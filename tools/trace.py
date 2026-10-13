#!/usr/bin/env python3
"""
Recursive-descent 68000 tracer for Mega Drive/Genesis ROMs, seeded from the
CPU vector table plus any extra seed addresses given on the command line.

Usage: trace.py <rom> <out.json> [extra_seed_hex ...]

Re-runnable: pass hex addresses (no 0x prefix, e.g. 3CE12) as extra seeds
to grow coverage after manually identifying a dispatch table or handler.

Besides coverage and edges, the output has `labels` (every call target 'sub',
every other branch target 'loc') and `datarefs` (each absolute or pc-relative
data address an instruction names, with the instructions that name it), the
same shape as the smd-disassembly skill's tracer, so names and RAM variables
can be counted against it.
"""
import sys, json, re
import capstone as cs

ABSL = re.compile(r'\$([0-9a-f]+)\.l\b')             # $a10008.l  absolute long
ABSW = re.compile(r'\$([0-9a-f]+)\.w\b')             # $e6a4.w    absolute short (sign-extended)
PCR  = re.compile(r'\$([0-9a-f]+)\(pc\)')            # $294(pc)   pc-relative


def data_refs(insn):
    """Data addresses an instruction names (not its branch target)."""
    if insn.mnemonic.split('.')[0] in ('jmp', 'jsr', 'bsr', 'bra') or insn.mnemonic.startswith(('b', 'db')):
        return []
    ops, out = insn.op_str, []
    out += [int(m.group(1), 16) for m in ABSL.finditer(ops)]
    out += [(lambda v: (0xFF0000 | v) if v >= 0x8000 else v)(int(m.group(1), 16)) for m in ABSW.finditer(ops)]
    out += [int(m.group(1), 16) for m in PCR.finditer(ops)]
    return out

VECTOR_NAMES = {
    0: 'initial_ssp', 1: 'reset_pc', 2: 'bus_error', 3: 'address_error',
    4: 'illegal_instr', 5: 'zero_divide', 6: 'chk', 7: 'trapv',
    8: 'privilege_violation', 9: 'trace', 10: 'line_1010', 11: 'line_1111',
    15: 'uninitialized_interrupt', 24: 'spurious_interrupt',
    25: 'irq1', 26: 'irq2', 27: 'irq3', 28: 'irq4_hblank', 29: 'irq5',
    30: 'irq6_vblank', 31: 'irq7',
}
for i in range(16):
    VECTOR_NAMES[32 + i] = f'trap_{i}'

BRANCH_MNEM = {
    'bra', 'beq', 'bne', 'bcc', 'bcs', 'bge', 'blt', 'bgt', 'ble',
    'bhi', 'bls', 'bpl', 'bmi', 'bvc', 'bvs', 'bhs', 'blo',
}
DBCC_MNEM = {m for m in (
    'dbt', 'dbf', 'dbra', 'dbeq', 'dbne', 'dbcc', 'dbcs', 'dbge', 'dblt',
    'dbgt', 'dble', 'dbhi', 'dbls', 'dbpl', 'dbmi', 'dbvc', 'dbvs',
)}
CALL_MNEM = {'bsr', 'jsr'}
JUMP_MNEM = {'jmp'}
RETURN_MNEM = {'rts', 'rte', 'rtr'}
NOFLOW_MNEM = {'illegal', 'trap'}

ADDR_RE = re.compile(r'\$([0-9A-Fa-f]+)')


def load_rom(path):
    with open(path, 'rb') as f:
        return f.read()


def get_seeds(rom):
    seeds = {}
    for idx in range(256):
        off = idx * 4
        if off + 4 > len(rom):
            break
        val = int.from_bytes(rom[off:off + 4], 'big')
        if val == 0 or val >= len(rom) or val & 1:
            continue
        if idx == 0:
            continue  # initial SSP, not code
        name = VECTOR_NAMES.get(idx, f'vector_{idx}')
        seeds[val] = name
    return seeds


