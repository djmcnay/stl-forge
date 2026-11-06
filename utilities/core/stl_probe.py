#!/usr/bin/env python3
"""stl_probe.py - format-agnostic STL inspector for stl-forge verification.

Usage: stl_probe.py <file.stl> [--slice-z Z]

Prints format (ascii|binary), facet count, byte size and bbox for either
STL flavour. With --slice-z, reports the cross-section at that height
(segment count and endpoint y-range), auto-nudging 0.01 mm off any plane
that sits exactly on a tessellation vertex ring: a ring-aligned plane
makes strict crossing tests return nothing and falsely claim an internal
feature is absent. Stdlib only.
"""
import argparse
import re
import struct
import sys


def load(path):
    data = open(path, "rb").read()
    ascii_fmt = data[:5] == b"solid" and b"facet normal" in data[:4000]
    if ascii_fmt:
        verts = re.findall(
            rb"vertex\s+(-?[\d.eE+-]+)\s+(-?[\d.eE+-]+)\s+(-?[\d.eE+-]+)", data)
        tris = [[tuple(map(float, v)) for v in verts[i:i + 3]]
                for i in range(0, len(verts), 3)]
        return "ascii", len(tris), len(data), tris
    n = struct.unpack_from("<I", data, 80)[0]
    need = 84 + 50 * n
    if len(data) < need:
        raise SystemExit(f"truncated binary STL: {len(data)} bytes < {need}")
    tris, off = [], 84
    for _ in range(n):
        vals = struct.unpack_from("<9f", data, off + 12)
        tris.append([(vals[0], vals[1], vals[2]),
                     (vals[3], vals[4], vals[5]),
                     (vals[6], vals[7], vals[8])])
        off += 50
    return "binary", n, len(data), tris


def bbox(tris):
    pts = [p for t in tris for p in t]
    xs, ys, zs = zip(*pts)
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def slice_at(tris, z):
    ends = []
    for tri in tris:
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if (a[2] - z) * (b[2] - z) < 0:
                f = (z - a[2]) / (b[2] - a[2])
                ends.append((a[0] + f * (b[0] - a[0]),
                             a[1] + f * (b[1] - a[1])))
    return ends


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("--slice-z", type=float)
    args = ap.parse_args()

    fmt, n, size, tris = load(args.stl)
    x, y, z = bbox(tris)
    print(f"format {fmt} | facets {n} | bytes {size}")
    print(f"bbox x {x:.3f} y {y:.3f} z {z:.3f}")

    if args.slice_z is not None:
        ring = sorted({round(p[2], 6) for t in tris for p in t})
        zz, note = args.slice_z, ""
        if any(abs(v - args.slice_z) < 1e-6 for v in ring):
            zz = args.slice_z + 0.01
            note = f" (nudged off vertex ring at z={args.slice_z})"
        ends = slice_at(tris, zz)
        if ends:
            ys = [p[1] for p in ends]
            print(f"slice z={zz:.4f}{note}: segments {len(ends) // 2} "
                  f"| endpoints y {min(ys):.3f}..{max(ys):.3f}")
        else:
            print(f"slice z={zz:.4f}{note}: NO crossings - step 0.01 further "
                  "or corroborate with projection(cut=true) before claiming absence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
