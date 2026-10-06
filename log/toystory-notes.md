# Toy Story (Mega Drive) — disassembly log

Traveller's Tales, published by Disney Interactive / Sega, 1995-96. Platformer,
4MB ROM (32-bit Mega Drive mapper, no bank switching, straight linear map).

## Session note: skill scripts were not synced

The `smd-disassembly` skill's `SKILL.md` came through, but its `scripts/`,
`references/`, and `log/` directories did not — only the procedure text was
available, none of the actual tooling (`trace.py`, `mapdump.py`, `xref.py`,
`ips.py`, etc.) or the prior idiom catalogue (`references/idioms.md`). Everything
under `scripts/` in this deliverable was rebuilt from scratch against
`capstone`'s M68K backend, following the procedure described in the skill text.
Because none of the prior idiom catalogue was available either, every dispatch
shape below was rediscovered from this ROM directly rather than looked up.

## Source-file problems found before analysis started

Two of the files the operator pointed at were not what their names claimed:

* `Toy Story (Europe).zip` originally contained a **Game Boy** ROM (`.gb`,
  512KB) — not a Mega Drive ROM at all. The operator replaced it mid-session
  with the correct file (`Toy Story (Europe).gen`, 4MB, MD header, checksum
  verifies). All EU/PAL findings below are against the replacement file.
* `Toy Story (JP).ips` is not an IPS patch — it's a saved GitHub HTML page
  (a `/blob/` view, not a `raw` download) for
  `github.com/luxbiter/Toy-Story-MD-JP-`. GitHub access wasn't available from
  this session to re-fetch the real raw file, so the JP release was **not**
  analysed this pass. Re-download the actual `.ips` from that repo's `raw`
  URL and re-run the diff step to add it.

## Identity

Five buildable variants, all Sega checksum-valid except the Indonesian one
(that IPS patch doesn't recompute the header checksum field — cosmetic,
doesn't affect play on real hardware/most emulators since Genesis games don't
self-check at runtime the way Game Gear/32X sometimes do):

