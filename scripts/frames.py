#!/usr/bin/env python3
"""Toy Story (Mega Drive, USA) sprite frames.

A frame is a header [w0 = 6 + 6*count][count][size in words] (the size is what
the DMA queue moves), then `count` 6-byte pieces
[size = (w-1)<<2 | (h-1)][first tile][x][y][x when flipped][y when flipped], then
the tiles at frame + w0. Tiles in a piece are column-major; a piece's first tile
is the running sum of the earlier pieces' sizes. Objects store their tiles raw.
The player (Woody, bank $82784: a table of longs, top byte = literal offset/2,
low 24 bits = frame) stores them run-length coded (the routine at $1162): command bytes
<0 zero-fill 64-(b&$7F)/2 longs, >0 copy 65-(b&$7F) longs from the literal data
(word-aligned after the commands), 0 ends.

    frame(rom, address) -> (tiles, pieces)
    pixels(tiles, pieces) -> {(x, y): colour index}
    palette(rom, address) -> 16 RGB tuples

Command line:

    python3 scripts/frames.py <rom> <hex frame address>              pieces
    python3 scripts/frames.py <rom> <hex frame address> <hex palette> <out.png>
"""
import struct, sys, zlib


def _rle(d, cmd):
    n = 0
    while d[cmd + n]:
        n += 1
    lit = cmd + 2 * ((n + 2) // 2)
    out, p = bytearray(), cmd
    while d[p]:
        b = d[p]
        p += 1
        if b & 0x80:
            out += bytes(4 * (64 - ((b & 0x7F) >> 1)))
        else:
            k = 65 - (b & 0x7F)
            out += d[lit:lit + 4 * k]
            lit += 4 * k
    return bytes(out)


def frame(d, f):
    w0, count, size = struct.unpack_from(">HHH", d, f)
    assert w0 == 6 + 6 * count, "no frame header at %X" % f
    pieces = [d[f + 6 + 6 * i:f + 12 + 6 * i] for i in range(count)]
    tiles = d[f + w0:f + w0 + size * 2]
    try:
        packed = _rle(d, f + w0)
        if len(packed) == size * 2:
            tiles = packed
    except IndexError:
        pass
    assert sum((((p[0] >> 2) & 3) + 1) * ((p[0] & 3) + 1) for p in pieces) * 16 == size, "piece sizes"
    return tiles, pieces


def pixels(tiles, pieces):
    px = {}
    for p in pieces:
        w, h, t0, x, y = ((p[0] >> 2) & 3) + 1, (p[0] & 3) + 1, p[1], p[2], p[3]
        for c in range(w):
            for r in range(h):
                tile = tiles[(t0 + c * h + r) * 32:(t0 + c * h + r + 1) * 32]
                for py in range(8):
                    for pxl in range(8):
                        v = (tile[py * 4 + pxl // 2] >> (4 if pxl % 2 == 0 else 0)) & 15
                        if v:
                            px[(x + c * 8 + pxl, y + r * 8 + py)] = v
    return px


def palette(d, a):
    w = [struct.unpack_from(">H", d, a + 2 * k)[0] for k in range(16)]
    return [(((v >> 1) & 7) * 36, ((v >> 5) & 7) * 36, ((v >> 9) & 7) * 36) for v in w]


def _png(path, px, pal):
    xs, ys = [x for x, _ in px], [y for _, y in px]
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    raw = b"".join(b"\0" + b"".join(bytes(pal[px[(x0 + x, y0 + y)]] if (x0 + x, y0 + y) in px else (0, 0, 0))
                                     for x in range(w)) for y in range(h))
    chunk = lambda t, q: struct.pack(">I", len(q)) + t + q + struct.pack(">I", zlib.crc32(t + q))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    tiles, pieces = frame(rom, int(sys.argv[2], 16))
    if len(sys.argv) > 4:
        _png(sys.argv[4], pixels(tiles, pieces), palette(rom, int(sys.argv[3], 16)))
    else:
        for p in pieces:
            print("%dx%d tile %d at (%d, %d)" % (((p[0] >> 2) & 3) + 1, (p[0] & 3) + 1, p[1], p[2], p[3]))
        print("%d tiles" % (len(tiles) // 32))
