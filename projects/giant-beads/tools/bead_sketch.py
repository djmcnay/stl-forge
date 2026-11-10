#!/usr/bin/env python3
"""The clean bead sketch for a view: one stroke per feature, nothing dead.

This is the drawing the SCAD template will be built from, not another review
render.  It is derived from the principal's trace:

* the silhouette is taken straight out of the trace ink - the outline strokes
  are closed, filled and re-contoured, so the shape is the principal's even
  where the trace had gaps or doubled lines;
* the internal detail is rebuilt as single strokes from the positions measured
  off the trace (the trace draws most panel edges twice, ~1-1.5 mm apart on the
  bead, which would print as one mushy groove);
* everything the principal deleted or omitted is simply absent.

`--json` output (`<stem>-bead-sketch.json`) is the build input for the SCAD
template: one closed silhouette polygon plus the parts, each tagged with its
level.  The `<stem>-parts.json` written by `part_map.py` is the ink-exact
reference and is not used to build anything.

Usage (from the repo root):
    python3 projects/giant-beads/tools/bead_sketch.py
    python3 projects/giant-beads/tools/bead_sketch.py --view rear --check
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import part_map as pm                       # noqa: E402
import viewdata                             # noqa: E402
from levels import LEVEL_COLOUR, LEVEL_HEAD, LEVEL_ORDER, STROKE   # noqa: E402
from trace_sketch import contours, rdp      # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
PROJECT = os.path.join(REPO, "projects", "giant-beads")

MARGIN = 40
KEY_W = 620

DEFAULT_VIEW = "rear"

# Published by `use_view`, so the drawing code below carries no view numbers.
VIEW = None
MM_PER_PX = None
OUT_PNG = OUT_JSON = OUT_OVERLAY = None


def use_view(name):
    """Bind a view's data and its output paths into this module."""
    global VIEW, MM_PER_PX, OUT_PNG, OUT_JSON, OUT_OVERLAY
    VIEW = viewdata.load(name)
    viewdata.bind(globals(), VIEW)
    outs = viewdata.out_paths(VIEW)
    OUT_PNG, OUT_JSON = outs["sketch_png"], outs["sketch_json"]
    OUT_OVERLAY = outs["overlay_png"]
    # provisional; render() recomputes it from the finished silhouette span
    MM_PER_PX = BEAD_WIDTH_MM / (BODY_RIGHT - BODY_LEFT)
    return VIEW


use_view(DEFAULT_VIEW)


