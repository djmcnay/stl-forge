#!/usr/bin/env python3
"""Colour an approved trace by part - no redrawing, for any view.

The principal's trace is the authority for the silhouette, so this tool never
draws a replacement outline.  It takes the pink ink from the view's
`OVERLAY` exactly as supplied, decides which part every ink pixel belongs to,
and repaints it in that part's colour.  The resulting PNG is pixel-for-pixel the
approved trace, only recoloured.

The geometry in `PARTS` is used for one thing only: deciding which pixels belong
to which part.  It is a proximity probe, not the drawing.

For CAD the ink is also vectorised per part (closed loops, even-odd fill) and
written to `<stem>-parts.json`, so the template gets the drawn shape rather than
a second-hand approximation of it.  That file is a reference, not the build
input - `bead_sketch.py` writes the one the SCAD uses.

Usage (from the repo root):
    python3 projects/giant-beads/tools/part_map.py
    python3 projects/giant-beads/tools/part_map.py --view rear --check -v
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viewdata                                  # noqa: E402
from levels import (ROLE_COLOUR, ROLE_DOTTED, ROLE_HEAD,      # noqa: E402
                    ROLE_ORDER)
from trace_sketch import contours, rdp            # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
PROJECT = os.path.join(REPO, "projects", "giant-beads")

FONT_DIR = "/System/Library/Fonts/Supplemental"

DEFAULT_VIEW = "rear"

# Everything view-specific is published as a module global by `bind`, so the
# functions below read exactly as they did when the numbers were inline.
VIEW = None
MM_PER_PX = None
OUT_PNG = OUT_JSON = None


def use_view(name):
    """Bind a view's data and its output paths into this module."""
    global VIEW, MM_PER_PX, OUT_PNG, OUT_JSON
    VIEW = viewdata.load(name)
    viewdata.bind(globals(), VIEW)
    outs = viewdata.out_paths(VIEW)
    OUT_PNG, OUT_JSON = outs["parts_png"], outs["parts_json"]
    MM_PER_PX = BEAD_WIDTH_MM / (BODY_RIGHT - BODY_LEFT)
    return VIEW


use_view(DEFAULT_VIEW)


