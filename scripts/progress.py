#!/usr/bin/env python3
"""progress.py: the disassembly's state, in several measures. Run from the repo root.

  traced     code the USA and EU/PAL traces reached (traces/), and the indirect calls
             still unresolved
  named      routines and RAM variables with a name (NAMES_USA) against the USA trace
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

regions = [(s, e, c) for s, e, _, c in f.REGIONS_USA] + [(s, e, 'HIGH') for s, e in f.RNC_BLOCKS_USA]
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


rows = [
    ('CODE (USA ROM, traced)', '', '%d bytes, %d instructions' % (usa['coverage_bytes'], usa['num_code_starts'])),
    ('  traced code, of the ROM', pct(usa['coverage_bytes'], usa['rom_size']), 'the rest is art, audio and data'),
    ('  indirect calls unresolved', '-', '%d, per-object pointers' % usa['num_unresolved_sites']),
    ('  named routines', pct(named_subs, len(subs)), '%d of %d' % (named_subs, len(subs))),
    ('  named RAM variables', pct(named_ram, len(ram)), '%d of %d referenced' % (named_ram, len(ram))),
    ('  traced code, EU/PAL ROM', pct(eu['coverage_bytes'], eu['rom_size']),
     '%d bytes; %d dispatch tables, %d inline jumps' % (eu['coverage_bytes'], len(f.DISPATCH_TABLES_EU_PAL),
                                                       len(f.INLINE_COMPUTED_JUMPS_EU_PAL))),
    ('ROM MAP (USA ROM)', '', '%d regions: %d HIGH, %d MED, %d LOW (incl. %d RNC blocks)'
     % (len(regions), conf['HIGH'], conf['MED'], conf['LOW'], len(f.RNC_BLOCKS_USA))),
    ('  mapped, bytes', pct(len(covered), usa['rom_size']), 'HIGH and MED ranges'),
    ('GRAPHICS (USA ROM)', '', ''),
    ('  RNC blocks decoded', pct(rnc['blocks_decoded'], rnc['blocks']),
     '%d of %d, %d bytes unpacked' % (rnc['blocks_decoded'], rnc['blocks'], rnc['unpacked_bytes'])),
    ('  sprite frames found', '-', '%d object, %d player' % (sprites['object_frames_found'], sprites['player_frames'])),
    ('  object frames identified', pct(buzz, sprites['object_frames_found']), '%d (Buzz Lightyear)' % buzz),
]
for label, p, rest in rows:
    print(('%-28s %6s  %s' % (label, p, rest)).rstrip())
