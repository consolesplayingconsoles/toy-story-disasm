"""
Per-game facts module for Toy Story (Mega Drive), Traveller's Tales / Disney
Interactive, 1995-96.

Confidence key: HIGH = cross-checked by runtime/diff evidence across 2+
independent sources. MED = single strong signal (one decode + one
corroborating diff). LOW = single-source read, not independently verified.

EU/PAL and USA are materially different compiled revisions (~98% of the ROM
differs byte-for-byte -- different framerate, USA has continues only, PAL
adds a password system every 4 levels). Addresses do NOT transfer between
them. Facts below are grouped per revision; anchors are given as masked
byte signatures where practical, per the disassembly skill's guidance,
since fixed addresses are known not to survive between builds here.
"""

IDENTITY = {
    'usa': {
        'sha1': '49be571cd943fd594949c318a0bdbe6263fdd512',
        'size': 4194304,
        'header_console_name': 'SEGA GENESIS',
        'header_copyright': '(C)T-239 1995.OCT',
        'checksum_field': 0x0A94,
        'checksum_ok': True,
        'confidence': 'HIGH',
    },
    'eu_pal': {
        'sha1': '6e7bb9b191389973922a5ab9978205bb9d2664cc',
        'size': 4194304,
        'header_console_name': 'SEGA MEGA DRIVE',
        'header_copyright': '(C)T-239 1996.FEB',
        'checksum_field': 0x70EE,
        'checksum_ok': True,
        'confidence': 'HIGH',
        'note': 'Different compile from USA, not a byte-patch of it '
                '(~98% of the ROM differs). Adds a password system every '
                '4 levels, runs at 25fps vs USA 30fps, per the FR '
                'translation readme.',
    },
    'fr_us': {
        'size': 4194304,   # same as its base: diffrom.py only diffs same-size ROMs (traces/diff_*)
        'sha1': '12df4adf74a2d460c15130e17c6eeb6cac134fc1',
        'source': 'USA + Toy Story (FR-US).bps',
        'checksum_ok': True, 'confidence': 'HIGH',
    },
    'fr_pal': {
        'size': 4194304,   # same as its base: diffrom.py only diffs same-size ROMs (traces/diff_*)
        'sha1': 'f7237963d94ff25054a43fd01ab464ae5bbb477',
        'source': 'EU/PAL + Toy Story (FR-PAL).bps',
        'checksum_ok': True, 'confidence': 'HIGH',
    },
    'indonesian': {
        'size': 4194304,   # same as its base: diffrom.py only diffs same-size ROMs (traces/diff_*)
        'sha1': 'f0181d510065112f2e7e382d56652a69316d676a',
        'source': 'USA + Toy Story (Indo).ips',
        'checksum_ok': False,
        'confidence': 'HIGH',
        'note': 'IPS patch does not recompute the header checksum field. '
                'Cosmetic only -- Genesis carts are not runtime-checksummed '
                'the way some other Sega platforms are.',
    },
    'jp_ntsc_region_patch': {
        'sha1': '6a37e5284460747fa3bea06b02cae774c61898d6',
        'source': 'USA + Toy Story (JP).ips (real patch, 49 bytes, 3 records; '
                   'the operator\'s first copy of this file was a saved GitHub '
                   'HTML page, not a real .ips -- corrected mid-session)',
        'checksum_ok': True,
        'confidence': 'HIGH',
        'note': 'NOT a translation, despite the repo name '
                '(github.com/luxbiter/Toy-Story-MD-JP-). Three edits, all on '
                'the USA ROM: (1) recompute header checksum field @0x18E, '
                '(2) flip the immediate in the hardware-region-check routine '
                'from #$80 to #$00 (see REGION_CHECK below) -- converts the '
                'boot gate from "expects overseas+NTSC (USA)" to "expects '
                'domestic+NTSC (Japan)", (3) rewrite the boot disclaimer '
                'string @0x21E6A from "NTSC GENESIS SYSTEMS" to "NTSC MEGA '
                'DRIVE SYSTEMS" (cosmetic re-brand to match). No script/text '
                'was touched, so this does not add a 4th text-diff data '
                'point the way FR/Indo did.',
    },
}