def classify(insn):
    """Return (kind, targets:list[int], indexed_base:int|None, is_indexed:bool)"""
    m = insn.mnemonic.split('.')[0]
    op = insn.op_str
    has_reg_index = bool(re.search(r',\s*[ad]\d\.[wl]\)', op)) or \
        bool(re.search(r'\(a\d\)', op)) or bool(re.search(r'\(a\d,', op))
    addrs = [int(a, 16) for a in ADDR_RE.findall(op)]

    if m in RETURN_MNEM or m in NOFLOW_MNEM:
        return ('stop', [], None, False)
    if m in CALL_MNEM:
        if has_reg_index or not addrs:
            return ('call_indirect', [], addrs[0] if addrs else None, has_reg_index)
        return ('call', [addrs[0]], None, False)
    if m in JUMP_MNEM:
        if has_reg_index or not addrs:
            return ('jump_indirect', [], addrs[0] if addrs else None, has_reg_index)
        return ('jump', [addrs[0]], None, False)
    if m in BRANCH_MNEM:
        if not addrs:
            return ('jump_indirect', [], None, False)
        if m == 'bra':
            return ('jump', [addrs[0]], None, False)
        return ('branch', [addrs[0]], None, False)
    if m in DBCC_MNEM:
        if not addrs:
            return ('jump_indirect', [], None, False)
        return ('branch', [addrs[0]], None, False)
    return ('normal', [], None, False)


def read_u16(rom, off):
    if off + 2 > len(rom):
        return None
    return int.from_bytes(rom[off:off + 2], 'big')


def resolve_dispatch_base(rom, base, max_entries=256):
    """
    Idiom A: 'BRA.W trampoline table' - table of 4-byte entries, each a
    literal BRA.W instruction (opcode 0x6000 + signed word displacement).
    Detected when the first table word is exactly 0x6000.
    Returns ('trampoline', [target_addr, ...]) or None if not this idiom.
    """
    if base is None or base < 0 or base + 4 > len(rom):
        return None
    w0 = read_u16(rom, base)
    if w0 != 0x6000:
        return None
    targets = []
    pos = base
    for _ in range(max_entries):
        op = read_u16(rom, pos)
        if op != 0x6000:
            break
        disp = read_u16(rom, pos + 2)
        if disp is None:
            break
        if disp & 0x8000:
            disp -= 0x10000
        target = (pos + 2 + disp) & 0xFFFFFFFF
        if target >= len(rom):
            break
        targets.append(target)
        pos += 4
    if len(targets) < 2:
        return None
    return ('trampoline', targets, pos)


REG_RE = re.compile(r'\b([ad][0-7])\b')


def find_reg_in_paren(op_str):
    """Extract the base address register used in '(a0)' / '(a0, d1.w)'."""
    m = re.match(r'\((a[0-7])(?:,\s*[ad][0-7]\.[wl])?\)', op_str)
    return m.group(1) if m else None


def find_lea_base(history, reg):
    for addr, mnem, op in reversed(history):
        if mnem.split('.')[0] == 'lea':
            mm = re.match(r'\$([0-9a-fA-F]+)\.[lw],\s*' + re.escape(reg) + r'$', op)
            if mm:
                return int(mm.group(1), 16)
    return None


