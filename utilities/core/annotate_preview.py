#!/usr/bin/env python3
"""Draw the delivery verification overlay on a bead preview PNG.

Annotates the assembly preview (pink recess floor on white body) with:
  BLUE circle - the spec letter circle (width * letter_space, in mm)
  RED cross   - the face centre (autocenter + viewall map the object
                centre to the image centre)
  RED box     - the letter ink bbox
Prints the measurement record (px/mm scale, margins to centre,
bbox-corner radius AND max ink radius vs circle radius) and exits
nonzero when the letter is missing, its ink leaves the circle, or its
bbox corner lands outside. Circle-containment spec: the bbox corner is
only a BOUND on the ink, so the hard containment gate is the max
distance of an actual pink ink pixel from the centre; the bbox corner
must measure inside-or-touching (within 0.05 mm of the circle). Both
gates allow the same 0.05 mm touch tolerance. Requires Pillow.

MEASUREMENT RENDER RULE: for scale-exact numbers, render the preview
with --projection=ortho --autocenter --viewall (e.g. --camera
0,0,0,0,0,0,350 for a bead's top view). A perspective render
magnifies features nearer the camera relative to the mid-row
silhouette edge used for the px/mm calibration (~4.5% for a bead's
top face at the standard distance), which can flip a passing bbox
corner to OUTSIDE; the overlay stays eye-valid but its printed mm
then carry that depth bias.

Example:
  python3 core/annotate_preview.py out/previews/bead_default_top.png \\
      /tmp/verified.png 90

Ship the output PNG to the project delivery folder (SKILL.md delivery
rules); the stdout numbers are the measurement record for the report.
For a letter rendered in a colour other than HotPink, adjust PINK below.
"""
import argparse
import math
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow required: python3 -m pip install Pillow")

