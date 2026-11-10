"""Trace a generated line drawing into a 1-bit PNG and an even-odd SVG.

Contours are traced on pixel cracks (exact, always closed) then simplified with
Douglas-Peucker, so a Fusion 360 SVG import gets clean lines instead of a
pixel staircase.

Usage:
    python3 projects/giant-beads/tools/trace_sketch.py IN.png OUT-1bit.png OUT.svg [tol] [threshold]

Default tolerance is 0.5, which keeps a pixel-exact ink match (IoU 1.0) for
2 px strokes; raising it starts eating the line weight.

Write outputs beside the source sketches in
`projects/giant-beads/references/defender/`, not into ~/Downloads.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def binarise(path, thresh=200, min_area=4):
    a = np.asarray(Image.open(path).convert("L"))
    mask = a < thresh
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes >= min_area
        mask = keep[lab]
    return mask, (a.shape[1], a.shape[0])


def contours(mask):
    """Closed polygons along pixel cracks, dark on one consistent side."""
    h, w = mask.shape
    m = np.zeros((h + 2, w + 2), bool)
    m[1:-1, 1:-1] = mask
    out = {}
    ys, xs = np.nonzero(m[1:-1, 1:-1])
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        y, x = y0 + 1, x0 + 1
        if not m[y - 1, x]:
            out.setdefault((x + 1, y), []).append((x, y))
        if not m[y + 1, x]:
            out.setdefault((x, y + 1), []).append((x + 1, y + 1))
        if not m[y, x - 1]:
            out.setdefault((x, y), []).append((x, y + 1))
        if not m[y, x + 1]:
            out.setdefault((x + 1, y + 1), []).append((x + 1, y))
    polys = []
    while out:
        start = next(iter(out))
        poly = [start]
        cur = start
        while True:
            nxts = out.get(cur)
            if not nxts:
                break
            nxt = nxts.pop()
            if not nxts:
                del out[cur]
            if nxt == start:
                break
            poly.append(nxt)
            cur = nxt
        if len(poly) > 2:
            polys.append([(float(x - 1), float(y - 1)) for x, y in poly])
    return polys


def rdp(points, tol):
    if len(points) < 3:
        return points
    pts = np.asarray(points, float)
    closed = np.allclose(pts[0], pts[-1])
    if not closed:
        pts = np.vstack([pts, pts[0]])
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        L = float(np.hypot(*ab))
        seg = pts[i + 1:j] - a
        if L == 0.0:
            d = np.hypot(seg[:, 0], seg[:, 1])
        else:
            d = np.abs(ab[0] * seg[:, 1] - ab[1] * seg[:, 0]) / L
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    out = [tuple(p) for p in pts[keep]]
    return out


def to_svg(polys, path, w, h, tol):
    ds = []
    for poly in polys:
        pts = rdp(poly, tol)
        if len(pts) < 3:
            continue
        ds.append("M" + " ".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z")
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d">\n<rect width="%d" height="%d" fill="#ffffff"/>\n'
           '<g fill="#000000" fill-rule="evenodd">\n%s\n</g>\n</svg>\n'
           % (w, h, w, h, w, h, "\n".join(f'<path d="{d}"/>' for d in ds)))
    open(path, "w", encoding="utf-8").write(svg)
    return len(ds)


def rasterise(polys, w, h):
    """Even-odd scanline fill; returns a boolean ink mask."""
    ys1, ys2, xs1, xs2 = [], [], [], []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if y1 == y2:
                continue
            ys1.append(y1); ys2.append(y2); xs1.append(x1); xs2.append(x2)
    out = np.zeros((h, w), bool)
    if not ys1:
        return out
    y1 = np.asarray(ys1); y2 = np.asarray(ys2)
    x1 = np.asarray(xs1); x2 = np.asarray(xs2)
    ymin, ymax = min(y1.min(), y2.min()), max(y1.max(), y2.max())
    for yy in range(max(0, int(np.floor(ymin))), min(h, int(np.ceil(ymax)) + 1)):
        sy = yy + 0.5
        act = ((y1 <= sy) & (y2 > sy)) | ((y2 <= sy) & (y1 > sy))
        if not act.any():
            continue
        t = (sy - y1[act]) / (y2[act] - y1[act])
        xc = np.sort(x1[act] + t * (x2[act] - x1[act]))
        for i in range(0, len(xc) - 1, 2):
            a = int(np.ceil(xc[i] - 0.5))
            b = int(np.floor(xc[i + 1] - 0.5))
            if b >= a:
                out[yy, max(0, a):min(w, b + 1)] = True
    return out


def iou(polys, mask):
    got = rasterise(polys, mask.shape[1], mask.shape[0])
    u = (got | mask).sum()
    return float((got & mask).sum() / u) if u else 1.0


if __name__ == "__main__":
    src, out_png, out_svg = sys.argv[1:4]
    tol = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    thresh = int(sys.argv[5]) if len(sys.argv) > 5 else 200
    mask, (w, h) = binarise(src, thresh)
    polys = contours(mask)
    ink = rasterise(polys, w, h)
    Image.fromarray(np.where(ink, 0, 255).astype("uint8"), "L").convert("1").save(out_png)
    n = to_svg(polys, out_svg, w, h, tol)
    print(f"contours={len(polys)} paths={n} iou={iou(polys, mask):.4f} "
          f"ink={mask.mean():.4f} -> {out_png} {out_svg}")
