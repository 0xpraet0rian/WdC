#!/usr/bin/env python3
"""
Parametric coded photogrammetry target generator (pure Python, no dependencies).

Layout (concentric, all fractions of the outer radius R):
    centre dot  -> white gap -> ring of N bit-sectors (black = 1, white = 0) -> white border
A through-hole in the middle (for a pin / nail) is optional.

Outputs per target (in --out):
    target_<code>_combined.stl   one solid; pause the print at --base-h to swap filament
    target_<code>_base.stl       light plate only   (multi-material / AMS: assign colour A)
    target_<code>_dark.stl       dark features only (multi-material / AMS: assign colour B)
    target_<code>.svg            flat preview / printable on paper too

Examples:
    python3 coded_target.py --bits 12 --code 0-9 --diameter 100
    python3 coded_target.py --bits 14 --code 42 --diameter 60 --hole 2.5
    python3 coded_target.py --bits 12 --list 20      # show first 20 valid codes
"""
import argparse
import math
import os
import struct

# ---- layout constants (fractions of outer radius R) -------------------------
DOT_R = 0.17      # black centre dot
RING_IN = 0.45    # inner edge of code ring
RING_OUT = 0.80   # outer edge of code ring
# beyond RING_OUT up to 1.0 is the white border


# ---- code handling ----------------------------------------------------------
def rotate(v, n, bits):
    mask = (1 << bits) - 1
    return ((v << n) | (v >> (bits - n))) & mask


def is_valid(v, bits):
    """Rotation-unique code: v is the minimum of its rotations AND aperiodic.
    This makes the ID independent of how the target is rotated in the photo."""
    if v == 0 or v == (1 << bits) - 1:
        return False
    rots = [rotate(v, i, bits) for i in range(1, bits)]
    return v < min(rots) if rots else False  # strictly less => aperiodic and minimal


def valid_codes(bits):
    return [v for v in range(1, (1 << bits) - 1) if is_valid(v, bits)]


def parse_codes(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


# ---- mesh helpers -----------------------------------------------------------
class Mesh:
    def __init__(self):
        self.tris = []

    def quad(self, a, b, c, d):  # CCW as seen from outside
        self.tris.append((a, b, c))
        self.tris.append((a, c, d))

    def annular_sector(self, r0, r1, a0, a1, z0, z1, seg_deg=2.0):
        """Closed solid: annular sector r0..r1, angles a0..a1 (rad), z0..z1."""
        full = abs((a1 - a0) - 2 * math.pi) < 1e-9
        n = max(2, int(math.ceil(math.degrees(a1 - a0) / seg_deg)))
        angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]

        def p(r, a, z):
            return (r * math.cos(a), r * math.sin(a), z)

        for i in range(n):
            s, e = angs[i], angs[i + 1]
            # top (+z) and bottom (-z)
            self.quad(p(r0, s, z1), p(r1, s, z1), p(r1, e, z1), p(r0, e, z1))
            self.quad(p(r0, s, z0), p(r0, e, z0), p(r1, e, z0), p(r1, s, z0))
            # outer wall
            self.quad(p(r1, s, z0), p(r1, e, z0), p(r1, e, z1), p(r1, s, z1))
            # inner wall (skip degenerate)
            if r0 > 1e-9:
                self.quad(p(r0, e, z0), p(r0, s, z0), p(r0, s, z1), p(r0, e, z1))
        if not full:
            # end caps
            for a, flip in ((a0, False), (a1, True)):
                q = [p(r0, a, z0), p(r1, a, z0), p(r1, a, z1), p(r0, a, z1)]
                if flip:
                    q = [q[0], q[3], q[2], q[1]]
                    self.quad(*q)
                else:
                    self.quad(*q)

    def extend(self, other):
        self.tris.extend(other.tris)

    def write_stl(self, path, name="target"):
        with open(path, "wb") as f:
            f.write(name.encode()[:80].ljust(80, b"\0"))
            f.write(struct.pack("<I", len(self.tris)))
            for a, b, c in self.tris:
                u = [b[i] - a[i] for i in range(3)]
                v = [c[i] - a[i] for i in range(3)]
                n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
                l = math.sqrt(sum(x * x for x in n)) or 1.0
                f.write(struct.pack("<12fH", *(n[0] / l, n[1] / l, n[2] / l), *a, *b, *c, 0))


