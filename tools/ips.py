#!/usr/bin/env python3
"""Summarise / apply an IPS patch."""
import sys

def parse_ips(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:5] == b'PATCH', 'not an IPS file'
    i = 5
    records = []
    while i < len(data):
        if data[i:i+3] == b'EOF':
            i += 3
            break
        offset = int.from_bytes(data[i:i+3], 'big'); i += 3
        size = int.from_bytes(data[i:i+2], 'big'); i += 2
        if size == 0:
            # RLE record
            rle_len = int.from_bytes(data[i:i+2], 'big'); i += 2
            val = data[i]; i += 1
            records.append((offset, rle_len, bytes([val]) * rle_len, True))
        else:
            chunk = data[i:i+size]; i += size
            records.append((offset, size, chunk, False))
    trailer = data[i:]
    truncate_len = None
    if len(trailer) == 3:
        truncate_len = int.from_bytes(trailer, 'big')
    return records, truncate_len

def apply_ips(rom_path, ips_path, out_path):
    with open(rom_path, 'rb') as f:
        rom = bytearray(f.read())
    records, trunc = parse_ips(ips_path)
    for offset, size, chunk, is_rle in records:
        end = offset + size
        if end > len(rom):
            rom.extend(b'\x00' * (end - len(rom)))
        rom[offset:end] = chunk
    if trunc is not None and trunc < len(rom):
        rom = rom[:trunc]
    with open(out_path, 'wb') as f:
        f.write(rom)
    return len(records)

if __name__ == '__main__':
    if sys.argv[1] == 'apply':
        n = apply_ips(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"applied {n} records -> {sys.argv[4]}")
    else:
        records, trunc = parse_ips(sys.argv[1])
        total_bytes = sum(r[1] for r in records)
        lo = min(r[0] for r in records)
        hi = max(r[0] + r[1] for r in records)
        print(f"{sys.argv[1]}: {len(records)} records, {total_bytes} bytes total, "
              f"span 0x{lo:X}-0x{hi:X}, truncate={trunc}")
        for offset, size, chunk, is_rle in records:
            kind = 'RLE ' if is_rle else 'RAW '
            print(f"  {kind}0x{offset:06X} +{size:5d}  {chunk[:16].hex()}{'...' if size>16 else ''}")
