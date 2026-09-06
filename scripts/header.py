#!/usr/bin/env python3
"""Read a Sega Mega Drive/Genesis ROM header and print key identity fields."""
import sys, hashlib

def read_header(path):
    with open(path, 'rb') as f:
        data = f.read()
    def s(off, n):
        return data[off:off+n].decode('ascii', errors='replace').rstrip()
    h = {
        'file': path,
        'size': len(data),
        'sha1': hashlib.sha1(data).hexdigest(),
        'md5': hashlib.md5(data).hexdigest(),
        'console_name': s(0x100, 16),
        'copyright': s(0x110, 16),
        'domestic_title': s(0x120, 48),
        'overseas_title': s(0x150, 48),
        'serial': s(0x180, 14),
        'checksum_field': int.from_bytes(data[0x18E:0x190], 'big') if len(data) > 0x190 else None,
        'device_support': s(0x190, 16),
        'rom_start': int.from_bytes(data[0x1A0:0x1A4], 'big') if len(data) > 0x1A4 else None,
        'rom_end': int.from_bytes(data[0x1A4:0x1A8], 'big') if len(data) > 0x1A8 else None,
        'ram_start': int.from_bytes(data[0x1A8:0x1AC], 'big') if len(data) > 0x1AC else None,
        'ram_end': int.from_bytes(data[0x1AC:0x1B0], 'big') if len(data) > 0x1B0 else None,
        'modem': s(0x1B0, 12),
        'memo': s(0x1C8, 40),
        'region': s(0x1F0, 16),
    }
    # computed checksum (sum of big-endian words from 0x200 to EOF)
    calc = 0
    for i in range(0x200, len(data) - (len(data) % 2), 2):
        calc = (calc + int.from_bytes(data[i:i+2], 'big')) & 0xFFFF
    h['checksum_calculated'] = calc
    h['checksum_ok'] = (calc == h['checksum_field'])
    return h

if __name__ == '__main__':
    for path in sys.argv[1:]:
        h = read_header(path)
        print(f"=== {path} ===")
        for k, v in h.items():
            if k == 'file':
                continue
            print(f"  {k:20s}: {v}")
        print()
