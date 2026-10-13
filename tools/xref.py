#!/usr/bin/env python3
"""What points at address X: checks trace edges plus a raw absolute-long scan."""
import sys, json, struct

def xref(rom, trace, addr):
    hits = {'call_edges': [], 'jump_edges': [], 'abs32_literals': []}
    for src, dst in trace.get('edges_call', []):
        if dst == addr:
            hits['call_edges'].append(src)
    for src, dst in trace.get('edges_jump', []):
        if dst == addr:
            hits['jump_edges'].append(src)
    needle = struct.pack('>I', addr)
    i = 0
    while True:
        i = rom.find(needle, i)
        if i == -1:
            break
        hits['abs32_literals'].append(i)
        i += 1
    return hits

if __name__ == '__main__':
    rom_path, trace_path = sys.argv[1], sys.argv[2]
    with open(rom_path, 'rb') as f:
        rom = f.read()
    with open(trace_path) as f:
        trace = json.load(f)
    for a in sys.argv[3:]:
        addr = int(a, 16)
        h = xref(rom, trace, addr)
        print(f"=== xrefs to 0x{addr:X} ===")
        for k, v in h.items():
            if v:
                print(f"  {k}: {[hex(x) for x in v[:20]]}{' ...' if len(v)>20 else ''} (n={len(v)})")
        if not any(h.values()):
            print("  (none found)")