# ---- build ------------------------------------------------------------------
def bits_of(code, bits):
    return [(code >> i) & 1 for i in range(bits)]  # bit i -> sector i, CCW from +x


def build(code, bits, diameter, base_h, dark_h, hole_d):
    R = diameter / 2.0
    rh = hole_d / 2.0
    if rh >= DOT_R * R:
        raise SystemExit("hole too large: must be smaller than the centre dot (%.2f mm dia)" % (2 * DOT_R * R))
    base, dark = Mesh(), Mesh()
    base.annular_sector(rh, R, 0, 2 * math.pi, 0, base_h)
    top = base_h
    dark.annular_sector(rh, DOT_R * R, 0, 2 * math.pi, top, top + dark_h)
    step = 2 * math.pi / bits
    b = bits_of(code, bits)
    # merge runs of consecutive 1s into one solid -> fewer faces, no internal seams
    i = 0
    while i < bits:
        if b[i]:
            j = i
            while j + 1 < bits and b[j + 1]:
                j += 1
            dark.annular_sector(RING_IN * R, RING_OUT * R, i * step, (j + 1) * step, top, top + dark_h)
            i = j + 1
        else:
            i += 1
    return base, dark


def svg(code, bits, diameter, hole_d):
    R = diameter / 2.0
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="%g %g %g %g">'
         % (diameter, diameter, -R, -R, diameter, diameter),
         '<circle r="%g" fill="#fff" stroke="#999" stroke-width="0.2"/>' % R,
         '<circle r="%g" fill="#000"/>' % (DOT_R * R)]
    step = 2 * math.pi / bits
    for i, v in enumerate(bits_of(code, bits)):
        if not v:
            continue
        a, e = i * step, (i + 1) * step
        r0, r1 = RING_IN * R, RING_OUT * R
        pt = lambda r, t: "%.4f %.4f" % (r * math.cos(t), -r * math.sin(t))  # flip y: SVG y is down
        s.append('<path d="M%s A%g %g 0 0 0 %s L%s A%g %g 0 0 1 %s Z" fill="#000"/>'
                 % (pt(r1, a), r1, r1, pt(r1, e), pt(r0, e), r0, r0, pt(r0, a)))
    if hole_d > 0:
        s.append('<circle r="%g" fill="#fff" stroke="#c00" stroke-width="0.15"/>' % (hole_d / 2))
    s.append("</svg>")
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bits", type=int, default=12, help="sectors in the code ring (12, 14, 16, 20 ...)")
    ap.add_argument("--code", default="0", help="index into the list of valid codes; e.g. 5 or 0-9 or 1,4,7")
    ap.add_argument("--diameter", type=float, default=100.0, help="outer diameter, mm")
    ap.add_argument("--base-h", type=float, default=1.2, help="plate thickness (light colour), mm")
    ap.add_argument("--dark-h", type=float, default=0.6, help="raised dark feature height, mm")
    ap.add_argument("--hole", type=float, default=2.0, help="centre pin hole diameter, mm (0 = none)")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--list", type=int, metavar="N", help="print the first N valid codes and exit")
    a = ap.parse_args()

    codes_all = valid_codes(a.bits)
    if a.list:
        print("%d-bit: %d usable codes" % (a.bits, len(codes_all)))
        for i, v in enumerate(codes_all[: a.list]):
            print("  code %-4d  %s" % (i, format(v, "0%db" % a.bits)))
        return
    os.makedirs(a.out, exist_ok=True)
    for c in parse_codes(a.code):
        if not 0 <= c < len(codes_all):
            raise SystemExit("code %d out of range 0..%d for %d bits" % (c, len(codes_all) - 1, a.bits))
        v = codes_all[c]
        base, dark = build(v, a.bits, a.diameter, a.base_h, a.dark_h, a.hole)
        both = Mesh(); both.extend(base); both.extend(dark)
        stem = os.path.join(a.out, "target_%db_%03d" % (a.bits, c))
        both.write_stl(stem + "_combined.stl")
        base.write_stl(stem + "_base.stl")
        dark.write_stl(stem + "_dark.stl")
        with open(stem + ".svg", "w") as f:
            f.write(svg(v, a.bits, a.diameter, a.hole))
        print("code %d  bits=%s  -> %s_*.stl/.svg  (filament swap at Z=%.2f mm)"
              % (c, format(v, "0%db" % a.bits), stem, a.base_h))


if __name__ == "__main__":
    main()