# Sega Genesis/MD hardware-version-register region check ($A10001, bit7 =
# domestic/overseas, bit6 = NTSC/PAL). Extremely common idiom across MD
# games -- worth checking for near any game's boot path. Found here at USA
# coords 0x20960-0x20976; confirmed by the JP region patch flipping exactly
# the trailing immediate byte (0x20975: cmpi.b #$80,d0 -> #$00,d0).
REGION_CHECK_USA = {
    'addr': 0x20960,
    'confidence': 'HIGH',
    'disasm': [
        'lea.l   $a10001.l, a0',
        'move.b  (a0), d0',
        'move.w  d0, $ffff0686.l',   # cached to RAM for later reads
        'andi.b  #$c0, d0',          # isolate domestic/overseas + NTSC/PAL bits
        'cmpi.b  #$80, d0',          # $80 = overseas(bit7=1) + NTSC(bit6=0) = USA
        'bne.b   fail',
        'jsr     $76bf6.l',          # region-ok path
        'rts',
        'fail: jsr $76bf6.l',
        'move.w  #$13, $ffff0498.l',
    ],
    # masked signature: wildcards the cached-RAM destination address and the
    # final compare immediate (that byte is exactly what the JP patch flips)
    'signature_masked': '41 F9 00 A1 00 01 10 10 33 C0 ?? ?? ?? ?? 02 00 00 C0 0C 00 00 ??',
}

# Confirmed present in EU/PAL too, at a different address and with a
# slightly different shape (no intermediate RAM-cache step, and it checks
# for Europe instead of USA) -- same idiom, adapted per-build. Cross-build
# confirmation for open item "does REGION_CHECK show up in EU/PAL too?".
REGION_CHECK_EU_PAL = {
    'addr': 0x20B4C,
    'confidence': 'HIGH',
    'disasm': [
        'lea.l   $a10001.l, a0',
        'move.b  (a0), d0',
        'andi.b  #$c0, d0',          # no RAM-cache step here, unlike USA
        'cmpi.b  #$c0, d0',          # $c0 = overseas(bit7=1) + PAL(bit6=1) = Europe
        'bne.b   fail',
        'jsr     $77496.l',
        'rts',
        'fail: jsr ...',
    ],
    # truly-invariant core shared with the USA build (region-comparison
    # immediate and the optional RAM-cache step both vary per build/region):
    'signature_masked_core': '41 F9 00 A1 00 01 10 10 02 00 00 C0 0C 00 00 ??',
}

# EU/PAL coordinates (primary target of this analysis pass).
DISPATCH_TABLES_EU_PAL = [
    {
        'name': 'shared_command_table_38',
        'idiom': 'A (BRA.W trampoline table)',
        'base': 0x271E,
        'entries': 38,
        'called_from': [0x26C4, 0x284E],
        'confidence': 'HIGH',
        'note': 'Only table found reached from 2 distinct call sites '
                '(one direct PC-relative JSR, one via LEA+register-indexed '
                'JSR) -- likely a shared engine command/event table, worth '
                'prioritising if resuming.',
    },
    {'name': 'jmp_table_11a', 'idiom': 'A', 'base': 0x4D38, 'called_from': [0x4D34], 'confidence': 'MED'},
    {'name': 'jmp_table_31', 'idiom': 'A', 'base': 0xB178, 'entries': 31, 'called_from': [0xB174], 'confidence': 'HIGH'},
    {'name': 'jmp_table_17a', 'idiom': 'A', 'base': 0x1033A, 'entries': 17, 'called_from': [0x10336], 'confidence': 'HIGH'},
    {'name': 'jmp_table_11b', 'idiom': 'A', 'base': 0x4ECE, 'entries': 11, 'called_from': [0x4ECA], 'confidence': 'HIGH'},
    {'name': 'jmp_table_11c', 'idiom': 'A', 'base': 0x4EA2, 'entries': 11, 'called_from': [0x4C9E], 'confidence': 'MED'},
    {'name': 'call_table_17b', 'idiom': 'A', 'base': 0x1027C, 'entries': 17, 'called_from': [0x102C2], 'confidence': 'HIGH'},
    {
        'name': 'entity_state_event_table_1', 'idiom': 'C (word-relative table)',
        'base': 0x42618, 'entries': 121, 'called_from': [0x42614], 'confidence': 'HIGH',
        'note': 'Index = ANDI.W #$E0 group nibble OR (ANDI.W #$F sub-state '
                '<<1) -- looks like a per-object "state x event" behaviour '
                'table.',
    },
    {
        'name': 'entity_state_event_table_2', 'idiom': 'C', 'base': 0x424F8,
        'entries': 121, 'called_from': [0x424F4], 'confidence': 'HIGH',
        'note': 'Same shape as entity_state_event_table_1, different '
                'entity/object class.',
    },
]

INLINE_COMPUTED_JUMPS_EU_PAL = [
    {'name': 'block_copy_duff', 'base': 0x138A, 'jumped_from': 0x1386,
     'note': 'move.l (a0)+,(a2)+ unrolled, index x2 (word stride)', 'confidence': 'HIGH'},
    {'name': 'block_fill_duff', 'base': 0x12FE, 'jumped_from': 0x12FA,
     'note': 'move.l d7,(a1)+ unrolled fill, D7 likely caller-supplied fill word',
     'confidence': 'MED'},
]

