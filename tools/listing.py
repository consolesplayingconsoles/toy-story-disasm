#!/usr/bin/env python3
"""Dump a correctly-aligned disassembly window using known code_ranges from a trace."""
import sys, json
import capstone as cs

def load(rom_path, trace_path):
    with open(rom_path, 'rb') as f:
        rom = f.read()
    with open(trace_path) as f:
        tr = json.load(f)
    return rom, tr['code_ranges']

def enclosing_range(ranges, addr):
    for s, e in ranges:
        if s <= addr < e:
            return s, e
    return None

def show(rom, ranges, addr, before_instrs=20, after_instrs=6):
    md = cs.Cs(cs.CS_ARCH_M68K, cs.CS_MODE_M68K_000 + cs.CS_MODE_BIG_ENDIAN)
    rng = enclosing_range(ranges, addr)
    if not rng:
        print(f"0x{addr:X}: not in any known code range")
        return
    s, e = rng
    insns = list(md.disasm(rom[s:e + 8], s))
    idx = next((i for i, ins in enumerate(insns) if ins.address == addr), None)
    lo = max(0, (idx or 0) - before_instrs)
    hi = min(len(insns), (idx or 0) + after_instrs + 1)
    for ins in insns[lo:hi]:
        marker = '>>' if ins.address == addr else '  '
        print(f" {marker} {ins.address:06X}: {ins.mnemonic:<10s} {ins.op_str}")

if __name__ == '__main__':
    rom_path, trace_path = sys.argv[1], sys.argv[2]
    rom, ranges = load(rom_path, trace_path)
    for a in sys.argv[3:]:
        addr = int(a, 16)
        print(f"=== 0x{addr:X} ===")
        show(rom, ranges, addr)
        print()
