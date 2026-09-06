#!/usr/bin/env python3
"""Diff two same-size ROMs and report merged difference regions."""
import sys, json

def diff_regions(a, b, gap=8):
    assert len(a) == len(b), f"size mismatch {len(a)} vs {len(b)}"
    n = len(a)
    regions = []
    i = 0
    while i < n:
        if a[i] != b[i]:
            start = i
            last_diff = i
            i += 1
            while i < n and (i - last_diff) <= gap:
                if a[i] != b[i]:
                    last_diff = i
                i += 1
            regions.append((start, last_diff + 1))
        else:
            i += 1
    return regions

if __name__ == '__main__':
    a_path, b_path = sys.argv[1], sys.argv[2]
    gap = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    with open(a_path, 'rb') as f:
        a = f.read()
    with open(b_path, 'rb') as f:
        b = f.read()
    regions = diff_regions(a, b, gap)
    total_bytes = sum(e - s for s, e in regions)
    print(f"{len(regions)} regions, {total_bytes} bytes total differ "
          f"(gap-merge={gap}) out of {len(a)}")
    out = {'a': a_path, 'b': b_path, 'gap': gap, 'regions': regions,
           'total_bytes': total_bytes}
    with open(sys.argv[4], 'w') as f:
        json.dump(out, f)
    for s, e in regions[:40]:
        print(f"  0x{s:06X}-0x{e:06X}  ({e-s} bytes)")
    if len(regions) > 40:
        print(f"  ... and {len(regions)-40} more")