# The 5 genuinely-unresolved per-object dispatch sites (register value comes
# from a struct field at runtime, not derivable statically from code alone):
UNRESOLVED_SITES_EU_PAL = [
    {'addr': 0x7ADCE, 'op': 'jsr (a4)'},
    {'addr': 0x7AE4A, 'op': 'jsr (a4)'},
    {'addr': 0x7AE10, 'op': 'jsr (a4)'},
    {'addr': 0x7859E, 'op': 'jsr (a4, d1.w)'},
    {'addr': 0x7CE84, 'op': 'jsr (a4, d1.w)'},
]

TEXT = {
    'encoding': 'plain 7-bit ASCII, uppercase, space-padded fixed-width slots',
    'confidence': 'HIGH',
    'evidence': 'diffed against 2 independent fan translations (FR, Indonesian); '
                'both show literal readable ASCII swapped in place',
    'delimiter': '"',  # each line/string bounded by literal ASCII quote marks
    'span_usa_coords': (0x1AC91, 0x27528),
    'span_eu_pal_coords_start_approx': 0x1AE05,  # shifted due to different compile; end not re-measured
    'diffing_regions_usa_vs_fr': 143,
    'diffing_regions_usa_vs_indo': 149,
    'diffing_bytes_usa_vs_fr': 12100,
    'header_before_first_string': bytes.fromhex('0001d700000000000000003cc16000 01d8'.replace(' ', '')),
    'header_decoded': False,  # two u16 fields (0x01D7, 0x01D8 in the first record) not yet identified
    'pointer_table_found': False,
    'note': 'Searched for absolute 32-bit and 24-bit big-endian pointers to '
            '0x1AC91 (USA coords) across the whole ROM -- zero hits. Lookup '
            'mechanism is not a literal absolute-address pointer table; '
            'likely PC-relative or goes through the undeciphered 2-word '
            'header per string.',
}

COVERAGE = {
    'eu_pal_first_pass_pct': 1.8535,
    'eu_pal_after_idioms_pct': 3.2633,
    'eu_pal_num_instructions': 33836,
    'unresolved_sites_before_idioms': 16,
    'unresolved_sites_after_idioms': 5,
    'entropy_note': 'H in [6,8): 34% of ROM, ~0% code -- compressed art/audio. '
                     'H in [3,5): 45% of ROM, only ~5% code so far -- mostly '
                     'uncompressed level/object data + the text blob, not '
                     'missed code (unlike the reference game this skill was '
                     'written from, data here does not sit at high entropy).',
}

# ---- graphics (USA coords) -------------------------------------------------
# The art the French translators "couldn't decompress" (their readme) is Rob
# Northen ProPack. scripts/rnc.py decodes it, scripts/frames.py the sprites.
GRAPHICS_USA = {
    'compression': {
        'format': 'Rob Northen ProPack (RNC): 18-byte header "RNC", method, '
                  'unpacked size, packed size, unpacked CRC16, packed CRC16 '
                  '(poly 0xA001), leeway, chunk count',
        'blocks': 264, 'blocks_decoded': 264, 'method1_huffman': 243, 'method2': 21,
        'unpacked_bytes': 3314612,
        'decompressor_method2': 0x960,   # entry: checks the 'RNC',2 magic; $9DE is its decode loop
        'note': 'Every block decodes to its header size with a matching CRC16. '
                'The method-2 routine at $960 primes its bit buffer with $80, '
                'refills with addx, skips 2 header bits, decodes in place (leeway '
                'byte at -2(a3)); length code 9 is a literal run of (n+3)*4 bytes.',
        'confidence': 'HIGH',
    },
    'sprite_frame': {
        'format': 'header [w0 = 6+6*count][count][size in words], then count '
                  '6-byte pieces [size=(w-1)<<2|(h-1)][first tile][x][y][x flipped]'
                  '[y flipped], then the tiles at frame+w0; tiles column-major per '
                  'piece, first tile = running sum of the earlier pieces',
        'found_via': 'DMA queue $AD1E -> the player frame routines entered at $B2E '
                     'and $1162 (both read the bank at $B7C and $11AC); then a scan '
                     'for piece runs where tile[i+1] = tile[i] + '
                     'size[i] (1218 object frames)',
        'object_frames_found': 1406,     # the 2026-10-13 scan below (OBJECT_FRAME_BLOCKS_USA); was 1218
        'player_bank': 0x82784,          # Woody: table of longs, top byte = literal offset/2, low 24 = the frame's
                                         # offset FROM THE BANK (frame = $82784 + offset): all 400 decode
        'player_frames': 400,            # all decode to their exact size
        'player_rle_routine': 0x1162,    # entry; the bank read is at $11AC
        'player_alt_banks_rnc': [0x25E4E0, 0x2622A8],
        'objects': 'same header, raw tiles (no run-length coding)',
        'confidence': 'HIGH',
    },
    'palettes': {
        'table': (0x7DDCA, 0x7E47A),     # 16-colour palettes; DMA'd by $D480, $11C40, $16900
        'buzz': 0x7DFFA,                 # duplicate at $7E73A: white, green, purple, skin
        'confidence': 'MED',
    },
    # Buzz Lightyear's object frames, by address (frame starts), identified by
    # rendering every frame with his palette.
    # Groups: (first frame, last frame, frame count).
    'buzz_frames': {
        'arm_raised': (0x1E9974, 0x1ED5D4, 9),
        'falling': (0x1EDE7C, 0x1FED6A, 48),     # look like a walk, are not
        'front': (0x1FF2D4, 0x1FF2D4, 1),
        'stand': (0x1FF970, 0x1FF970, 1),
        'stride': (0x1FFF6C, 0x1FFF6C, 1),
        'lunge': (0x20053C, 0x200B72, 2),
        'wings_out': (0x2011CE, 0x2011CE, 1),
        'carrying_tyre': (0x201950, 0x20549C, 9),
        'confidence': 'MED',
    },
    'other_frames_seen': {
        'mr_potato_head': 0x1DC958,
        'cluster_rex_hamm_rc_babyface_vehicles': 0x0FDBF6,
        'confidence': 'LOW',
    },
}

