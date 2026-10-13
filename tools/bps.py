#!/usr/bin/env python3
"""Minimal BPS patch applier (beat/bps format)."""
import sys, struct, zlib

def read_vlq(data, i):
    result = 0
    shift = 1
    while True:
        b = data[i]; i += 1
        result += (b & 0x7f) * shift
        if b & 0x80:
            break
        shift <<= 7
        result += shift
    return result, i

def apply_bps(source_path, patch_path, out_path):
    with open(source_path, 'rb') as f:
        source = f.read()
    with open(patch_path, 'rb') as f:
        patch = f.read()
    assert patch[:4] == b'BPS1', 'not a BPS file'
    i = 4
    source_size, i = read_vlq(patch, i)
    target_size, i = read_vlq(patch, i)
    metadata_size, i = read_vlq(patch, i)
    metadata = patch[i:i+metadata_size]; i += metadata_size

    footer = patch[-12:]
    source_crc, target_crc, patch_crc = struct.unpack('<III', footer)
    body_end = len(patch) - 12

    assert len(source) == source_size, f"source size mismatch: {len(source)} vs {source_size}"

    out = bytearray()
    out_pos = 0
    src_rel = 0
    tgt_rel = 0
    while i < body_end:
        data_cmd, i = read_vlq(patch, i)
        action = data_cmd & 3
        length = (data_cmd >> 2) + 1
        if action == 0:  # SourceRead
            out.extend(source[out_pos:out_pos+length])
            out_pos += length
        elif action == 1:  # TargetRead
            out.extend(patch[i:i+length])
            i += length
            out_pos += length
        elif action == 2:  # SourceCopy
            d, i = read_vlq(patch, i)
            sign = -1 if (d & 1) else 1
            src_rel += sign * (d >> 1)
            out.extend(source[src_rel:src_rel+length])
            src_rel += length
            out_pos += length
        elif action == 3:  # TargetCopy
            d, i = read_vlq(patch, i)
            sign = -1 if (d & 1) else 1
            tgt_rel += sign * (d >> 1)
            for _ in range(length):
                out.append(out[tgt_rel])
                tgt_rel += 1
            out_pos += length

    assert len(out) == target_size, f"target size mismatch: {len(out)} vs {target_size}"
    calc_target_crc = zlib.crc32(out) & 0xffffffff
    ok = (calc_target_crc == target_crc)
    with open(out_path, 'wb') as f:
        f.write(out)
    return ok, metadata

if __name__ == '__main__':
    ok, meta = apply_bps(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"applied -> {sys.argv[3]}  target_crc_ok={ok}  metadata={meta[:200]!r}")
