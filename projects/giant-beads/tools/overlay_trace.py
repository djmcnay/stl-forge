#!/usr/bin/env python3
"""Overlay a traced sketch on its reference photo and report the alignment error.

CPU only: uniform scale + translation are fitted by chamfer matching against the
reference's edge map, so the result is reproducible and does not touch the GPU.

Write the overlay into the project references folder, never into ~/Downloads.

Usage:
    python3 projects/giant-beads/tools/overlay_trace.py \
        projects/giant-beads/references/defender/side.png \
        SKETCH.png \
        projects/giant-beads/references/defender/side-sketch-overlay.png
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def load_reference(path):
    im = Image.open(path)
    if im.mode in ("P", "LA", "RGBA"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    return im


def edge_map(rgb, keep=0.10):
    a = np.asarray(rgb, float).mean(axis=2)
    gx = ndimage.sobel(a, axis=1)
    gy = ndimage.sobel(a, axis=0)
    mag = np.hypot(gx, gy)
    mag /= mag.max() or 1.0
    edges = mag > keep
    return edges, mag


def sketch_lines(path):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    a = np.asarray(Image.alpha_composite(bg, im).convert("L"))
    return a < 128


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def transform(lines, s, tx, ty, shape):
    h, w = shape
    ys, xs = np.nonzero(lines)
    X = xs * s + tx
    Y = ys * s + ty
    ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
    out = np.zeros(shape, bool)
    out[Y[ok].astype(int), X[ok].astype(int)] = True
    return out


def fit(ref_edges, lines, verbose=True):
    D = ndimage.distance_transform_edt(~ref_edges)
    h, w = ref_edges.shape
    x0, y0, x1, y1 = bbox(lines)
    rbx0, rby0, rbx1, rby1 = bbox(ref_edges)
    sw, sh = x1 - x0 + 1, y1 - y0 + 1
    rw, rh = rbx1 - rbx0 + 1, rby1 - rby0 + 1
    s0 = min(rw / sw, rh / sh)
    tx0 = rbx0 - x0 * s0
    ty0 = rby0 - y0 * s0
    ys, xs = np.nonzero(lines)
    sub = slice(None)
    if len(xs) > 12000:  # sample for speed; final score uses all pixels
        idx = np.linspace(0, len(xs) - 1, 12000).astype(int)
        ys, xs = ys[idx], xs[idx]

    def score(s, tx, ty):
        X = (xs * s + tx).astype(int)
        Y = (ys * s + ty).astype(int)
        ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
        return D[Y[ok], X[ok]].mean()

    s, tx, ty = s0, tx0, ty0
    for step_s, step_t in ((0.04, 12), (0.015, 4), (0.005, 1)):
        improved = True
        while improved:
            improved = False
            best = score(s, tx, ty)
            for ds in (-step_s, 0, step_s):
                for dx in (-step_t, 0, step_t):
                    for dy in (-step_t, 0, step_t):
                        if ds == dx == dy == 0:
                            continue
                        v = score(s + ds, tx + dx, ty + dy)
                        if v < best - 1e-6:
                            best, s, tx, ty = v, s + ds, tx + dx, ty + dy
                            improved = True
    if verbose:
        print(f"fit scale={s:.4f} tx={tx:.1f} ty={ty:.1f} mean_edge_dist={score(s, tx, ty):.2f}px")
    return s, tx, ty, score(s, tx, ty)


def render(ref_rgb, lines, s, tx, ty, out_path, colour=(255, 0, 128), zoom=2):
    w, h = ref_rgb.size
    placed = transform(lines, s, tx, ty, (h, w))
    thick = ndimage.binary_dilation(placed, np.ones((2, 2), bool))
    base = np.asarray(ref_rgb, float)
    # fade the photo so thin overlay lines stay readable
    base = 255 - (255 - base) * 0.55
    out = base.copy()
    out[thick] = colour
    img = Image.fromarray(out.astype("uint8"))
    if zoom != 1:
        img = img.resize((w * zoom, h * zoom), Image.LANCZOS)
    img.save(out_path)
    return thick.sum()


def agreement(ref_edges, placed, near_px=3):
    """Two-way agreement: sketch ink near a reference edge, and vice versa."""
    d_ref = ndimage.distance_transform_edt(~ref_edges)
    d_sk = ndimage.distance_transform_edt(~placed)
    on_sk = d_ref[placed] <= near_px
    on_ref = d_sk[ref_edges] <= near_px
    return (float(on_sk.mean()) if placed.any() else 0.0,
            float(on_ref.mean()) if ref_edges.any() else 0.0)


if __name__ == "__main__":
    ref_path, sketch_path, out_path = sys.argv[1:4]
    ref = load_reference(ref_path)
    edges, _ = edge_map(ref)
    lines = sketch_lines(sketch_path)
    s, tx, ty, err = fit(edges, lines)
    ink = render(ref, lines, s, tx, ty, out_path)
    placed = transform(lines, s, tx, ty, ref.size[::-1])
    a, b = agreement(edges, placed)
    print(f"overlay={out_path} ink_px={ink}")
    print(f"report: scale={s:.3f} offset=({tx:.0f},{ty:.0f}) mean_dist={err:.2f}px")
    print(f"agreement within 3px: sketch->ref {a*100:.1f}%  ref->sketch {b*100:.1f}%")