# ---- sprite frame data (USA coords) -------------------------------------------
# Woody's 400 run-length coded frames sit back to back after his bank: each frame's extent is its
# header, pieces, command bytes and literal longs (tools/frames.py's format), all 400 decoding to
# their exact size.
PLAYER_FRAMES_USA = (0x082F1C, 0x0E4A25)
# Object frames found by scanning for the frame header (w0 = 6 + 6*count, 1-40 pieces, each piece's
# first tile the running sum of the earlier sizes, size = the pieces' tiles) outside the traced code,
# the RNC blocks and the player frames; single-piece frames only next to another frame. 1406
# frames, merged into runs (gaps of 16 bytes or less). A random sample of 48 all rendered as
# real sprites (Woody, Buzz, Rex, Hamm, Mr Potato Head, Babyface, RC, the planes, the shoe).
OBJECT_FRAME_BLOCKS_USA = [
    (0x0E4A26, 0x0E4F61),
    (0x0E52BE, 0x0E5839),
    (0x0E5B9A, 0x0E60D5),
    (0x0E649A, 0x0E69DB),
    (0x0E6D24, 0x0E715F),
    (0x0E741E, 0x0E788D),
    (0x0E7B46, 0x0E7F7B),
    (0x0E8290, 0x0E877D),
    (0x0E8B34, 0x0E90B5),
    (0x0E9490, 0x0E9A0B),
    (0x0E9DD8, 0x0EA3CD),
    (0x0EA78A, 0x0EACC5),
    (0x0EB07E, 0x0EB5F9),
    (0x0EB9D8, 0x0EBF33),
    (0x0EC358, 0x0EC807),
    (0x0ECB20, 0x0ECFE1),
    (0x0ED2D8, 0x0ED78D),
    (0x0EDA9C, 0x0EDF91),
    (0x0EE288, 0x0EE769),
    (0x0EEA7A, 0x0EEF2F),
    (0x0EF25A, 0x0EF70F),
    (0x0EFA42, 0x0EFEDD),
    (0x0F0240, 0x0F0721),
    (0x0F0A98, 0x0F0FF9),
    (0x0F1350, 0x0F18B7),
    (0x0F1C12, 0x0F214D),
    (0x0F24EA, 0x0F2A4B),
    (0x0F2D9A, 0x0F32C9),
    (0x0F3686, 0x0F3BC1),
    (0x0F3F74, 0x0F44D5),
    (0x0F4848, 0x0F4DA9),
    (0x0F5106, 0x0F5647),
    (0x0F59B6, 0x0F5ED1),
    (0x0F6294, 0x0F67F5),
    (0x0F6BDC, 0x0F7183),
    (0x0F75B2, 0x0F7B85),
    (0x0F7FB4, 0x0F85C7),
    (0x0F9446, 0x0FD8F5),
    (0x0FDBF6, 0x1266B1),
    (0x1268CA, 0x13C4C7),
    (0x13C67C, 0x1449B5),
    (0x144A76, 0x146805),
    (0x146846, 0x147801),
    (0x147862, 0x14C84F),
    (0x14C8D0, 0x152741),
    (0x1527CE, 0x157373),
    (0x158E08, 0x16D2F5),
    (0x16D456, 0x176F5B),
    (0x177060, 0x18569D),
    (0x185746, 0x18AC7B),
    (0x18BB88, 0x18CC21),
    (0x18D360, 0x1916B5),
    (0x191776, 0x19A287),
    (0x19A368, 0x1A183D),
    (0x1A18DE, 0x1A958F),
    (0x1A9624, 0x1B0807),
    (0x1B76A8, 0x1BA081),
    (0x1BA112, 0x1BC617),
    (0x1BC6A8, 0x1BFAF1),
    (0x1BFB72, 0x1C0A9D),
    (0x1C0B1E, 0x1C5157),
    (0x1C5278, 0x1D8EBF),
    (0x1D9064, 0x1E7885),
    (0x1E9974, 0x1EDD5B),
    (0x1EDE7C, 0x205C23),
    (0x22D2C0, 0x22DE37),
    (0x22E6A8, 0x244A81),
    (0x244ADE, 0x24E0C1),
    (0x24E122, 0x2582F9),
    (0x25835A, 0x25E4DF),
    (0x2E16DC, 0x2E1CA3),
    (0x2E1CC4, 0x2E35A5),
    (0x2E6C42, 0x2EE57B),
    (0x2EE600, 0x2F02CF),
    (0x2F0354, 0x2F2127),
    (0x2F21AC, 0x2F3ED7),
    (0x2F3F08, 0x2F5A4F),
    (0x2F5B18, 0x2FBE71),
    (0x30690C, 0x309419),
    (0x30AF76, 0x30B493),
    (0x30B546, 0x311405),
    (0x312888, 0x3189E5),
    (0x31F3F4, 0x322269),
    (0x325CC2, 0x32A83F),
    (0x3305C8, 0x3351DF),
    (0x33A1B0, 0x33BDE9),
    (0x33BE4A, 0x33D8F9),
    (0x33D90E, 0x33E349),
    (0x3D564E, 0x3DA9E1),
]

