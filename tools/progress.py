#!/usr/bin/env python3
"""progress.py: the disassembly's state, in several measures. Run from the repo root.

  game code  subroutines named, unnamed and documented (named in a *.md), and RAM
             variables named (NAMES_USA) against the USA trace; code the USA and EU/PAL
             traces reached (traces/), and the indirect calls still unresolved
  mapped     REGIONS_USA and the RNC blocks by confidence, and the bytes they cover
  graphics   RNC blocks that decode, sprite frames found, character frames identified
Everything comes from tracked files (log/toystory_facts.py, traces/), so any clone gives
the same report.
"""
import json, sys

sys.path.insert(0, 'log')
import toystory_facts as f

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


import glob
docs = ''.join(open(p, encoding='utf-8').read() for p in sorted(glob.glob('*.md') + glob.glob('log/*.md')))
documented = sum(1 for a, n in f.NAMES_USA.items() if a in subs and n in docs)

# The shared layout (the Dreamcast decomps' too): the main metric first, the one that reads
# 100% when the project is complete; for a disassembly that is the ROM mapped (every byte known
# as code, art or data). Then the game code, and what this disassembly measures on its own.
rows = [
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