# ---- drawing helpers (legend + probe raster only) ----------------------
class Canvas:
    def __init__(self, width, height, ss=2):
        self.ss = ss
        self.img = Image.new("RGB", (width * ss, height * ss), "white")
        self.d = ImageDraw.Draw(self.img)

    def _p(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def path(self, pts, colour, width, dotted=False, closed=False):
        pts = list(pts) + ([pts[0]] if closed else [])
        w = max(1, int(round(width * self.ss)))
        if not dotted:
            self.d.line(self._p(pts), fill=colour, width=w, joint="curve")
            r = w / 2.0
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse([x * self.ss - r, y * self.ss - r,
                                x * self.ss + r, y * self.ss + r], fill=colour)
            return
        on, off = 5.0, 5.0
        walk = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if seg == 0:
                continue
            t = 0.0
            while t < seg:
                phase = walk % (on + off)
                if phase < on:
                    step = min(on - phase, seg - t)
                    ax = x0 + (x1 - x0) * (t / seg)
                    ay = y0 + (y1 - y0) * (t / seg)
                    bx = x0 + (x1 - x0) * ((t + step) / seg)
                    by = y0 + (y1 - y0) * ((t + step) / seg)
                    self.d.line(self._p([(ax, ay), (bx, by)]),
                                fill=colour, width=w)
                else:
                    step = min(on + off - phase, seg - t)
                t += step
                walk += step

    def rect(self, box, colour, width, dotted=False):
        x0, y0, x1, y1 = box
        self.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], colour, width,
                  dotted, closed=False)
        self.path([(x0, y1), (x0, y0)], colour, width, dotted)

    def rounded_rect(self, box, radius, colour, width, dotted=False):
        radii = radius if isinstance(radius, (list, tuple)) else [radius] * 4
        self.path(rounded_rect_points(box, radii), colour, width, dotted, True)

    def filled(self, c, r, colour):
        cx, cy = c[0] * self.ss, c[1] * self.ss
        rr = r * self.ss
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=colour)

    def circle(self, c, r, colour, width, dotted=False):
        if dotted:
            self.path(circle_points(c, r), colour, width, dotted, True)
            return
        w = max(1, int(round(width * self.ss)))
        cx, cy = c[0] * self.ss, c[1] * self.ss
        rr = r * self.ss
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                       outline=colour, width=w)

    def text(self, xy, s, size, colour="#111111", bold=False):
        f = load_font(size * self.ss, bold)
        self.d.text((xy[0] * self.ss, xy[1] * self.ss), s, font=f, fill=colour)

    def save(self, path):
        self.img.resize((self.img.width // self.ss, self.img.height // self.ss),
                        Image.LANCZOS).save(path)


def rounded_rect_points(box, radii, seg=16):
    """radii = [top-left, top-right, bottom-right, bottom-left] in pixels."""
    x0, y0, x1, y1 = box
    tl, tr, br, bl = radii
    lim = min((x1 - x0) / 2, (y1 - y0) / 2)
    tl, tr, br, bl = [min(v, lim) for v in (tl, tr, br, bl)]
    pts = []
    corners = [(x1 - tr, y0 + tr, -90, tr), (x1 - br, y1 - br, 0, br),
               (x0 + bl, y1 - bl, 90, bl), (x0 + tl, y0 + tl, 180, tl)]
    for cx, cy, a0, r in corners:
        if r <= 0.01:
            pts.append((cx, cy))
            continue
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def circle_points(c, r, seg=96):
    return [(c[0] + r * math.cos(2 * math.pi * i / seg),
             c[1] + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]


_FONTS = {}


def load_font(size, bold=False):
    key = (size, bold)
    if key not in _FONTS:
        name = "Arial Bold.ttf" if bold else "Arial.ttf"
        try:
            _FONTS[key] = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
        except OSError:
            _FONTS[key] = ImageFont.load_default()
    return _FONTS[key]


def angles(count, start_deg):
    return [start_deg + 360.0 * i / count for i in range(count)]


def draw_shape(draw, s, colour, width):
    kind = s["type"]
    if kind == "polygon":
        draw.path(s["points"], colour, width, closed=True)
    elif kind == "line":
        draw.path(s["points"], colour, width)
    elif kind == "lines":
        for ln in s["lines"]:
            draw.path(ln, colour, width)
    elif kind == "rect":
        draw.rect(s["box"], colour, width)
    elif kind == "rects":
        for b in s["boxes"]:
            draw.rect(b, colour, width)
    elif kind == "rounded_rect":
        draw.rounded_rect(s["box"], s["radius"], colour, width)
    elif kind == "rounded_rects":
        for b in s["boxes"]:
            draw.rounded_rect(b, s["radius"], colour, width)
    elif kind == "circle":
        draw.circle(s["c"], s["r"], colour, width)
    elif kind == "circles":
        for c in s["centres"]:
            draw.circle(c, s["radius"], colour, width)
    elif kind == "ring":
        draw.circle(s["c"], s["r"], colour, width)
        draw.circle(s["c"], s["r_in"], colour, width)
    elif kind == "annulus":
        draw.filled(s["c"], s["r"], colour)
        draw.filled(s["c"], s["r_in"], "#FFFFFF")
    elif kind == "circle_ring_array":
        for a in angles(s["count"], s["start_deg"]):
            c = (s["c"][0] + s["ring"] * math.cos(math.radians(a)),
                 s["c"][1] + s["ring"] * math.sin(math.radians(a)))
            draw.circle(c, s["radius"], colour, width)
    elif kind == "radial_ticks":
        for a in angles(s["count"], s["start_deg"]):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            draw.path([(s["c"][0] + s["r"] * ca, s["c"][1] + s["r"] * sa),
                       (s["c"][0] + s["r_out"] * ca,
                        s["c"][1] + s["r_out"] * sa)], colour, width)
    else:
        raise ValueError("unknown shape " + kind)


# ---- ink -> parts ------------------------------------------------------
def reference_mask(path=OVERLAY):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    return (r > 140) & (g < 130) & (b > 60) & ((r - g) > 60) & ((b - g) > 30)


def build_ink(width=None, height=None):
    """Trace ink, minus the strokes the principal removed, plus the ones added."""
    from scipy import ndimage
    width = ART_W if width is None else width
    height = PHOTO_H if height is None else height
    ink = reference_mask()

    # -- removals -------------------------------------------------------
    if REMOVE_SEEDS:
        lab, _ = ndimage.label(ink, structure=np.ones((3, 3)))
        for x, y in REMOVE_SEEDS:
            comp = lab[y, x]
            if comp:
                size = int((lab == comp).sum())
                if not 500 < size < 20000:
                    raise SystemExit("refusing to remove a %d px component" % size)
                ink &= lab != comp
    for x0, y0, x1, y1 in REMOVE_RECTS:
        ink[y0:y1, x0:x1] = False
    if REMOVE_ANNULI:
        yy, xx = np.mgrid[0:ink.shape[0], 0:ink.shape[1]]
        for a in REMOVE_ANNULI:
            r = np.hypot(xx - a["c"][0], yy - a["c"][1])
            ink[(r >= a["r_in"]) & (r <= a["r_out"])] = False

    # -- additions ------------------------------------------------------
    if ADDED:
        c = Canvas(width, height, ss=1)
        for shape in ADDED:
            draw_shape(c, shape, "#000000", 4)
        ink = ink | (np.asarray(c.img.convert("L")) < 250)
    return ink


def assign(width=None, height=None):
    """Label each ink pixel with the part whose probe stroke is closest."""
    from scipy import ndimage
    width = ART_W if width is None else width
    height = PHOTO_H if height is None else height
    ink = build_ink(width, height)
    best = np.full(ink.shape, 1e9, np.float32)
    label = np.full(ink.shape, -1, np.int16)
    for i, part in enumerate(PARTS):
        c = Canvas(width, height, ss=1)
        for probe in part["probes"]:
            draw_shape(c, probe, "#000000", 1)
        probe_ink = np.asarray(c.img.convert("L")) < 250
        dist = ndimage.distance_transform_edt(~probe_ink)
        score = dist - part["bias"]
        better = score < best
        best[better] = score[better]
        label[better] = i
    return ink, label, best


def report(ink, label, best, verbose=False):
    print("ink -> part assignment (probe strokes only decide ownership)")
    print("  ink pixels : %d" % ink.sum())
    far = ink & (best > 14)
    print("  orphans    : %d px further than 14 px from any probe" % far.sum())
    if far.any():
        ys, xs = np.nonzero(far)
        print("               x %d..%d  y %d..%d" % (xs.min(), xs.max(),
                                                    ys.min(), ys.max()))
    share = {p["id"]: int((ink & (label == i)).sum())
             for i, p in enumerate(PARTS)}
    if verbose:
        print("\n  per part")
        for pid, n in share.items():
            print("    %-20s %7d px  %5.1f%%" % (pid, n,
                                                 100.0 * n / ink.sum()))
    missing = [k for k, v in share.items() if v == 0]
    if missing:
        print("  no ink claimed by: %s" % ", ".join(missing))


def trace_part_loops(mask, tol=0.9):
    out = []
    for poly in contours(mask):
        pts = rdp(poly, tol)
        if len(pts) >= 3:
            out.append([[round(float(x), 1), round(float(y), 1)]
                        for x, y in pts])
    return out


# ---- render ------------------------------------------------------------
def legend_height():
    h = 42 + 34 + 20 + 20 + 34 + 40          # title and subtitle block
    for role in ROLE_ORDER:
        n = len([p for p in PARTS if p["role"] == role])
        if n:
            h += 36 + 38 * n + 12
    return h + 12 * 17 + 40


def render(out_png=None, out_json=None):
    out_png = out_png or OUT_PNG
    out_json = out_json or OUT_JSON
    ink, label, best = assign()

    art_w, art_h = ART_W, ART_H
    margin = 40
    legend_w = 660
    width = margin + art_w + margin + legend_w + margin
    height = max(art_h + 2 * margin, legend_height() + 2 * margin)

    # exact recolour of the approved ink - no resampling, no redrawing
    art = np.full((art_h, art_w, 3), 255, np.uint8)
    sub_ink = ink[:art_h, :art_w]
    sub_lab = label[:art_h, :art_w]
    for i, part in enumerate(PARTS):
        hexed = ROLE_COLOUR[part["role"]]
        rgb = tuple(int(hexed[j:j + 2], 16) for j in (1, 3, 5))
        art[sub_ink & (sub_lab == i)] = rgb

    # the legend is drawn supersampled, then the ink is pasted back at 1:1 so
    # the trace stays pixel-exact in the delivered PNG
    c = Canvas(width, height, ss=2)

    # ---- legend ----
    lx = margin + art_w + margin
    id_font = load_font(17 * c.ss, False)
    id_w = max(id_font.getlength(p["id"]) for p in PARTS) / c.ss + 18
    ty = margin
    c.text((lx, ty), TITLE + " - PART MAP", 30, "#111111", bold=True)
    ty += 42
    c.text((lx, ty), "your trace, recoloured   |   120 mm bead   |   1 px = %.3f mm"
           % MM_PER_PX, 15, "#555555")
    ty += 20
    c.text((lx, ty), "no redraw - only the edits listed at the foot of this panel",
           15, "#555555")
    ty += 20
    c.text((lx, ty), "colours are levels, not identity", 15, "#555555")
    ty += 34

    for role in ROLE_ORDER:
        group = [p for p in PARTS if p["role"] == role]
        if not group:
            continue
        chip = Canvas(28, 28, ss=2)
        chip.rect([5, 5, 23, 23], ROLE_COLOUR[role], 4.0)
        c.img.paste(chip.img.resize((28, 28), Image.LANCZOS),
                    (int(lx * c.ss), int((ty + 2) * c.ss)))
        c.text((lx + 38, ty), ROLE_HEAD[role], 17, "#222222", bold=True)
        ty += 36
        for p in group:
            c.text((lx + 38, ty + 4), p["id"], 17, ROLE_COLOUR[role])
            c.text((lx + 38 + id_w, ty + 4), p["name"], 17, "#111111")
            ty += 38
        ty += 12

    notes = EDITS_NOTES
    for i, line in enumerate(notes):
        c.text((lx, ty + 24 + 17 * i), line, 13.5, "#555555")

    sheet = c.img.resize((width, height), Image.LANCZOS)
    arr = np.asarray(sheet).copy()
    arr[margin:margin + art_h, margin:margin + art_w] = art
    out = Image.fromarray(arr)
    d = ImageDraw.Draw(out)
    d.rectangle([margin - 1, margin - 1, margin + art_w, margin + art_h],
                outline="#E4E7EB", width=1)
    out.save(out_png)

    back = np.asarray(out)[margin:margin + art_h, margin:margin + art_w]
    drawn = ~np.all(back == 255, axis=2)
    src = reference_mask()[:art_h, :art_w]
    kept = src & drawn
    print("trace ink kept      : %d px (%.1f%% of the trace)"
          % (kept.sum(), 100.0 * kept.sum() / src.sum()))
    print("trace ink removed   : %d px" % int((src & ~drawn).sum()))
    print("ink added on request: %d px" % int((drawn & ~src).sum()))

    parts_json = []
    for i, p in enumerate(PARTS):
        mask = ink & (label == i)
        loops = trace_part_loops(mask) if mask.any() else []
        entry = dict(id=p["id"], name=p["name"], role=p["role"],
                     colour=ROLE_COLOUR[p["role"]],
                     pixels=int(mask.sum()), loops=loops)
        if p.get("draw"):
            entry["added"] = True
        parts_json.append(entry)
    with open(out_json, "w") as fh:
        fh.write(dump_json(dict(
            source=os.path.relpath(OVERLAY, REPO),
            note="ink traced from the approved overlay; loops are closed, "
                 "even-odd fill, overlay pixels (origin top-left, y down)",
            edits=dict(removed=list(EDITS_REMOVED),
                       added=list(EDITS_ADDED)),
            body_centre_x=CX,
            mm_per_px=round(MM_PER_PX, 5),
            bead_width_mm=BEAD_WIDTH_MM,
            parts=parts_json), indent=1))
    print("wrote %s" % os.path.relpath(out_png, REPO))
    print("wrote %s" % os.path.relpath(out_json, REPO))
    report(ink, label, best)


def dump_json(obj, indent=1):
    """JSON with coordinate arrays kept on one line, so the file stays readable."""
    pad = " " * indent

    def num(v):
        v = round(v, 2) if isinstance(v, float) else v
        return json.dumps(v)

    def inline(v):
        if all(isinstance(n, (int, float)) for n in v):
            return "[" + ", ".join(num(n) for n in v) + "]"
        return "[" + ", ".join(inline(n) for n in v) + "]"

    def emit(v, depth):
        head = pad * (depth + 1)
        if isinstance(v, dict):
            items = [head + json.dumps(k) + ": " + emit(val, depth + 1)
                     for k, val in v.items()]
            return "{\n" + ",\n".join(items) + "\n" + pad * depth + "}"
        if isinstance(v, list) and v:
            if all(isinstance(n, (int, float)) for n in v):
                return inline(v)
            if all(isinstance(n, list) and all(isinstance(m, (int, float))
                                              for m in n) for n in v):
                one = inline(v)
                if len(one) + len(head) <= 96:
                    return one
                lines, cur = [], head + " "
                for i, pt in enumerate(v):
                    piece = inline(pt) + ("," if i < len(v) - 1 else "")
                    if len(cur) + len(piece) > 96 and cur.strip():
                        lines.append(cur.rstrip())
                        cur = head + " "
                    cur += piece + " "
                lines.append(cur.rstrip())
                return "[\n" + "\n".join(lines) + "\n" + pad * depth + "]"
            items = [head + emit(n, depth + 1) for n in v]
            return "[\n" + ",\n".join(items) + "\n" + pad * depth + "]"
        return json.dumps(v)

    return emit(obj, 0) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only, no render")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="per-part pixel counts")
    ap.add_argument("--view", default=DEFAULT_VIEW, help=", ".join(viewdata.available()))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.view != DEFAULT_VIEW:
        use_view(args.view)
    if args.check:
        ink, label, best = assign()
        report(ink, label, best, verbose=args.verbose)
        return
    render(out_png=args.out)


if __name__ == "__main__":
    main()