# ---- names and region map (USA coords) ---------------------------------------
# Read from the code (traces/trace_usa.json). NAMES_USA: address -> name.
NAMES_USA = {
    0x000200: 'EntryPoint',          # TMSS/VDP/Z80/PSG init (the standard Sega boot block), then falls into Main
    0x0002FA: 'Main',                # waits for DMA idle, installs VBlankDefault/HBlankDefault, sets up, runs the game
    0x00238A: 'VBlankInterrupt',     # level-6 vector: jumps through the RAM pointer at VBlankVector
    0x002392: 'VBlankDefault',       # the RAM pointer's default: sets VBlankSeen and returns
    0x00239C: 'HBlankInterrupt',     # level-4 vector: jumps through the RAM pointer at HBlankVector
    0x0023A4: 'HBlankWriteReg11',    # an HBlank handler other code installs: VDP reg 11 = $03 (per-line hscroll), return
    0x0023AE: 'HBlankDefault',       # rte: the RAM pointer's default; the unused vectors point into this run of rte (level 2 at the second)
    0x002138: 'ResetDisplay',        # sets VBlankVector to VBlankDefault, then falls into ResetDisplayVdp (22 callers)
    0x002142: 'ResetDisplayVdp',     # HBlank back to HBlankDefault, VDP regs 2/4/7/11/12/13/16 rewritten, scroll and plane areas cleared
    0x002210: 'InitVdpRegisters',    # writes VDP registers 0-14, 16-18 and 15 (auto-increment 2)
    0x0022B2: 'ClearVram',           # VRAM write at $0000, 2048 x 8 longs of zero: all 64 KB
    0x00233C: 'ClearCram',           # CRAM write at 0, 64 words of zero
    0x002358: 'ClearVsram',          # VSRAM write at 0, 64 words of zero
    0x000960: 'RncUnpack2',          # RNC method 2: checks the magic, unpacks in place
    0x00AB1E: 'WaitFrames',          # clears VBlankSeen and waits for it, d0+1 times
    0x00AD1E: 'QueueDma',            # the DMA queue the sprite loaders feed
    0x020960: 'RegionCheck',         # $A10001: expects overseas + NTSC (REGION_CHECK_USA)
    0x07DDCA: 'PaletteTable',        # 16-colour palettes
    0x07DFFA: 'BuzzPalette',
    0xFFFF0400: 'VBlankVector',      # RAM long: handler the VBlank vector jumps to (Main sets VBlankDefault)
    0xFFFF0404: 'HBlankVector',      # RAM long: handler the HBlank vector jumps to (Main sets HBlankDefault)
    0xFFFF04AA: 'VBlankSeen',        # word: VBlankDefault sets it to 1
    0x082784: 'PlayerFrameBank',     # Woody: 400 longs, run-length coded frames
}

# Instructions whose immediate is a ROM address (a handler installed in a RAM vector): they assemble as labels.
POINTERS_USA = {
    0x000314, 0x00031E, 0x0003F8, 0x000402, 0x000472, 0x00047C,
    0x00071A, 0x000724, 0x002138, 0x00214A, 0x002154, 0x00A6FA,
    0x00A740, 0x00C0DC, 0x00D192, 0x00E866, 0x01037E, 0x011B88,
    0x012FA0, 0x013932, 0x016856, 0x0174E4, 0x023F2A, 0x023F34,
    0x0240DE, 0x0240E8, 0x02412A, 0x024134, 0x024392, 0x02439C,
    0x0244D4, 0x024536, 0x077520, 0x07752A, 0x07755E, 0x077568,
    0x07B24E, 0x07B258, 0x07B278, 0x07B282, 0x07D862, 0x07D8C2,
}

