"""Measure a bead STL: shells, degenerate facets, and flat faces by height.

Written because the rear bead was handed over five times with a fault that a
measurement would have caught and no render ever did: a flat shelf running the
length of each wheel, and a saucer round every lamp.  A render shows shading; a
flat face at a grazing angle is invisible, and a shallow one is exaggerated.

Run it on the file you are about to hand over - not on a template, and not on
the output of a different parameter set.

    python3 tools/stl_check.py bead.stl
    python3 tools/stl_check.py bead.stl --band 56.9:57.1 --band 59.9:60.1
"""
import argparse
import struct
import sys

import numpy as np

WELD_MM = 0.02          # vertices closer than this are the same vertex
DEGENERATE_MM2 = 1e-6   # a facet with less area than this is a sliver
FLAT_COS = 0.95         # |normal.z| above this counts as a horizontal face


def load(path):
    """Triangle normals and vertices from a binary STL."""
    data = open(path, "rb").read()
    if len(data) < 84:
        raise SystemExit("%s: too short to be a binary STL" % path)
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise SystemExit("%s: not a binary STL (ascii? %d facets expected)"
                         % (path, count))
    raw = np.frombuffer(data, dtype=np.uint8, count=count * 50, offset=84)
    raw = raw.reshape(count, 50)
    face = np.frombuffer(raw[:, :48].tobytes(), dtype="<f4").reshape(count, 4, 3)
    return face[:, 0, :].astype(float), face[:, 1:4, :].astype(float)


def face_normals(verts):
    """Unit normals from the geometry.

    The normals stored in an STL are advisory - some writers leave them zero -
    so they are recomputed here.  Everything this tool decides rests on them.
    """
    n = np.cross(verts[:, 1] - verts[:, 0], verts[:, 2] - verts[:, 0])
    length = np.linalg.norm(n, axis=1, keepdims=True)
    return np.divide(n, np.where(length > 0, length, 1.0))


def areas(verts):
    return 0.5 * np.linalg.norm(
        np.cross(verts[:, 1] - verts[:, 0], verts[:, 2] - verts[:, 0]), axis=1)


def shells(verts):
    """How many separate shells, and the welded vertex count of the largest."""
    key = np.round(verts.reshape(-1, 3) / WELD_MM).astype(np.int64)
    uniq, inverse = np.unique(key, axis=0, return_inverse=True)
    tris = inverse.reshape(-1, 3)
    parent = np.arange(len(uniq))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in tris:
        ra, rb, rc = find(a), find(b), find(c)
        if ra != rb:
            parent[ra] = rb
        rc = find(c)
        rb = find(b)
        if rb != rc:
            parent[rb] = rc
    roots = np.array([find(i) for i in range(len(uniq))])
    _, counts = np.unique(roots, return_counts=True)
    return len(counts), int(counts.max())


def horizontal(normals, verts, area):
    """Total, largest and heights of the horizontal faces."""
    flat = np.abs(normals[:, 2]) > FLAT_COS
    if not flat.any():
        return dict(area=0.0, largest=0.0, heights=[])
    z = verts[:, :, 2].mean(axis=1)[flat]
    a = area[flat]
    return dict(area=float(a.sum()), largest=float(a.max()),
                heights=np.round(np.unique(z), 2).tolist())


def band(normals, verts, area, low, high):
    """Horizontal faces whose centroid sits between two heights."""
    z = verts[:, :, 2].mean(axis=1)
    sel = (np.abs(normals[:, 2]) > FLAT_COS) & (z > low) & (z < high)
    if not sel.any():
        return dict(faces=0, area=0.0, largest=0.0)
    return dict(faces=int(sel.sum()), area=float(area[sel].sum()),
                largest=float(area[sel].max()))


def report(path, bands=()):
    _stored, verts = load(path)
    normals = face_normals(verts)
    area = areas(verts)
    lo = verts.reshape(-1, 3).min(axis=0)
    hi = verts.reshape(-1, 3).max(axis=0)
    count, largest = shells(verts)
    out = dict(
        facets=len(area),
        bbox=[round(float(v), 2) for v in (hi - lo)],
        size=[round(float(v), 2) for v in hi],
        shells=count,
        largest_shell=largest,
        degenerate=int((area < DEGENERATE_MM2).sum()),
        flat=horizontal(normals, verts, area),
        bands=[band(normals, verts, area, *b) for b in bands],
    )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl")
    ap.add_argument("--band", action="append", default=[],
                    metavar="LOW:HIGH",
                    help="report horizontal faces between two heights, mm")
    args = ap.parse_args()
    bands = []
    for text in args.band:
        low, _, high = text.partition(":")
        bands.append((float(low), float(high)))
    res = report(args.stl, bands)
    print("%s" % args.stl)
    print("  facets        %d" % res["facets"])
    print("  size          %.2f x %.2f x %.2f mm" % tuple(res["bbox"]))
    print("  shells        %d  (largest %d welded vertices)"
          % (res["shells"], res["largest_shell"]))
    print("  degenerate    %d" % res["degenerate"])
    print("  flat faces    %.1f mm2 total, largest %.2f mm2"
          % (res["flat"]["area"], res["flat"]["largest"]))
    for (low, high), b in zip(bands, res["bands"]):
        print("  band %6.2f..%-6.2f %4d faces, %7.2f mm2, largest %5.2f mm2"
              % (low, high, b["faces"], b["area"], b["largest"]))
    if res["shells"] != 1:
        print("  FAIL: more than one shell - something is floating")
        return 1
    if res["degenerate"]:
        print("  WARN: %d degenerate facets" % res["degenerate"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
