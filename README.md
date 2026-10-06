# Toy Story disassembly

A static disassembly of the Mega Drive **Toy Story** (Traveller's Tales, 1995): a recursive-descent
trace, the engine's dispatch idioms, its text format, and the graphics format, with tools to unpack
the compressed art and read the sprites.

**This repository contains no game code or data.** You supply your own ROM; the traces hold
addresses and diff ranges only.

## Supported version

| Release | Size | SHA-1 | Used for |
|---|---|---|---|
| Toy Story (USA) | 4,194,304 | `49be571cd943fd594949c318a0bdbe6263fdd512` | `traces/trace_usa.json`, the names, the region map and the graphics |
| Toy Story (Europe) | 4,194,304 | `6e7bb9b191389973922a5ab9978205bb9d2664cc` | `traces/trace_eu_pal.json` and the dispatch idioms |
| USA + French patch | 4,194,304 | `12df4adf74a2d460c15130e17c6eeb6cac134fc1` | diff partner: the text |
| Europe + French patch | 4,194,304 | `f7237963d94ff25054a43fd01ab464ae5bbb477` (one character short in the notes: not recorded in full) | diff partner: the text |
| USA + Indonesian patch | 4,194,304 | `f0181d510065112f2e7e382d56652a69316d676a` | diff partner: the text |

The two are separate compiles, not a patch of each other: about 98% of the bytes differ, so
addresses do not carry over. Facts are recorded per revision and anchored by byte signature where
practical. The fan translations used for diffs are listed in `log/toystory_facts.py`.

## Building

```
python3 scripts/trace.py <rom> traces/trace_usa.json [<hex seed> ...]
python3 scripts/rnc.py <rom> list
python3 scripts/rnc.py <rom> extract <hex offset> out.bin
python3 scripts/frames.py <rom> <hex frame> <hex palette> out.png
```

The tracer takes extra manual seeds after the output file. Python 3 only; `trace.py` needs
`capstone`.

## What is here

| | |
|---|---|
| `log/toystory-notes.md` | the narrative: identity, dispatch idioms, coverage, text, graphics |
| `log/toystory_facts.py` | the structured facts, per revision, with a confidence per entry: identities, names (`NAMES_USA`), the region map (`REGIONS_USA`, `RNC_BLOCKS_USA`) |
| `traces/` | the USA and EU/PAL traces (addresses only: code, labels, data references) and the ROM-to-ROM diff ranges |
| `scripts/trace.py` | recursive-descent 68000 tracer |
| `scripts/rnc.py` | Rob Northen ProPack (RNC) decoder: list or extract the compressed blocks |
| `scripts/frames.py` | sprite frame decoder: pieces, or a PNG with a palette |
| `scripts/` (others) | listing, cross references, entropy map, ROM diffs, header, IPS/BPS |
| `scripts/progress.py` | the Progress block below |

## Progress

<!-- progress -->
```
CODE (USA ROM, traced)               135510 bytes, 33524 instructions
  traced code, of the ROM      3.2%  the rest is art, audio and data
  indirect calls unresolved       -  5, per-object pointers
  named routines               0.4%  2 of 448
  named RAM variables          0.0%  0 of 642 referenced
  traced code, EU/PAL ROM      3.3%  136874 bytes; 9 dispatch tables, 2 inline jumps
ROM MAP (USA ROM)                    268 regions: 266 HIGH, 2 MED, 0 LOW (incl. 264 RNC blocks)
  mapped, bytes               35.8%  HIGH and MED ranges
GRAPHICS (USA ROM)
  RNC blocks decoded         100.0%  264 of 264, 3314612 bytes unpacked
  sprite frames found             -  1218 object, 400 player
  object frames identified     5.9%  72 (Buzz Lightyear)
```
<!-- /progress -->

Updated on every commit by `scripts/hooks/pre-commit` from `scripts/progress.py` (enable once per
clone: `git config core.hooksPath scripts/hooks`).

## Engine

Three dispatch idioms carry most of the indirect flow, and the tracer resolves all three: a table of
`bra.w` instructions reached by a computed `jmp`/`jsr` (the largest, 38 entries at EU `$271E`, has
two callers), an unrolled copy or fill loop entered part way in, and a word-relative jump table
indexed by an object's state and event. Five calls remain unresolved: real per-object function
pointers loaded from a struct field at run time. The boot path has the standard Mega Drive region
check on `$A10001`. Details and addresses in the notes.

## Text

Plain 7-bit ASCII, uppercase, padded to fixed-width slots and bounded by quote marks: two fan
translations (French, Indonesian) swap readable ASCII in place. The two-word header before each
string and the lookup mechanism are not decoded yet.

## Graphics

The compressed art is Rob Northen ProPack (RNC): 264 blocks in the USA ROM, all of which decode
with a matching checksum. Sprites use a piece-list frame format; Woody's frames are run-length
coded, objects' are raw. Buzz Lightyear's frames, grouped by pose, and his palette are in
`GRAPHICS_USA`.

## See it in action

See what mods Pluto has helped me build from disassemblies like this one, with gameplay on real hardware:

- 📸 **Instagram:** [@consolesplayingconsoles](https://www.instagram.com/consolesplayingconsoles/)
- 🔗 **Everything else:** [beacons.ai/consolesplayingconsoles](https://beacons.ai/consolesplayingconsoles)

## Third-party sources

The French, Indonesian and Japanese patches studied here belong to their authors and are not
included; only diff ranges are. Toy Story and its owners' trademarks belong to them. This project
is not affiliated with or endorsed by them.

## Licence

© 2026 consolesplayingconsoles. Free software under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)): use it, study it, share it, modify it. Derivative works stay under the same licence, so what gets built on this stays open too.

This covers the tools and notes in this repo. It does not cover the original game, its ROM or its code, none of which are included.