# (start, end inclusive, what, confidence: HIGH, MED, LOW as above)
REGIONS_USA = [
    (0x01AC91, 0x027528, 'script text, plain ASCII', 'HIGH'),
    (0x07DDCA, 0x07E47A, 'palette table', 'MED'),
    (0x082784, 0x082DC3, 'player frame bank: 400 longs', 'HIGH'),
    (0x1E9974, 0x205C23, 'Buzz Lightyear object frames', 'MED'),
]
# Every RNC block, (start, end inclusive): header + packed data. All 264 decode.
RNC_BLOCKS_USA = [
    (0x1573C0, 0x1584A3),
    (0x158504, 0x158D1A),
    (0x18ACBC, 0x18BB36),
    (0x18CC42, 0x18D2BE),
    (0x1B0808, 0x1B3889),
    (0x1B388A, 0x1B7647),
    (0x1E796A, 0x1E98E7),
    (0x205D20, 0x2077B7),
    (0x2077B8, 0x20CD7C),
    (0x20CD7E, 0x20E262),
    (0x20E264, 0x212F4C),
    (0x212F4E, 0x217424),
    (0x217426, 0x21CE15),
    (0x21CE16, 0x2211AF),
    (0x2211B0, 0x22576A),
    (0x22576C, 0x229A2E),
    (0x229A30, 0x22D15F),
    (0x25E4E0, 0x2622A7),
    (0x2622A8, 0x263D88),
    (0x269C0A, 0x26AD12),
    (0x26AD14, 0x26BE03),
    (0x26BE04, 0x26CF71),
    (0x26CF72, 0x26D3A5),
    (0x26D3A6, 0x26DBF8),
    (0x26DF26, 0x2706D8),
    (0x2706DA, 0x27121B),
    (0x27121C, 0x2714EF),
    (0x2714F0, 0x271578),
    (0x27257A, 0x274FCD),
    (0x274FCE, 0x275A47),
    (0x275A48, 0x275C66),
    (0x275C68, 0x275CE8),
    (0x2764EA, 0x2798CD),
    (0x2798CE, 0x27A2D3),
    (0x27A2D4, 0x27A657),
    (0x27A658, 0x27A6AA),
    (0x27A6AC, 0x27A974),
    (0x27A976, 0x27D203),
    (0x27D204, 0x27D67E),
    (0x27D680, 0x27D6F6),
    (0x27D6F8, 0x27D744),
    (0x27D746, 0x27DC9F),
    (0x27DCA0, 0x28185E),
    (0x281860, 0x282533),
    (0x282534, 0x28326C),
    (0x28326E, 0x2832AC),
    (0x2832AE, 0x283FFB),
    (0x283FFC, 0x2867FB),
    (0x2867FC, 0x287185),
    (0x287186, 0x2875E3),
    (0x2875E4, 0x287658),
    (0x28865A, 0x28B089),
    (0x28B08A, 0x28BA2B),
    (0x28BA2C, 0x28BE96),
    (0x28BE98, 0x28BEDE),
    (0x28BEE0, 0x28C282),
    (0x28C284, 0x28DE67),
    (0x28DE68, 0x28E419),
    (0x28E41A, 0x28E4B1),
    (0x28E4B2, 0x28E4DB),
    (0x28E4DC, 0x28EAE9),
    (0x28EAEA, 0x28F68B),
    (0x28F68C, 0x2914B9),
    (0x2914BA, 0x291ED4),
    (0x291ED6, 0x2921E6),
    (0x2921E8, 0x292233),
    (0x292234, 0x2928A3),
    (0x2928A4, 0x2935FD),
    (0x2935FE, 0x296BB0),
    (0x296BB2, 0x2974FB),
    (0x2974FC, 0x297DC7),
    (0x297DC8, 0x297E16),
    (0x297E18, 0x29A9B7),
    (0x29A9B8, 0x29A9DA),
    (0x29A9DC, 0x29AA0B),
    (0x29AA0C, 0x29AA2F),
    (0x29AA30, 0x29B176),
    (0x29B178, 0x29B745),
    (0x29B746, 0x2A007D),
    (0x2A007E, 0x2A0946),
    (0x2A0948, 0x2A0C8F),
    (0x2A0C90, 0x2A0CD7),
    (0x2A0CD8, 0x2A147C),
    (0x2A147E, 0x2A2561),
    (0x2A2562, 0x2A548C),
    (0x2A548E, 0x2A6017),
    (0x2A6018, 0x2A6564),
    (0x2A6566, 0x2A65F1),
    (0x2A7BF2, 0x2A82D5),
    (0x2A82D6, 0x2AAB81),
    (0x2AAB82, 0x2AB663),
    (0x2AB664, 0x2ABC80),
    (0x2ABC82, 0x2ABCDB),
    (0x2ABCDC, 0x2AC12B),
    (0x2AC12C, 0x2AC9D3),
    (0x2AC9D4, 0x2B0C12),
    (0x2B0C14, 0x2B1B71),
    (0x2B1B72, 0x2B2893),
    (0x2B2894, 0x2B2914),
    (0x2B2916, 0x2B2B2F),
    (0x2B2B30, 0x2B3664),
    (0x2B3666, 0x2B672B),
    (0x2B672C, 0x2B768D),
    (0x2B768E, 0x2B7D38),
    (0x2B7D3A, 0x2B7D59),
    (0x2B7D5A, 0x2BA750),
    (0x2BA752, 0x2BB5C2),
    (0x2BD5C4, 0x2BEF65),
    (0x2BEF66, 0x2BF1CC),
    (0x2CAC8E, 0x2CAE36),
    (0x2CBE38, 0x2CC21D),
    (0x2CC21E, 0x2CD370),
    (0x2CD372, 0x2CE410),
    (0x2CE412, 0x2CEBFB),
    (0x2CEBFC, 0x2CFC38),
    (0x2CFC3A, 0x2D02C0),
    (0x2D02C2, 0x2D0323),
    (0x2DD0A4, 0x2DF8DF),
    (0x2DF8E0, 0x2E16BB),
    (0x2E64C6, 0x2E6857),
    (0x2E6858, 0x2E6BBC),
    (0x2FBE72, 0x3008A7),
    (0x3008A8, 0x3039AD),
    (0x3039AE, 0x303D92),
    (0x303D94, 0x3068AA),
    (0x30981A, 0x30A6BA),
    (0x30A6BC, 0x30AAF4),
    (0x30AB24, 0x30AF70),
    (0x30B494, 0x30B4C4),
    (0x311406, 0x311772),
    (0x311824, 0x311BF4),
    (0x311C8A, 0x312847),
    (0x3189E6, 0x318EA1),
    (0x31CEA2, 0x31DCB3),
    (0x31DCB4, 0x31E558),
    (0x31E55A, 0x31EC2E),
    (0x31EC30, 0x31F39A),
    (0x32226A, 0x325C6D),
    (0x32A840, 0x32DAAF),
    (0x32DAD2, 0x32DB9E),
    (0x32DBA0, 0x32DE9E),
    (0x32DEA0, 0x32E4BC),
    (0x32E4BE, 0x32E73A),
    (0x32E73C, 0x32EABF),
    (0x32EAC0, 0x32EFB4),
    (0x32EFB6, 0x32F2DE),
    (0x32F2E0, 0x32F866),
    (0x32F868, 0x32F9FE),
    (0x32FA00, 0x32FC68),
    (0x32FC6A, 0x32FD5A),
    (0x32FD5C, 0x32FFF9),
    (0x32FFFA, 0x330055),
    (0x330056, 0x330403),
    (0x330404, 0x330459),
    (0x33045A, 0x3305A7),
    (0x3351E0, 0x3355B0),
    (0x3355B2, 0x335602),
    (0x335604, 0x335793),
    (0x335794, 0x335A27),
    (0x335A28, 0x335B05),
    (0x335B06, 0x335FCC),
    (0x335FCE, 0x336490),
    (0x336492, 0x3368E8),
    (0x3368EA, 0x336BFA),
    (0x336BFC, 0x336C1C),
    (0x336C1E, 0x336C3E),
    (0x336C40, 0x336C60),
    (0x336C62, 0x336FC4),
    (0x336FC6, 0x33703B),
    (0x33703C, 0x33705C),
    (0x33705E, 0x33707E),
    (0x33E34A, 0x33F0C0),
    (0x33F0C2, 0x33F359),
    (0x33F35A, 0x33FFEA),
    (0x33FFEC, 0x3401A7),
    (0x3401A8, 0x340266),
    (0x340268, 0x3442A9),
    (0x3442AA, 0x34C263),
    (0x34C264, 0x352948),
    (0x352A14, 0x352E78),
    (0x352ED8, 0x353196),
    (0x353412, 0x354611),
    (0x354612, 0x355C10),
    (0x355C12, 0x357755),
    (0x3579BC, 0x358B65),
    (0x358B66, 0x359054),
    (0x359B4E, 0x3606EE),
    (0x3606F0, 0x3682DE),
    (0x3682E0, 0x3692F0),
    (0x3692F2, 0x3695C9),
    (0x3695CA, 0x36987D),
    (0x36987E, 0x36EA1D),
    (0x36EA1E, 0x372C2E),
    (0x372C30, 0x373471),
    (0x373472, 0x373642),
    (0x373644, 0x374133),
    (0x374134, 0x374519),
    (0x37451A, 0x37484B),
    (0x37484C, 0x374D82),
    (0x374D84, 0x374F79),
    (0x374F7A, 0x378A07),
    (0x378A08, 0x37CC2C),
    (0x37CC2E, 0x37EEF1),
    (0x37EEF2, 0x37F11D),
    (0x37F11E, 0x37F288),
    (0x37F28A, 0x380E56),
    (0x380E58, 0x38280A),
    (0x38280C, 0x3843A5),
    (0x3843A6, 0x38581C),
    (0x38581E, 0x38641A),
    (0x38641C, 0x387803),
    (0x387804, 0x388ED7),
    (0x388ED8, 0x38A865),
    (0x38A866, 0x38C787),
    (0x38C788, 0x38E3EF),
    (0x38E3F0, 0x390012),
    (0x390014, 0x392137),
    (0x392138, 0x39347E),
    (0x393480, 0x394A62),
    (0x394A64, 0x3969C9),
    (0x3969CA, 0x3985F1),
    (0x3985F2, 0x399D68),
    (0x399D6A, 0x39B47A),
    (0x39B47C, 0x39C9A5),
    (0x39C9A6, 0x39E721),
    (0x39E722, 0x3A01A6),
    (0x3A01A8, 0x3A1684),
    (0x3A1686, 0x3A3519),
    (0x3A351A, 0x3A50B6),
    (0x3A50B8, 0x3A6DFF),
    (0x3A6E00, 0x3A8BFD),
    (0x3A8BFE, 0x3AAC0F),
    (0x3AAC10, 0x3ACBBA),
    (0x3ACBBC, 0x3AE50C),
    (0x3AE50E, 0x3B0366),
    (0x3B0368, 0x3B1F6B),
    (0x3B1F6C, 0x3B3F52),
    (0x3B3F54, 0x3B5C0F),
    (0x3B5C10, 0x3B7953),
    (0x3B7954, 0x3B98BA),
    (0x3B98BC, 0x3BABF1),
    (0x3BABF2, 0x3BC2BA),
    (0x3BC2BC, 0x3BD783),
    (0x3BD784, 0x3BF53F),
    (0x3BF540, 0x3C1166),
    (0x3C1168, 0x3C34AA),
    (0x3C34AC, 0x3C58D6),
    (0x3C58D8, 0x3C7D44),
    (0x3C7D46, 0x3CA0DB),
    (0x3CA0DC, 0x3CC15F),
    (0x3CC160, 0x3CD832),
    (0x3CD834, 0x3D0659),
    (0x3D065A, 0x3D1238),
    (0x3D123A, 0x3D1470),
    (0x3D1472, 0x3D14E9),
    (0x3D14EA, 0x3D1608),
    (0x3DA9E2, 0x3DBE7C),
    (0x3F7C2A, 0x3FA229),
    (0x3FA22A, 0x3FAC47),
    (0x3FAC48, 0x3FBADF),
    (0x3FBAE0, 0x3FBF16),
    (0x3FBF18, 0x3FC6F2),
    (0x3FC6F4, 0x3FC7DA),
    (0x3FC7DC, 0x3FD00B),
]

