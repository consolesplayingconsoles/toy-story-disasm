#!/usr/bin/env python3
"""Rob Northen ProPack (RNC) methods 1 and 2, as used by Toy Story (MD).

Header (18 bytes): 'RNC', method, unpacked size (BE32), packed size (BE32),
unpacked CRC16, packed CRC16, leeway, chunk count. Method 2 is ported from the
game's own routine at $9DE (USA); method 1 is the standard Huffman variant.

    decode(rom, offset) -> bytes      (raises ValueError on CRC mismatch)

Command line (USA ROM: 264 blocks, 243 method 1 and 21 method 2, all CRC-checked):

    python3 tools/rnc.py <rom> list
    python3 tools/rnc.py <rom> extract <hex offset> <out file>
"""
import struct

_CRC = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0xA001 if _c & 1 else _c >> 1
    _CRC.append(_c)


def crc16(data):
    c = 0
    for b in data:
        c = _CRC[(c ^ b) & 0xFF] ^ (c >> 8)
    return c


def _lword(d, p):
    return d[p] | (d[p + 1] << 8) if p + 1 < len(d) else (d[p] if p < len(d) else 0)


class _Bits1:
    def __init__(self, d, p):
        self.d, self.p = d, p
        self.buf, self.cnt = _lword(d, p), 16

    def advance(self, n):
        self.buf >>= n
        self.cnt -= n
        if self.cnt < 16:
            self.p += 2
            self.buf |= _lword(self.d, self.p) << self.cnt
            self.cnt += 16

    def read(self, n):
        v = self.buf & ((1 << n) - 1)
        self.advance(n)
        return v

    def fix(self):
        self.cnt -= 16
        self.buf &= (1 << self.cnt) - 1
        self.buf |= _lword(self.d, self.p) << self.cnt
        self.cnt += 16


def _mirror(x, n):
    r = 0
    for _ in range(n):
        r = (r << 1) | (x & 1)
        x >>= 1
    return r


def _table(bs):
    num = bs.read(5)
    if not num:
        return []
    lens = [bs.read(4) for _ in range(num)]
    t, code = [], 0
    for L in range(1, max(lens + [1]) + 1):
        for j in range(num):
            if lens[j] == L:
                t.append((_mirror(code, L), L, j))
                code += 1
        code <<= 1
    return t


def _huf(t, bs):
    for code, L, val in t:
        if bs.buf & ((1 << L) - 1) == code:
            bs.advance(L)
            if val >= 2:
                v = 1 << (val - 1)
                return v | bs.read(val - 1)
            return val
    raise ValueError("bad huffman code")


def _m1(d, p, size):
    out = bytearray()
    bs = _Bits1(d, p)
    bs.advance(2)
    while len(out) < size:
        raw, dist, ln = _table(bs), _table(bs), _table(bs)
        count = bs.read(16)
        while True:
            n = _huf(raw, bs)
            if n:
                out += d[bs.p:bs.p + n]
                bs.p += n
                bs.fix()
            count -= 1
            if count <= 0:
                break
            off = _huf(dist, bs) + 1
            n = _huf(ln, bs) + 2
            for _ in range(n):
                out.append(out[-off])
    return bytes(out[:size])


class _Bits2:
    """8-bit buffer with a sentinel bit, MSB first (add.b d7,d7 / addx refill)."""
    def __init__(self, d, p):
        self.d, self.p = d, p
        b = d[p]; self.p += 1
        self.buf = ((b << 1) | 1) & 0xFF
        self.get()                                 # 2nd header bit (1st went with the load)

    def byte(self):
        b = self.d[self.p]; self.p += 1
        return b

    def get(self):
        self.buf <<= 1
        c = self.buf >> 8
        self.buf &= 0xFF
        if self.buf == 0:
            b = self.byte()
            c = b >> 7
            self.buf = ((b << 1) | 1) & 0xFF
        return c


def _m2(d, p, size):
    out = bytearray()
    bs = _Bits2(d, p)
    while True:
        if not bs.get():                           # 0 = literal byte
            out.append(bs.byte())
            continue
        n, off = 2, 0
        if not bs.get():
            n = (n << 1) | bs.get()
            if bs.get():
                n = ((n - 1) << 1) | bs.get()
                if n == 9:                         # literal run of (v+3)*4 bytes
                    v = 0
                    for _ in range(4):
                        v = (v << 1) | bs.get()
                    k = (v + 3) * 4
                    out += d[bs.p:bs.p + k]
                    bs.p += k
                    continue
        elif not bs.get():
            off = -1                               # length 2, byte offset only
        else:
            n = 3
            if bs.get():
                n = bs.byte()
                if n == 0:                         # chunk end / stream end
                    if bs.get():
                        continue
                    break
                n += 8
        if off == -1:
            off = 0
        elif bs.get():
            off = (off << 1) | bs.get()
            if bs.get():
                off = ((off << 1) | bs.get()) | 4
                if not bs.get():
                    off = (off << 1) | bs.get()
            elif off == 0:
                off = (1 << 1) | bs.get()
            off <<= 8
        off |= bs.byte()
        for _ in range(n):
            out.append(out[-(off + 1)])
    return bytes(out[:size])


def header(d, o):
    assert d[o:o + 3] == b"RNC", "no RNC header at %X" % o
    m = d[o + 3]
    u, pk = struct.unpack_from(">II", d, o + 4)
    ucrc, pcrc = struct.unpack_from(">HH", d, o + 12)
    return m, u, pk, ucrc, pcrc


def decode(d, o):
    m, u, pk, ucrc, pcrc = header(d, o)
    out = (_m1 if m == 1 else _m2)(d, o + 18, u)
    if len(out) != u or crc16(out) != ucrc:
        raise ValueError("RNC m%d at %X: size %d/%d crc %04X/%04X" % (m, o, len(out), u, crc16(out), ucrc))
    return out


def blocks(d):
    """(offset, method, unpacked size) of every block that decodes with a good CRC."""
    out, i = [], d.find(b"RNC")
    while i >= 0:
        if d[i + 3] in (1, 2):
            try:
                out.append((i, d[i + 3], len(decode(d, i))))
            except (ValueError, IndexError, AssertionError):
                pass                                   # an "RNC" that is not a header
        i = d.find(b"RNC", i + 1)
    return out


if __name__ == "__main__":
    import sys
    rom = open(sys.argv[1], "rb").read()
    if sys.argv[2] == "list":
        found = blocks(rom)
        for off, m, size in found:
            print("%06X  m%d  %7d bytes" % (off, m, size))
        print("%d blocks, %d bytes unpacked" % (len(found), sum(s for _, _, s in found)))
    elif sys.argv[2] == "extract":
        open(sys.argv[4], "wb").write(decode(rom, int(sys.argv[3], 16)))
