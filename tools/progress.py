#!/usr/bin/env python3
"""progress.py: the disassembly's state, in several measures, the main one first. Run from the repo root.

  source     the main metric: bytes the source rebuilds identically as named, readable
             code and data (the rebuild record, see source_rows)
  game code  subroutines named, unnamed and documented (named in a *.md), and RAM
             variables named (NAMES_USA) against the USA trace; code the USA and EU/PAL
             traces reached (traces/), and the indirect calls still unresolved
  mapped     REGIONS_USA and the RNC blocks by confidence, and the bytes they cover
  graphics   RNC blocks that decode, sprite frames found, character frames identified
Everything comes from tracked files (log/toy_story_facts.py, traces/), so any clone gives
the same report.
"""
import json, sys

sys.path.insert(0, 'log')
import toy_story_facts as f

usa = json.load(open('traces/trace_usa.json'))
eu = json.load(open('traces/trace_eu_pal.json'))
g = f.GRAPHICS_USA

subs = {int(a, 16) for a, k in usa['labels'].items() if k == 'sub'}
ram = {int(a, 16) for a in usa['datarefs'] if int(a, 16) >= 0xFF0000}
named_subs = sum(1 for a in f.NAMES_USA if a in subs)
named_ram = sum(1 for a in f.NAMES_USA if a >= 0xFF0000)

regions = ([(s, e, c) for s, e, _, c in f.REGIONS_USA] + [(s, e, 'HIGH') for s, e in f.RNC_BLOCKS_USA]
           + [f.PLAYER_FRAMES_USA + ('HIGH',)] + [(s, e, 'MED') for s, e in f.OBJECT_FRAME_BLOCKS_USA])
conf = {'HIGH': 0, 'MED': 0, 'LOW': 0}
for _, _, c in regions:
    conf[c] += 1
covered = set()
for s, e, c in regions:
    if c != 'LOW':
        covered.update(range(s, e + 1))

buzz = sum(v[2] for k, v in g['buzz_frames'].items() if k != 'confidence')
sprites, rnc = g['sprite_frame'], g['compression']


def pct(a, b):
    return '%5.1f%%' % (100.0 * a / b) if b else '-'


# ── the main metric: equivalent source ──────────────────────────────────────────────────
# The disassembly is done when its source rebuilds the ROM byte for byte and every byte of it
# reads as source: code in named routines with symbolic operands (no raw ROM addresses, so the
# source can be edited and still build), data in named blocks of a decoded format. The rebuild
# tool records what it emitted in REBUILD (tracked: addresses, names and formats, no game bytes):
#   {"identical": bool, "blocks": [{"start", "end" (inclusive), "kind": "code"|"data", "name",
#    "symbolic": bool (code), "format": str (data; "raw" when not decoded)}]}
# A byte counts only when the whole rebuild is identical and its block is named and readable.
import re
AUTO = re.compile(r'^(sub|loc|off|ram|unk|byte|word|dword|tbl|ptr|jt|mode|vec|bad|bin|data)_[0-9A-Fa-f]+$')


def source_rows(path, rom_size, release):
    try:
        rb = json.load(open(path))
    except (OSError, ValueError):
        rb = None
    if not rb:
        return [('SOURCE (%s)' % release, '', 'no rebuild recorded yet (%s)' % path),
                ('  done: equivalent source', pct(0, rom_size), 'rebuilds byte-identical; named code with symbolic operands, named data in a decoded format'),
                ('  rebuilds byte-identical', '-', 'not recorded yet')]
    named = lambda b: bool(b.get('name')) and not AUTO.match(b['name'])
    size = lambda b: b['end'] - b['start'] + 1
    code = [b for b in rb['blocks'] if b['kind'] == 'code']
    data = [b for b in rb['blocks'] if b['kind'] == 'data']
    code_ok = sum(size(b) for b in code if named(b) and b.get('symbolic'))
    data_ok = sum(size(b) for b in data if named(b) and b.get('format', 'raw') != 'raw')
    done = code_ok + data_ok if rb.get('identical') else 0
    code_b, data_b = sum(size(b) for b in code), sum(size(b) for b in data)
    return [('SOURCE (%s)' % release, '', '%d blocks: %d code, %d data' % (len(rb['blocks']), len(code), len(data))),
            ('  done: equivalent source', pct(done, rom_size), 'rebuilds byte-identical; named code with symbolic operands, named data in a decoded format'),
            ('  rebuilds byte-identical', '-', 'yes' if rb.get('identical') else 'NO: nothing counts until it does'),
            ('  code as source', pct(code_ok, code_b), '%d of %d code bytes: named routine, symbolic operands' % (code_ok, code_b)),
            ('  data as source', pct(data_ok, data_b), '%d of %d data bytes: named block, decoded format' % (data_ok, data_b))]


import glob
docs = ''.join(open(p, encoding='utf-8').read() for p in sorted(glob.glob('*.md') + glob.glob('log/*.md')))
documented = sum(1 for a, n in f.NAMES_USA.items() if a in subs and n in docs)

# The shared layout (the Dreamcast decomps' too): the main metric first, the one that reads
# 100% when the project is complete (equivalent source, above). Then the ROM map, the game
# code, and what this disassembly measures on its own.
rows = source_rows('traces/rebuild_usa.json', usa['rom_size'], 'USA ROM') + [
    ('ROM MAP (USA ROM)', '', '%d regions: %d high, %d medium, %d low confidence (incl. %d RNC blocks, %d sprite frame runs)'
     % (len(regions), conf['HIGH'], conf['MED'], conf['LOW'], len(f.RNC_BLOCKS_USA), 1 + len(f.OBJECT_FRAME_BLOCKS_USA))),
    ('  mapped, bytes', pct(len(covered), usa['rom_size']), 'high and medium confidence ranges'),
    ('GAME CODE (USA ROM, traced)', '', '%d subroutines, %d bytes of code' % (len(subs), usa['coverage_bytes'])),
    ('  named', pct(named_subs, len(subs)), '%d of %d subroutines (NAMES_USA)' % (named_subs, len(subs))),
    ('  unnamed', pct(len(subs) - named_subs, len(subs)), '%d subroutines (sub_...)' % (len(subs) - named_subs)),
    ('  documented', pct(documented, len(subs)), '%d named subroutines in *.md' % documented),
    ('  named globals', '-', '%d of %d RAM variables referenced' % (named_ram, len(ram))),
    ('  traced code, of the ROM', pct(usa['coverage_bytes'], usa['rom_size']), 'the rest is art, audio and data'),
    ('  indirect calls unresolved', '-', '%d, per-object pointers' % usa['num_unresolved_sites']),
    ('  traced code, EU/PAL ROM', pct(eu['coverage_bytes'], eu['rom_size']),
     '%d bytes; %d dispatch tables, %d inline jumps' % (eu['coverage_bytes'], len(f.DISPATCH_TABLES_EU_PAL),
                                                       len(f.INLINE_COMPUTED_JUMPS_EU_PAL))),
    ('GRAPHICS (USA ROM)', '', ''),
    ('  RNC blocks decoded', pct(rnc['blocks_decoded'], rnc['blocks']),
     '%d of %d, %d bytes unpacked' % (rnc['blocks_decoded'], rnc['blocks'], rnc['unpacked_bytes'])),
    ('  sprite frames found', '-', '%d object, %d player' % (sprites['object_frames_found'], sprites['player_frames'])),
    ('  object frames identified', pct(buzz, sprites['object_frames_found']), '%d (Buzz Lightyear)' % buzz),
]
for label, p, rest in rows:
    print(('%-30s %6s  %s' % (label, p, rest)).rstrip())