| build | source | sha1 | checksum_ok |
|---|---|---|---|
| USA (v?, Oct 1995) | `Toy Story (USA).zip` → `.gen`, 4194304 bytes | `49be571c...fdd512` | yes |
| EU/PAL (rev, Feb 1996) | `Toy Story (Europe).zip` → `.gen`, 4194304 bytes | `6e7bb9b1...d2664cc` | yes |
| FR (US-base) | US + `Toy Story (FR-US).bps` | `12df4adf...134fc1` | yes |
| FR (PAL-base) | EU + `Toy Story (FR-PAL).bps` | `f7237963...5bbb477` | yes |
| Indonesian | US + `Toy Story (Indo).ips` | `f0181d51...9316d676` | **no** (patch doesn't fix checksum) |

USA header says `SEGA GENESIS`, EU header says `SEGA MEGA DRIVE` — cosmetic
per-region string, not a functional difference.

**EU/PAL is not a byte-shifted re-release of USA** — diffing them shows
~98% of the ROM differs (4.11MB of 4.19MB). This matches the French
translator's readme, which describes real gameplay differences between the
two builds: USA runs at 30fps with no password system (continue only), PAL
runs at 25fps with a password system every 4 levels and a free continue.
That's consistent with a genuine second compile, four months later, not a
patch — don't expect addresses to transfer between the two builds. Anchor
findings by signature, not offset, exactly as the skill warns.

## Dispatch idioms found in this engine

None of these were in the (missing) idiom catalogue; all three were
identified from this ROM's own unresolved trace sites. Shown as PC-relative
`JMP`/`JSR`, but idiom A appears both in the direct PC-relative form and via
a register pre-loaded through `LEA` (see A-via-reg below).

### Idiom A — BRA.W trampoline table

```
<index computed in D0, doubled once per table entry (x4 for this idiom)>
jmp   table(pc,d0.w)        ; or jsr, for a call table
table:
  bra.w  handler_0
  bra.w  handler_1
  ...
```

Each table entry is a **literal 4-byte `BRA.W` instruction** (`0x6000` +
signed word displacement), not a raw address. Detect by checking whether the
first table word is exactly `0x6000`; decode entries as `bra.w` and resolve
`target = entry_addr + 2 + sign16(disp)`. Table length isn't stored anywhere
explicit — read forward while the word `0x6000` keeps recurring at the
4-byte stride; stop at the first entry that isn't `0x6000,disp`.

Confirmed table at (EU/PAL) `0x271E`: 38 entries, reached from *two*
different call sites — one direct PC-relative `JSR $271E(pc,d4.w)` at
`0x26C4`, and one via `LEA $271E.w,A1 ; JSR (A1,D4.W)` at `0x284E` (the
"A-via-reg" variant of the same idiom, same table). This is the largest
dispatch table found and looks like a shared command/event-type table used
by more than one caller — worth prioritising if resuming this analysis.

Other confirmed instances (EU/PAL addresses): `0x4D38` (jsr table),
`0xB178` (31-entry jmp table), `0x1033A` (17-entry jmp table), `0x4ECE`
(11-entry jmp table), `0x1381A`(20174, 11-entry jmp table), `0x4D48`(19768,
11-entry jmp table), `0x1027C`(66248, 17-entry call table).

### Idiom B — inline computed jump ("duff's device")

```
<index in D0, doubled once (x2)>
jmp   base(pc,d0.w)
base:
  move.l (a0)+,(a2)+     ; or move.l Dn,(a2)+, etc.
  move.l (a0)+,(a2)+
  ...                    ; repeated N times, unrolled
  rts                    ; (or falls into the routine's tail)
```

Looks identical to idiom A at the call site (computed `JMP base(pc,Dn.w)`)
but `base` is **not a table — it's code**: an unrolled block-copy/fill loop.
Jumping partway in skips the first *k* iterations, a classic 68000
"jump into a repeated instruction stream" trick for a variable-length
copy/fill in fixed time-per-iteration. Distinguish from idiom A by checking
whether the first word at `base` decodes as a plausible instruction
opcode (specifically: is it `0x6000`? if not, it's not the trampoline
idiom) — if it's ordinary code, just treat `base` as a normal branch target
and let linear decode continue through it.

Confirmed instances (EU/PAL): `0x1382`→`0x138A` (`move.l (a0)+,(a2)+` block
copy), `0x12F8`→`0x12FE` (`move.l d7,(a1)+` block fill — D7 is very likely
pre-loaded with a fill word/pattern by the caller).

### Idiom C — word-relative jump table

```
lea.l   table.l,a0
<index computed in Dn, already at the right byte stride for the table>
adda.w  (a0,dn.w),a0
jmp     (a0)                ; or jsr
table:
  dc.w  disp_0, disp_1, ...   ; signed 16-bit, relative to `table` itself
```

The classic byte/word switch-table idiom — table entries are **signed word
displacements from the table's own base**, not from the entry or from PC.
`target = table_base + sign16(word_at(table_base + index))`. Table length
isn't stored explicitly; bound it using the `ANDI.W #mask,Dn` instructions
that built the index (OR the masks together, divide by entry stride) rather
than scanning blind — the two confirmed instances both mask a two-part
index (`event-group` in the high bits, `sub-state` in the low bits) OR'd
together before use, consistent with a per-object "state × event" behaviour
table, ~120 entries each.

Confirmed instances (EU/PAL): call table at `0x42618` (reached from
`0x42614`), and an identical-shape table at `0x424F8` (reached from
`0x424F4`) — same handler pattern reused for (at least) two different
entity/object classes.

### Unresolved: true per-object function pointers

5 sites remain genuinely unresolved — `JSR (An)` / `JSR (An,Dn.w)` where the
address register is loaded from an **object/struct field** at runtime
(e.g. `movea.l d6,a4 ; jsr (a4)` at `0x7ADCE`, or `jsr (a4,d1.w)` at
`0x7859E` reached through a sprite-metrics lookup). These are real
per-instance behaviour/vtable pointers, not statically resolvable from code
alone — would need either a runtime trace (emulator with tracing) or a
data-flow pass tracking what values get written into that struct field
across the whole ROM. Left open; see the 5 sites logged in `trace4.json`'s
`unresolved_shapes`.

## Coverage

First pass (vector table seeds only, no idiom resolution): **1.85%**
(19083 instructions). After teaching idioms A/B/C: **3.26%**
(33836 instructions), unresolved sites down from 16 (10 distinct shapes) to
5 (2 shapes, both the genuine per-object vtable case above).

Entropy map (256-byte blocks) shows two clusters that explain why coverage
plateaus well under 100%:

* H in [6,7) ∪ [7,8): 34% of the ROM, essentially 0% code-covered → almost
  certainly compressed graphics/audio payload.
* H in [3,5): 45% of the ROM, only ~5% code-covered so far → most likely
  uncompressed level/tilemap/object-placement data and the text blob (see
  below), not missed code — this game's data doesn't compress to the high
  end of the entropy range the way 4bpp tile art typically does, so don't
  assume "mid-entropy = definitely code" the way the reference game allowed.

Chasing coverage further from here would mean resolving the 5 true
per-object dispatch sites (highest leverage — likely unlocks all the
entity-behaviour code at once, the same way idiom A's 38-entry table did),
not more idiom-teaching.

## Text

**Plain 7-bit ASCII, uppercase, no custom glyph table.** This was the
easiest possible outcome of the "solve the encoding" step — confirmed by
diffing against three independent translations (French, Indonesian) which
all show literal readable text swapped in place:

```
USA:    "O.K. EVERYONE... TODAY IS ANDY'S  BIRTHDAY AND WE  NEED TO FIND..."
FR-US:  "BONJOUR A TOUS. AUJOURD'HUI C'EST L'ANNIVERSAIRE D'ANDY. ON DOIT..."
```

Cutscene/hint script sits in a contiguous region, USA-based coordinates
`0x1AC91`–`0x27528` (~44.6KB span), EU/PAL coordinates shifted to start
around `0x1AE05` (expected — see the "not byte-shifted" note above). Within
that span, only 134 distinct byte-regions actually change between languages
(~12.5KB of real character data) — the rest is shared framing/padding, which
means strings live in **fixed-size slots** and translators pad/truncate to
fit rather than the engine supporting variable-length strings. Confirmed
independently by both the French BPS patches (143 diff regions against each
base) and the Indonesian IPS patch (149 diff regions) landing on the same
span.

Each string is `"`-delimited in ROM (literal ASCII quote marks bound each
line of dialogue) and preceded by what looks like a small binary header
(seen: `00 01 D7 00 00 00 00 00 00 3C C1 60 00 01 D8` before the first
string) — **not yet decoded**. Didn't find a pointer table referencing the
string region via absolute long or absolute short addressing in the time
available (searched for the 4-byte and 3-byte big-endian forms of
`0x1AC91`, no hits — the lookup mechanism is presumably PC-relative or
goes through the 2-byte header field, not a literal pointer table). This is
the natural next step if resuming: figure out what the two 16-bit header
fields (`0x01D7`, `0x01D8` in the first record) encode — likely a
string-id/length pair or a pair of pointers into a second, smaller index
table.

The French readme also states graphics were not translatable ("couldn't
decompress the graphics") — consistent with the high-entropy 34% of the ROM
being compressed art the translators also bounced off.

## Update: the real JP patch is not a translation

The operator's first `Toy Story (JP).ips` was a saved GitHub HTML page (see
above); the real file has since been supplied and applied cleanly
(sha1 `6a37e528...898d6`, checksum verifies). It's tiny — 3 IPS records,
26 bytes total — and turns out to be a **region-compatibility patch**, not
a Japanese script translation, despite the source repo's name
(`Toy-Story-MD-JP-`):

1. `0x18E` (2 bytes): recomputed header checksum field (expected, any patch
   touching code needs this).
2. `0x20975` (1 byte): `0x80` → `0x00`. This is the trailing immediate byte
   of `CMPI.B #$80,D0` inside the game's hardware-region-check routine —
   see `REGION_CHECK_USA` in `toystory_facts.py`. The routine reads the
   Genesis version register at `$A10001` (bit7 = domestic/overseas, bit6 =
   NTSC/PAL), masks to those two bits, and compares against `$80`
   (overseas+NTSC = USA). The patch changes the target to `$00`
   (domestic+NTSC = **Japan**) — it re-gates the boot check from "must be a
   USA console" to "must be a Japanese console". This is a textbook Genesis
   region-check idiom, worth checking for in any other MD game — the
   masked signature is in the facts module.
3. `0x21E6A` (23 bytes): rewrites the boot disclaimer string from
   `"NTSC GENESIS SYSTEMS"` to `"NTSC MEGA DRIVE SYSTEMS"` — cosmetic
   re-branding to match, part of the same "COMPATIBLE ONLY WITH NTSC ...
   SYSTEMS" legal text found near `0x21E60`.

No text/script bytes are touched, so this doesn't add a fourth text-diff
data point the way the French/Indonesian patches did — that idea is now
closed out (nothing more to gain there; the existing FR + Indo diff pair
already fully confirms the plain-ASCII encoding and the ~44.6KB script
span).

## Graphics: RNC compression and sprite frames (USA)

The compressed art the French translators "couldn't decompress" is **Rob
Northen ProPack (RNC)**. The USA ROM holds 264 `RNC` blocks (243 method 1,
Huffman; 21 method 2), 3.3 MB unpacked, and every one decodes with a matching
CRC16 (`scripts/rnc.py`, `rnc.py <rom> list`). Method 2 follows the game's own
decompressor, entered at `$960` (it checks the `RNC` method-2 magic first).

Sprites were found from the other end: the DMA queue (`$AD1E`) leads to the
player frame routines (entered at `$B2E` and `$1162`, both reading the frame
bank), which give the frame format (`scripts/frames.py`). Contact sheets of the raw tiles had failed
because the tile order only makes sense through each frame's piece list. With
the format known, a scan for piece runs (each piece's first tile is the sum of
the earlier pieces' sizes) finds 1218 object frames. Woody's 400 player frames
sit in the run-length-coded bank at `$82784`; objects store raw tiles. Buzz
Lightyear's frames, their palette and the frame groups are in `GRAPHICS_USA`
in `toystory_facts.py`. One caution from using them: Buzz's long run of
leg-moving frames looks like a walk cycle but is a fall.

## Open items / next steps if resuming

1. Decode the 2-word string header (`0x01D7`/`0x01D8`-style pair) to get an
   exact string count and pointer/length mechanism.
2. Resolve the 5 per-object `JSR (An)` sites — likely the single highest-value
   remaining target, expected to unlock the entity-behaviour code en masse
   the way idiom A's table did.
3. The 38-entry table at `0x271E` is called from two different sites — worth
   checking whether it's a general "engine command" table (input handling,
   cutscene commands, etc.) shared across subsystems.
4. ~~The `REGION_CHECK_USA` signature is a good candidate to hunt for in
   EU/PAL too~~ — done, see below.
5. The graphics facts are USA coordinates, not yet checked against EU/PAL
   (`rnc.py <EU rom> list` is the quick first check).

## Region-check idiom confirmed in EU/PAL too

Searched EU/PAL for the fixed `LEA $A10001.l,A0 ; MOVE.B (A0),D0` opening
of the region-check idiom (see `REGION_CHECK_USA` above) — exactly one hit,
at `0x20B4C`:

```
lea.l   $a10001.l, a0
move.b  (a0), d0
andi.b  #$c0, d0
cmpi.b  #$c0, d0        ; $c0 = overseas(bit7=1) + PAL(bit6=1) = Europe
bne.b   fail
jsr     $77496.l
rts
fail: jsr ...
```

Same idiom as USA's, adapted two ways: the compare immediate is `$C0`
(overseas+PAL) instead of USA's `$80` (overseas+NTSC) — correctly matches
each build's real target region — and EU/PAL skips the intermediate
`move.w d0,$ffff0686.l` RAM-cache step USA has. Net: the truly portable
part of this signature is just
`LEA $A10001.l,A0 ; MOVE.B (A0),D0 ; ANDI.B #$C0,D0 ; CMPI.B #imm,D0`
(`REGION_CHECK_EU_PAL.signature_masked_core` in the facts module) — the
RAM-cache step is per-build, not part of the idiom itself.
