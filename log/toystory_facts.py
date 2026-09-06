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
        'sha1': '12df4adf74a2d460c15130e17c6eeb6cac134fc1',
        'source': 'USA + Toy Story (FR-US).bps',
        'checksum_ok': True, 'confidence': 'HIGH',
    },
    'fr_pal': {
        'sha1': 'f7237963d94ff25054a43fd01ab464ae5bbb477',
        'source': 'EU/PAL + Toy Story (FR-PAL).bps',
        'checksum_ok': True, 'confidence': 'HIGH',
    },
    'indonesian': {
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
        'entries': 121, 'called_from': [0x4224F4], 'confidence': 'HIGH',
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