PINK = lambda r, g, b: r > 170 and g < 130 and b > 130
BG_DELTA = 30


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="preview PNG (assembly render, pink letter)")
    ap.add_argument("output", help="annotated PNG to write")
    ap.add_argument("circle_mm", type=float,
                    help="spec letter circle diameter in mm (width*letter_space)")
    ap.add_argument("--bead-mm", type=float, default=120.0,
                    help="object full width in mm (bead diameter, default 120)")
    ap.add_argument("--span-mm", type=float, default=None,
                    help="when given, derive pixels-per-mm from the object's bbox "
                    "width over ALL rows (min/max x of non-background pixels) "
                    "instead of the mid-row edge")
    ap.add_argument("--circle-y-mm", type=float, default=0.0,
                    help="world-space vertical offset of the letter circle "
                    "centre from the face centre in mm (+up/-down in the "
                    "model)")
    ap.add_argument("--label", default=None,
                    help="overlay caption (default derives from circle_mm)")
    ap.add_argument("--object", dest="object", action="store_true",
                    help="letter-less object mode: measure the object bbox "
                    "as non-background pixels over ALL rows (x and y); "
                    "circle_mm is the width spec")
    ap.add_argument("--expect-h-mm", type=float, default=None,
                    help="expected object height in mm (object mode only)")
    a = ap.parse_args()

    im = Image.open(a.input).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = px[2, 2]

    if a.object:
        min_x, max_x, min_y, max_y = w, -1, h, -1
        for yy in range(h):
            for x in range(w):
                p = px[x, yy]
                if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > BG_DELTA:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
                    if yy < min_y:
                        min_y = yy
                    if yy > max_y:
                        max_y = yy
        if max_x < 0:
            sys.exit("FAIL: no object (background detection broke)")
        ppm = (max_x - min_x) / a.circle_mm
        w_mm = (max_x - min_x) / ppm
        h_mm = (max_y - min_y) / ppm
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        radius = 60.0 * ppm
        draw = ImageDraw.Draw(im)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     outline=(0, 160, 255), width=3)
        draw.line([(cx - 40, cy), (cx + 40, cy)], fill=(255, 0, 0), width=2)
        draw.line([(cx, cy - 40), (cx, cy + 40)], fill=(255, 0, 0), width=2)
        draw.rectangle([min_x, min_y, max_x, max_y],
                       outline=(255, 60, 60), width=2)
        if a.expect_h_mm is None:
            print(f"object = {w_mm:.2f} x {h_mm:.2f} mm "
                  f"(width spec {a.circle_mm:g} mm)")
        else:
            print(f"object = {w_mm:.2f} x {h_mm:.2f} mm "
                  f"(width spec {a.circle_mm:g} mm, "
                  f"expect h {a.expect_h_mm:g})")
        print(f"circle tracks width: L={min_x - (cx - radius):.1f} "
              f"R={(cx + radius) - max_x:.1f} px")
        label = (a.label or "BLUE circle = width spec | RED cross = centre "
                 "| RED box = object bbox")
        draw.text((8, h - 24), label, fill=(0, 0, 0))
        im.save(a.output)
        print(f"saved: {a.output}")
        ok = abs(w_mm - a.circle_mm) <= 0.3 and (
            True if a.expect_h_mm is None
            else abs(h_mm - a.expect_h_mm) <= 0.75)
        sys.exit(0 if ok else 1)

    y = h // 2

    def delta(p):
        return abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2])

    left = next((x for x in range(w) if delta(px[x, y]) > BG_DELTA), None)
    if left is None and a.span_mm is None:
        sys.exit("FAIL: no object at mid-row (background detection broke)")
    cx = w / 2.0
    if a.span_mm is not None:
        min_x = w
        max_x = -1
        for yy in range(h):
            for x in range(w):
                p = px[x, yy]
                if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > BG_DELTA:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
        if max_x < 0:
            sys.exit("FAIL: no object (background detection broke)")
        ppm = (max_x - min_x) / a.span_mm
    else:
        ppm = (cx - left) * 2.0 / a.bead_mm
    radius = (a.circle_mm / 2.0) * ppm
    cy = y if a.circle_y_mm == 0 else y - a.circle_y_mm * ppm

    draw = ImageDraw.Draw(im)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 outline=(0, 160, 255), width=3)
    draw.line([(cx - 40, cy), (cx + 40, cy)], fill=(255, 0, 0), width=2)
    draw.line([(cx, cy - 40), (cx, cy + 40)], fill=(255, 0, 0), width=2)

    ok = True
    pink = [(x, yy) for yy in range(h) for x in range(w)
            if PINK(*px[x, yy])]
    if not pink:
        print("FAIL: no pink letter pixels (adjust PINK threshold or re-render)")
        ok = False
    else:
        xs = [p[0] for p in pink]
        ys = [p[1] for p in pink]
        l, r, t, b = min(xs), max(xs), min(ys), max(ys)
        draw.rectangle([l, t, r, b], outline=(255, 60, 60), width=2)
        corner = max(math.hypot(a_ - cx, b_ - cy)
                     for a_ in (l, r) for b_ in (t, b))
        ink_r = max(math.hypot(x - cx, yy - cy) for x, yy in pink)
        tol_px = 0.05 * ppm   # touching allowance: bbox corner may kiss the circle (spec: within 0.05 mm)
        print(f"ppm={ppm:.4f} circle_r={radius:.1f}px letter={r - l}x{b - t}px")
        print(f"margins to centre: L={int(cx - l)} R={int(r - cx)} "
              f"T={int(cy - t)} B={int(b - cy)} px")
        inside = corner <= radius + tol_px
        print(f"bbox corner r={corner:.1f}px vs circle r={radius:.1f}px -> "
              f"{'INSIDE' if inside else 'OUTSIDE'} by "
              f"{abs(radius - corner):.1f}px ({abs(radius - corner) / ppm:.2f} mm)")
        ink_inside = ink_r <= radius + tol_px
        print(f"ink max r={ink_r:.1f}px vs circle r={radius:.1f}px -> "
              f"{'INSIDE' if ink_inside else 'OUTSIDE'} by "
              f"{abs(radius - ink_r):.1f}px ({abs(radius - ink_r) / ppm:.2f} mm)")
        ok = inside and ink_inside

    label = (a.label or f"BLUE circle = spec dia {a.circle_mm:g}mm "
             "| RED cross = face centre | RED box = letter")
    draw.text((8, h - 24), label, fill=(0, 0, 0))
    im.save(a.output)
    print(f"saved: {a.output}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