def disc(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def drop_spikes(pts, min_len=11.0, min_angle=55.0):
    """Remove one-vertex notches left by gaps in the traced outline."""
    out = [list(p) for p in pts]
    changed = True
    while changed and len(out) > 8:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            v1 = (a[0] - b[0], a[1] - b[1])
            v2 = (c[0] - b[0], c[1] - b[1])
            l1 = math.hypot(*v1)
            l2 = math.hypot(*v2)
            if min(l1, l2) > min_len:
                continue
            cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / max(l1 * l2, 1e-6)
            ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
            if ang < min_angle:
                del out[i]
                changed = True
                break
    return out


def smooth(pts, passes=2, keep=0.45):
    out = [list(p) for p in pts]
    for _ in range(passes):
        nxt = []
        n = len(out)
        for i in range(n):
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            nxt.append([b[0] + keep * ((a[0] + c[0]) / 2 - b[0]),
                        b[1] + keep * ((a[1] + c[1]) / 2 - b[1])])
        out = nxt
    return out


# The trace's wheel-arch flares are drawn as arcs that run off the canvas, so
# they enclose nothing on their own.  These wedges fill the area between each
# arch, the hip line the principal asked to close, and the body flank, so the
# flare becomes part of the silhouette instead of a dangling line.
def silhouette_polygon():
    """Close, fill and re-contour the outline strokes of the trace."""
    from PIL import Image as _Image
    ink, label, _ = pm.assign()
    ids = [i for i, p in enumerate(pm.PARTS) if p["role"] == "silhouette"]
    sil = np.isin(label, ids) & ink
    wedges = _Image.new("L", (ART_W, ART_H), 0)
    wd = ImageDraw.Draw(wedges)
    for poly in FLARE_WEDGES:
        wd.polygon([tuple(pt) for pt in poly], fill=255)
    sil = sil[:ART_H, :ART_W] | (np.asarray(wedges) > 0)
    filled = ndimage.binary_fill_holes(ndimage.binary_closing(sil, disc(9)))
    body = ndimage.binary_erosion(filled, disc(3))
    polys = sorted(contours(body), key=len, reverse=True)
    pts = rdp(polys[0], 1.2)
    pts = drop_spikes(pts)
    pts = smooth(pts, passes=1, keep=0.35)
    pts = rdp(pts, 0.8)
    pts = drop_spikes(pts, min_len=9.0, min_angle=50.0)
    return [[round(float(x), 1), round(float(y), 1)] for x, y in pts]


# ---- the clean part model ---------------------------------------------
# `build_parts()` lives in the view module: what the bead carries is a property
# of the elevation, and it is the model the SCAD template is built from.

# ---- drawing -----------------------------------------------------------
def round_rect_points(box, radii, seg=18):
    x0, y0, x1, y1 = box
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * 4
    tl, tr, br, bl = radii
    lim = min((x1 - x0) / 2, (y1 - y0) / 2)
    tl, tr, br, bl = [min(v, lim) for v in (tl, tr, br, bl)]
    pts = []
    for cx, cy, a0, r in [(x1 - tr, y0 + tr, -90, tr), (x1 - br, y1 - br, 0, br),
                          (x0 + bl, y1 - bl, 90, bl), (x0 + tl, y0 + tl, 180, tl)]:
        if r <= 0.01:
            pts.append((cx, cy))
            continue
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_part(c, part, sil, halo=False):
    """One part, optionally with a white halo so it reads over the photograph."""
    w = STROKE[part["level"]]
    if halo:
        _draw_geometry(c, part, sil, "#FFFFFF", w + 3.4)
    _draw_geometry(c, part, sil, LEVEL_COLOUR[part["level"]], w)


def _draw_geometry(c, part, sil, colour, w):
    kind = part["kind"]
    if kind == "none":
        return
    if kind == "polygon":
        c.path(sil, colour, w, closed=True)
    elif kind in ("line", "polyline"):
        c.path(part["points"], colour, w)
    elif kind == "lines":
        for ln in part["lines"]:
            c.path(ln, colour, w)
    elif kind == "round_rect":
        c.path(round_rect_points(part["box"], part["radius"]), colour, w,
               closed=True)
    elif kind == "circle":
        c.circle(part["c"], part["r"], colour, w)
    elif kind == "circles":
        for ctr, r in zip(part["centres"], part["radii"]):
            c.circle(ctr, r, colour, w)
    elif kind == "ring_array":
        for i in range(part["count"]):
            a = math.radians(part["start_deg"] + 360.0 * i / part["count"])
            ctr = (part["c"][0] + part["ring"] * math.cos(a),
                   part["c"][1] + part["ring"] * math.sin(a))
            c.circle(ctr, part["radius"], colour, w)
    else:
        raise ValueError(kind)


def fit_report(parts, sil):
    """How close is the clean sketch to the trace ink it came from?"""
    ink = pm.reference_mask()[:ART_H, :ART_W]
    dist = ndimage.distance_transform_edt(~ink)
    c = pm.Canvas(ART_W, ART_H, ss=1)
    for p in parts:
        draw_part(c, p, sil)
    mine = np.asarray(c.img.convert("L")) < 250
    d = dist[mine]
    print("clean sketch vs trace ink")
    print("  silhouette  : %d points" % len(sil))
    print("  sketch ink  : %6d px" % mine.sum())
    print("  to trace    : mean %.2f px (%.3f mm), 95%% %.2f px, max %.1f px"
          % (d.mean(), d.mean() * MM_PER_PX, np.percentile(d, 95), d.max()))
    return d


def draw_key(c, lx, ty, parts, title, lines):
    c.text((lx, ty), title, 28, "#111111", bold=True)
    ty += 40
    for line in lines:
        c.text((lx, ty), line, 14, "#555555")
        ty += 19
    ty += 16
    f = pm.load_font(15 * c.ss, False)
    id_w = max(f.getlength(p["id"]) for p in parts) / c.ss + 18
    for level in LEVEL_ORDER:
        group = [p for p in parts if p["level"] == level]
        if not group:
            continue
        chip = pm.Canvas(26, 26, ss=2)
        chip.rect([4, 4, 22, 22], LEVEL_COLOUR[level], 4.0)
        c.img.paste(chip.img.resize((26, 26), Image.LANCZOS),
                    (int(lx * c.ss), int((ty + 2) * c.ss)))
        c.text((lx + 36, ty), LEVEL_HEAD[level], 16, "#222222", bold=True)
        ty += 32
        for p in group:
            c.text((lx + 36, ty + 3), p["id"], 15, LEVEL_COLOUR[level])
            c.text((lx + 36 + id_w, ty + 3), p["name"], 15, "#111111")
            ty += 32
        ty += 10


def render(out_png=None, out_json=None, out_overlay=None):
    global MM_PER_PX
    out_png = out_png or OUT_PNG
    out_json = out_json or OUT_JSON
    out_overlay = out_overlay or OUT_OVERLAY
    parts = build_parts()
    sil = silhouette_polygon()
    span = max(p[0] for p in sil) - min(p[0] for p in sil)
    MM_PER_PX = BEAD_WIDTH_MM / span
    width = MARGIN + ART_W + MARGIN + KEY_W + MARGIN

    # ---- the sketch on its own ----
    c = pm.Canvas(width, max(ART_H + 2 * MARGIN, key_height() + 2 * MARGIN), ss=2)
    for level in LEVEL_ORDER:
        for p in parts:
            if p["level"] == level:
                draw_part(c, p, sil)
    draw_key(c, MARGIN + ART_W + MARGIN, MARGIN, parts,
             TITLE + " - BEAD SKETCH",
             ["one stroke per feature, no doubled lines",
              "deleted and omitted parts are simply absent",
              "%g mm bead  |  1 px = %.4f mm" % (BEAD_WIDTH_MM, MM_PER_PX)])
    c.save(out_png)

    # ---- the same lines over the original photograph ----
    # The trace frame was built with the photo at 2x, so the sketch coordinates
    # land on the photo without any fitting.
    o = pm.Canvas(width, PHOTO_H + 2 * MARGIN, ss=2)
    photo = Image.open(PHOTO).convert("RGB").resize((ART_W * 2, PHOTO_H * 2),
                                                   Image.LANCZOS)
    faded = 255 - (255 - np.asarray(photo, float)) * 0.40
    o.img.paste(Image.fromarray(faded.astype("uint8")), (MARGIN * 2, MARGIN * 2))
    for level in LEVEL_ORDER:
        for p in parts:
            if p["level"] == level:
                draw_part(o, p, sil, halo=True)
    draw_key(o, MARGIN + ART_W + MARGIN, MARGIN, parts,
             "SKETCH OVER THE PHOTOGRAPH",
             ["same lines as %s" % os.path.basename(OUT_PNG),
              "no fitting: the photo sits in the trace frame at 2x",
              "%g mm bead  |  1 px = %.4f mm" % (BEAD_WIDTH_MM, MM_PER_PX)])
    o.save(out_overlay)

    with open(out_json, "w") as fh:
        fh.write(pm.dump_json(dict(
            note="clean bead sketch: single strokes, derived from %s; "
                 "overlay pixels, origin top-left, y down"
                 % os.path.basename(OVERLAY),
            bead_width_mm=BEAD_WIDTH_MM,
            mm_per_px=round(MM_PER_PX, 5),
            body_centre_x=CX,
            silhouette=sil,
            parts=[dict(id=p["id"], name=p["name"], level=p["level"],
                        colour=LEVEL_COLOUR[p["level"]],
                        **{k: v for k, v in p.items()
                           if k not in ("id", "name", "level")})
                   for p in parts],
        ), indent=1))
    print("wrote %s" % os.path.relpath(out_png, REPO))
    print("wrote %s" % os.path.relpath(out_overlay, REPO))
    print("wrote %s" % os.path.relpath(out_json, REPO))
    fit_report(parts, sil)


def key_height():
    h = 40 + 3 * 19 + 16
    for level in LEVEL_ORDER:
        n = len([p for p in build_parts() if p["level"] == level])
        if n:
            h += 32 + 32 * n + 10
    return h


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only")
    ap.add_argument("--view", default=DEFAULT_VIEW, help=", ".join(viewdata.available()))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.view != DEFAULT_VIEW:
        use_view(args.view)
    if args.check:
        parts = build_parts()
        fit_report(parts, silhouette_polygon())
        return
    render(out_png=args.out)


if __name__ == "__main__":
    main()
