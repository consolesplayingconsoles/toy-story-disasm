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
           + [f.PLAYER_FRAMES_USA + ('HIGH',)] + [(s, e, 'MED') for s, e in f.OBJECT_FRAME_BLOCKS_USA]
           + [(s, e, 'HIGH') for s, e, _, _ in f.BLOCKS_USA])            # checked whole
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
# A byte counts only when the whole rebuild is identical and its block is named and readable: code
# symbolic; data a leaf asset kept as a binary file in a decoded format (LEAF), or written by the
# rebuild as source ("source": true). Structured data (tables, mappings, frame layouts, scripts,
# text) counts only as source.
import re
LEAF = {'tiles', 'rle_tiles', 'compressed_tiles', 'rnc', 'lzss', 'lzss_frames', 'nemesis', 'kosinski', 'palette',
        'samples', 'pcm', 'fill'}


def readable(b):
    return bool(b.get('source')) or b.get('format', 'raw') in LEAF


AUTO = re.compile(r'^(sub|loc|off|ram|unk|byte|word|dword|tbl|ptr|jt|mode|vec|bad|bin|data|code)_[0-9A-Fa-f]+$')


def source_rows(path, rom_size, release):
    try:
        rb = json.load(open(path))
    except (OSError, ValueError):
        rb = None
    if not rb:
        return [('SOURCE (%s)' % release, '', 'no rebuild recorded yet (%s)' % path),
                ('  done: equivalent source', pct(0, rom_size), 'rebuilds byte-identical; named code with every label and operand named; named leaf assets, structured data as source'),
                ('  rebuilds byte-identical', '-', 'not recorded yet')]
    named = lambda b: bool(b.get('name')) and not AUTO.match(b['name'])
    size = lambda b: b['end'] - b['start'] + 1
    code = [b for b in rb['blocks'] if b['kind'] == 'code']
    data = [b for b in rb['blocks'] if b['kind'] == 'data']
    code_ok = sum(size(b) for b in code if named(b) and b.get('symbolic')
                  and b.get('named_labels', 0) == b.get('labels', 0))
    data_ok = sum(size(b) for b in data if named(b) and readable(b))
    recog_blocks = [b for b in data if b.get('format', '').startswith('recognised_')]
    recog, recog_n = sum(size(b) for b in recog_blocks), len(recog_blocks)
    inner = sum(b.get('labels', 0) for b in code)
    inner_named = sum(b.get('named_labels', 0) for b in code)
    flds = sum(b.get('fields', 0) for b in code)
    flds_named = sum(b.get('named_fields', 0) for b in code)
    done = code_ok + data_ok if rb.get('identical') else 0
    code_b, data_b = sum(size(b) for b in code), sum(size(b) for b in data)
    return [('SOURCE (%s)' % release, '', '%d blocks: %d code, %d data' % (len(rb['blocks']), len(code), len(data))),
            ('  done: equivalent source', pct(done, rom_size), 'rebuilds byte-identical; named code with every label and operand named; named leaf assets, structured data as source'),
            ('  rebuilds byte-identical', '-', 'yes' if rb.get('identical') else 'NO: nothing counts until it does'),
            ('  code as source', pct(code_ok, code_b), '%d of %d code bytes: named routine, labels and operands (addresses, struct fields) named' % (code_ok, code_b)),
            ('  data as source', pct(data_ok, data_b), '%d of %d data bytes: named leaf asset, or written as source' % (data_ok, data_b)),
            ('  recognised, not counted', pct(recog, rom_size), '%d bytes, %d blocks: a known format or program, content not yet identified or not yet written as source; not in the figures above' % (recog, recog_n)),
            ('  local labels named', pct(inner_named, inner), '%d of %d labels inside routines' % (inner_named, inner)),
            ('  struct fields named', pct(flds_named, flds), '%d of %d displacements off an address register' % (flds_named, flds)),
            ('  named constants', '-', 'not required: an ID and a count look alike')]


import glob
docs = ''.join(open(p, encoding='utf-8').read() for p in sorted(glob.glob('*.md') + glob.glob('log/*.md')))
documented = sum(1 for a, n in f.NAMES_USA.items() if a in subs and n in docs)

# The shared layout (the Dreamcast decomps' too): the main metric first, the one that reads
# 100% when the project is complete (equivalent source, above). Then the ROM map, the game
# code, and what this disassembly measures on its own.
rows = source_rows('traces/rebuild_usa.json', usa['rom_size'], 'USA ROM') + [
    ('ROM MAP (USA ROM)', '', '%d regions: %d high, %d medium, %d low confidence (incl. %d RNC blocks, %d sprite frame runs)'
     % (len(regions), conf['HIGH'], conf['MED'], conf['LOW'], len(f.RNC_BLOCKS_USA), 1 + len(f.OBJECT_FRAME_BLOCKS_USA))),
    ('  mapped, bytes', pct(len(covered), usa['rom_size']), 'high and medium confidence ranges, and the data blocks'),
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
def write_badge(rows, label, path='badge.svg'):
    """badge.svg beside the README: the label, a bar filled to the main metric ("done: ...") and its percentage, in
    Pluto's colours. One metric only; the number is always printed, so colour carries no meaning on its own."""
    done = 0.0
    for n, p, _ in rows:
        if n.strip().startswith('done:'):
            try:
                done = float(p.strip().rstrip('%'))
            except ValueError:
                done = 0.0
            break
    bar = 64
    wd = int(round(bar * min(done, 100.0) / 100.0))
    if done > 0 and wd < 2:
        wd = 2
    text = '%.1f%%' % done
    title = '%s: %s done' % (label, text)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="182" height="20" role="img" aria-label="%s">'
           '<title>%s</title><clipPath id="r"><rect width="182" height="20" rx="3"/></clipPath>'
           '<g clip-path="url(#r)"><rect width="52" height="20" fill="#1a2233"/><rect x="52" width="130" height="20" fill="#2a3347"/>'
           '<rect x="60" y="6" width="%d" height="8" rx="2" fill="#ecc9b9"/>'
           '<rect x="60" y="6" width="%d" height="8" rx="2" fill="#c87053"/></g>'
           '<g fill="#fff" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11" text-anchor="middle">'
           '<text x="26" y="14">%s</text><text x="154" y="14">%s</text></g></svg>\n'
           % (title, title, bar, wd, label, text))
    try:
        open(path, 'w').write(svg)
    except OSError:
        pass
    # the README's badge link carries the number (badge.svg?p=40.3): a new number is a new address, so GitHub's image cache
    # never shows an old badge
    try:
        readme = open('README.md').read()
        fresh = re.sub(r'\(badge\.svg(\?p=[0-9.]*)?\)', '(badge.svg?p=%.1f)' % done, readme, count=1)
        if fresh != readme:
            open('README.md', 'w').write(fresh)
    except (IOError, OSError):
        pass


write_badge(rows, 'disasm')
for label, p, rest in rows:
    print(('%-30s %6s  %s' % (label, p, rest)).rstrip())
