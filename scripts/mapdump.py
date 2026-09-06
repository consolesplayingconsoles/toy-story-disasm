#!/usr/bin/env python3
"""Per-block Shannon entropy map of a ROM, to distinguish code from asset payload."""
import sys, math, json
from collections import Counter

def entropy(block):
    if not block:
        return 0.0
    c = Counter(block)
    n = len(block)
    return -sum((v / n) * math.log2(v / n) for v in c.values())

def mapdump(path, block_size=256):
    with open(path, 'rb') as f:
        data = f.read()
    blocks = []
    for off in range(0, len(data), block_size):
        chunk = data[off:off + block_size]
        blocks.append({'offset': off, 'entropy': round(entropy(chunk), 3)})
    return blocks

def summarize(blocks, trace_json=None):
    code_ranges = []
    if trace_json:
        with open(trace_json) as f:
            code_ranges = json.load(f)['code_ranges']

    def is_code(off, size):
        for s, e in code_ranges:
            if s < off + size and e > off:
                return True
        return False

    buckets = {}
    for b in blocks:
        lo = int(b['entropy'])
        buckets.setdefault(lo, [0, 0])
        buckets[lo][0] += 1
        if code_ranges and is_code(b['offset'], 256):
            buckets[lo][1] += 1
    return buckets

if __name__ == '__main__':
    path = sys.argv[1]
    trace_json = sys.argv[2] if len(sys.argv) > 2 else None
    blocks = mapdump(path)
    buckets = summarize(blocks, trace_json)
    total = len(blocks)
    print(f"{total} blocks of 256 bytes, entropy histogram (bucket=floor(H)):")
    for lo in sorted(buckets):
        n, coded = buckets[lo]
        pct = 100.0 * n / total
        print(f"  H in [{lo},{lo+1}):  {n:6d} blocks ({pct:5.1f}%)  code-covered: {coded:6d}")
    with open(sys.argv[1] + '.entropy.json', 'w') as f:
        json.dump(blocks, f)