def resolve_word_table(rom, history, reg, base, max_cap=256):
    """
    Idiom C: 'LEA table,An ; ADDA.W (An,Dx.W),An ; JMP/JSR (An)'.
    Table entries are signed 16-bit displacements *relative to the table
    base itself* (not to the entry). Bound the entry count using the
    nearest ANDI.W masks feeding the index, when found.
    Caller must already have ruled out the trampoline-table idiom for base.
    """
    if base is None or base + 2 > len(rom):
        return None

    masks = []
    for addr, mnem, op in reversed(history):
        full = f"{mnem} {op}"
        mm = re.match(r"andi\.w #\$([0-9a-fA-F]+), [ad][0-7]", full)
        if mm:
            masks.append(int(mm.group(1), 16))
        if len(masks) >= 2:
            break
    if masks:
        max_index = 0
        for mval in masks:
            max_index |= mval
        entry_count_cap = min(max_cap, max_index // 2 + 2)
    else:
        entry_count_cap = max_cap

    targets = []
    pos = base
    for _ in range(entry_count_cap):
        w = read_u16(rom, pos)
        if w is None:
            break
        if w & 0x8000:
            disp = w - 0x10000
        else:
            disp = w
        target = base + disp
        if target < 0 or target >= len(rom):
            break
        targets.append(target)
        pos += 2
    if len(targets) < 2:
        return None
    return base, targets, entry_count_cap


def trace(rom, seeds):
    md = cs.Cs(cs.CS_ARCH_M68K, cs.CS_MODE_M68K_000 + cs.CS_MODE_BIG_ENDIAN)
    md.detail = False
    n = len(rom)
    covered = bytearray(n)  # 0=unknown,1=code
    code_starts = set()
    queue = list(seeds.keys())
    origin = dict(seeds)
    unresolved = {}  # shape -> list of {addr, mnemonic, op_str, base}
    edges_call = []
    edges_jump = []
    bad_decodes = []
    idiom_hits = []
    datarefs = {}

    while queue:
        addr = queue.pop()
        if addr is None or addr < 0 or addr >= n or addr & 1:
            continue
        if addr in code_starts:
            continue
        cur = addr
        history = []
        while True:
            if cur >= n or cur & 1:
                break
            if cur in code_starts:
                break  # merged into already-traced code
            chunk = bytes(rom[cur:cur + 10])
            got = list(md.disasm(chunk, cur))
            if not got:
                bad_decodes.append(cur)
                break
            insn = got[0]
            size = insn.size
            # overlap check against already-covered bytes from a *different* start
            if any(covered[cur:cur + size]) and cur not in code_starts:
                # ambiguous overlap; stop this thread, don't corrupt existing map
                break
            for i in range(cur, min(cur + size, n)):
                covered[i] = 1
            code_starts.add(cur)
            history.append((cur, insn.mnemonic, insn.op_str))
            for a in data_refs(insn):
                datarefs.setdefault(a, set()).add(cur)
            if len(history) > 16:
                history.pop(0)

            kind, targets, base, is_idx = classify(insn)
            if kind == 'call':
                edges_call.append((cur, targets[0]))
                queue.append(targets[0])
                cur = cur + size
                continue
            if kind == 'branch':
                edges_jump.append((cur, targets[0]))
                queue.append(targets[0])
                cur = cur + size
                continue
            if kind == 'jump':
                edges_jump.append((cur, targets[0]))
                queue.append(targets[0])
                break
            if kind == 'stop':
                break
            if kind in ('jump_indirect', 'call_indirect'):
                resolved = resolve_dispatch_base(rom, base) if base is not None else None
                if resolved:
                    _, targets, table_end = resolved
                    idiom_hits.append({
                        'site': cur, 'kind': kind, 'idiom': 'trampoline_table',
                        'base': base, 'num_entries': len(targets), 'table_end': table_end,
                    })
                    for t in targets:
                        queue.append(t)
                        (edges_call if kind == 'call_indirect' else edges_jump).append((cur, t))
                elif base is not None:
                    # Idiom B: computed jump lands directly on inline code
                    # (duff's-device style unrolled loop), not a data table.
                    idiom_hits.append({
                        'site': cur, 'kind': kind, 'idiom': 'inline_computed_jump',
                        'base': base,
                    })
                    queue.append(base)
                    (edges_call if kind == 'call_indirect' else edges_jump).append((cur, base))
                else:
                    reg = find_reg_in_paren(insn.op_str)
                    lea_base = find_lea_base(history, reg) if reg else None
                    trampoline = resolve_dispatch_base(rom, lea_base) if lea_base is not None else None
                    word_table = None
                    if trampoline:
                        _, tt_targets, tt_end = trampoline
                        idiom_hits.append({
                            'site': cur, 'kind': kind, 'idiom': 'trampoline_table_via_reg',
                            'base': lea_base, 'num_entries': len(tt_targets), 'table_end': tt_end,
                        })
                        for t in tt_targets:
                            queue.append(t)
                            (edges_call if kind == 'call_indirect' else edges_jump).append((cur, t))
                    elif lea_base is not None:
                        word_table = resolve_word_table(rom, history, reg, lea_base)
                    if trampoline:
                        pass  # already queued above
                    elif word_table:
                        wt_base, wt_targets, cap = word_table
                        idiom_hits.append({
                            'site': cur, 'kind': kind, 'idiom': 'word_relative_table',
                            'base': wt_base, 'num_entries': len(wt_targets), 'cap': cap,
                        })
                        for t in wt_targets:
                            queue.append(t)
                            (edges_call if kind == 'call_indirect' else edges_jump).append((cur, t))
                    else:
                        shape = f"{insn.mnemonic} :: {re.sub(r'[ad][0-7]', 'Dn', insn.op_str)}"
                        unresolved.setdefault(shape, []).append({
                            'addr': cur, 'mnemonic': insn.mnemonic,
                            'op_str': insn.op_str, 'base': base,
                        })
                if kind == 'call_indirect':
                    cur = cur + size
                    continue
                break
            cur = cur + size

    coverage_bytes = sum(covered)
    # merge contiguous code ranges
    ranges = []
    start = None
    for i in range(n + 1):
        is_code = i < n and covered[i]
        if is_code and start is None:
            start = i
        elif not is_code and start is not None:
            ranges.append([start, i])
            start = None

    labels = {t: 'loc' for _, t in edges_jump}
    labels.update({t: 'sub' for _, t in edges_call})
    return {
        'labels': {'%06X' % a: k for a, k in sorted(labels.items()) if 0 <= a < n},
        'datarefs': {'%06X' % a: sorted('%06X' % x for x in v) for a, v in sorted(datarefs.items())},
        'rom_size': n,
        'seeds': {hex(k): v for k, v in seeds.items()},
        'coverage_bytes': coverage_bytes,
        'coverage_pct': round(100.0 * coverage_bytes / n, 4),
        'num_code_starts': len(code_starts),
        'code_ranges': ranges,
        'unresolved_shapes': {k: {'count': len(v), 'examples': v[:8]} for k, v in unresolved.items()},
        'num_unresolved_sites': sum(len(v) for v in unresolved.values()),
        'edges_call': edges_call,
        'edges_jump': edges_jump,
        'idiom_hits': idiom_hits,
        'bad_decodes_sample': bad_decodes[:50],
        'num_bad_decodes': len(bad_decodes),
    }


if __name__ == '__main__':
    rom_path, out_path = sys.argv[1], sys.argv[2]
    extra_seeds = [int(a, 16) for a in sys.argv[3:]]
    rom = load_rom(rom_path)
    seeds = get_seeds(rom)
    for a in extra_seeds:
        seeds[a] = 'manual_seed'
    result = trace(rom, seeds)
    with open(out_path, 'w') as f:
        json.dump(result, f)
    print(f"coverage: {result['coverage_pct']}% ({result['coverage_bytes']}/{result['rom_size']} bytes), "
          f"{result['num_code_starts']} instrs, "
          f"{result['num_unresolved_sites']} unresolved sites in {len(result['unresolved_shapes'])} shapes, "
          f"{result['num_bad_decodes']} bad decodes")
    print("Top unresolved shapes:")
    shapes = sorted(result['unresolved_shapes'].items(), key=lambda kv: -kv[1]['count'])
    for shape, info in shapes[:15]:
        print(f"  [{info['count']:4d}]  {shape}")