# Object frame runs identified by rendering every frame of the run (2026-10-13): (first frame,
# frames, character). A run is walked frame by frame from its first frame (tools/frame_blocks.py
# checks each one). Runs not listed are not identified yet; within Mr Potato Head's run the last 8
# frames (a large close-up) are left out.
OBJECT_GROUPS_USA = [
    (0x0FDBF6, 65, 'rex'),
    (0x13C67C, 40, 'plane'),
    (0x158E08, 49, 'hamm'),
    (0x177060, 26, 'rc'),
    (0x1C5278, 48, 'babyface'),
    (0x1D9064, 49, 'mr_potato_head'),
    (0x22E6A8, 20, 'scud'),
]

# ---- data blocks for the rebuild (tools/rebuild.py BLOCKS) --------------------
# (start, end inclusive, name, format): a block counts as source only when every byte of it is what
# the format says, decoded by a tool here. A sprite frame is a header (structured: it counts only
# once written as source) and its tiles (a leaf asset): tools/frame_blocks.py decodes every
# identified frame (Woody's 400 from his bank, Buzz's 8 groups walked frame by frame) and lists
# each frame's tiles in log/toy_story_frame_blocks.py. Woody's table holds bank-relative offsets
# with a literal byte on top: structured, listed for its name only.
from toy_story_frame_blocks import FRAME_TILE_BLOCKS_USA
BLOCKS_USA = [
    (0x082784, 0x082DC3, 'woody_frame_table', 'frame_offsets'),
] + FRAME_TILE_BLOCKS_USA
