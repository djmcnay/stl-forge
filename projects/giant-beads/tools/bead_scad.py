#!/usr/bin/env python3
"""Turn a view's bead-sketch JSON into the SCAD data file the template includes.

`<stem>-bead-sketch.json` is the build input - the resolved geometry the
principal approved.  OpenSCAD cannot read JSON, so this tool bakes it into
`templates/bead_defender_<stem>_data.scad` as plain arrays.  The template next
to it stays hand-written and parametric; only the geometry is generated.

Coordinates are converted once, here:

* overlay pixels (y down, origin top-left) become millimetres (y up) with the
  origin at the centre of the silhouette, so the bead spans exactly
  `bead_width_mm` across;
* everything is emitted at the reference width (`DATA_WIDTH`), and the template
  scales the face plane by `width / DATA_WIDTH`.  Depths stay in millimetres, so
  a wider bead keeps the same etch depth and the same raised heights.

The JSON's part list is already grouped by level; this tool only converts each
primitive into the shape SCAD needs (a polyline stroke, a ring stroke, a filled
pad, a dome).  Nothing is added, moved or smoothed.

Usage (from the repo root):
    python3 projects/giant-beads/tools/bead_scad.py
    python3 projects/giant-beads/tools/bead_scad.py --view rear --check
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viewdata                                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
PROJECT = os.path.join(REPO, "projects", "giant-beads")
TEMPLATES = os.path.join(PROJECT, "templates")

DEFAULT_VIEW = "rear"
ARC_STEP_DEG = 7.5          # corner sampling for rounded rectangles
OUTLINE_TOL_MM = 0.2        # see simplify(): removes the pixel-trace wobble
TREAD_TOP_PX = 1132         # the chassis line: below it the profile is the two
                            # road wheels, which sit behind the rear
TREAD_SPLIT_MM = 0.3        # the clip must clear the chassis line itself, or a
                            # sliver of the middle band comes with it

# ---- clearance from the outline ----------------------------------------
# The template rounds the face edge with `fillet_radius`, which pulls the flat
# face in by that much all the way round.  Anything drawn closer than that to
# the outline ends up overhanging the rounded shoulder, so a feature is pushed
# inwards until it clears the fillet, plus half as much again for etched lines
# and a fixed move for the lamps.
FILLET_MM = 1.0             # matches fillet_radius in the template
FACE_MARGIN_MM = FILLET_MM / 2   # extra margin on etched lines
PAD_COVE_MM = 1.0           # matches pad_cove in the template
LAMP_NUDGE_MM = 3.0         # the principal's figure for a lamp sat too close


# ---- pixel frame -> millimetre frame -----------------------------------
class Frame:
    """The one conversion the pipeline makes: sketch px to bead mm."""

    def __init__(self, doc):
        xs = [p[0] for p in doc["silhouette"]]
        ys = [p[1] for p in doc["silhouette"]]
        self.width_mm = doc["bead_width_mm"]
        self.span_px = max(xs) - min(xs)
        self.scale = self.width_mm / self.span_px
        self.cx = (min(xs) + max(xs)) / 2.0
        self.cy = (min(ys) + max(ys)) / 2.0
        self.height_mm = (max(ys) - min(ys)) * self.scale

    def xy(self, px, py):
        return [round((px - self.cx) * self.scale, 3),
                round((self.cy - py) * self.scale, 3)]

    def r(self, v):
        return round(v * self.scale, 3)

    def px(self, mx, my):
        """Millimetres back to source pixels, for primitives that need them."""
        return [round(mx / self.scale + self.cx, 3),
                round(self.cy - my / self.scale, 3)]

    def box_mm(self, box):
        """A pixel box as millimetres, y up: [x0, y0, x1, y1]."""
        x0, y0, x1, y1 = box
        a, b = self.xy(x0, y0), self.xy(x1, y1)
        return [a[0], b[1], b[0], a[1]]

    def box_px(self, box):
        x0, y0, x1, y1 = box
        a, b = self.px(x0, y0), self.px(x1, y1)
        return [a[0], b[1], b[0], a[1]]

    def ring(self, pts):
        return [self.xy(x, y) for x, y in pts]


def simplify(pts, tol):
    """Douglas-Peucker on the closed outline.

    The sketch is traced on pixel cracks, so the profile carries sub-pixel
    wobble: visible in CAD as facets on a wall that should be flat, invisible on
    a print.  Removing every point that sits within `tol` of the chord between
    its neighbours keeps the principal's shape to within that tolerance and
    leaves a clean edge for the extruder.
    """
    ring = pts + [pts[0]]

    def rec(index):
        if len(index) < 3:
            return index
        a, b = index[0], index[-1]
        ax, ay = ring[a]
        bx, by = ring[b]
        dx, dy = bx - ax, by - ay
        span = math.hypot(dx, dy)
        best, at = -1.0, None
        for k in index[1:-1]:
            px, py = ring[k]
            d = (math.hypot(px - ax, py - ay) if span == 0
                 else abs(dx * (ay - py) - dy * (ax - px)) / span)
            if d > best:
                best, at = d, k
        if best <= tol or at is None:
            return [a, b]
        i = index.index(at)
        return rec(index[:i + 1])[:-1] + rec(index[i:])

    keep = rec(list(range(len(ring))))
    return [ring[i] for i in keep[:-1]]


def clip_below(pts, y):
    """The closed loops of a polygon at or below the line y (mm).

    A shape that crosses the line more than twice comes back as several loops -
    the rear's two road wheels, for instance, which the chassis line separates
    from the body between them.
    """
    pieces, run = [], []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        a_in, b_in = a[1] <= y, b[1] <= y
        if a_in:
            if not run:
                run = [[round(a[0], 3), round(a[1], 3)]]
            else:
                run.append([round(a[0], 3), round(a[1], 3)])
            if not b_in:
                t = (y - a[1]) / (b[1] - a[1])
                run.append([round(a[0] + t * (b[0] - a[0]), 3), y])
                pieces.append(run)
                run = []
        elif b_in:
            t = (y - a[1]) / (b[1] - a[1])
            run = [[round(a[0] + t * (b[0] - a[0]), 3), y],
                   [round(b[0], 3), round(b[1], 3)]]
    if len(run) > 2:
        pieces.append(run)
    return [p for p in pieces if len(p) >= 3]


def round_rect_loop(frame, box, radius):
    """A rounded rectangle as a closed polyline, corners sampled by angle."""
    x0, y0, x1, y1 = box
    radii = list(radius) if isinstance(radius, (list, tuple)) else [radius] * 4
    # a corner radius can never exceed half the shorter side
    lim = min(x1 - x0, y1 - y0) / 2.0
    radii = [min(max(r, 0.0), lim) for r in radii]
    corners = [
        (x0 + radii[0], y0 + radii[0], 180, 270, radii[0]),   # top-left
        (x1 - radii[1], y0 + radii[1], 270, 360, radii[1]),   # top-right
        (x1 - radii[2], y1 - radii[2], 0, 90, radii[2]),      # bottom-right
        (x0 + radii[3], y1 - radii[3], 90, 180, radii[3]),    # bottom-left
    ]
    pts = []
    for cx, cy, a0, a1, rr in corners:
        if rr <= 0.01:
            pts.append([cx, cy])
            continue
        n = max(2, int(math.ceil((a1 - a0) / ARC_STEP_DEG)))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append([cx + rr * math.cos(a), cy + rr * math.sin(a)])
    return frame.ring(pts)


def ring_array(group, frame):
    """A ring of small circles, each a ring stroke of its own radius."""
    cx, cy = group["c"]
    out = []
    for i in range(int(group["count"])):
        a = math.radians(group["start_deg"] + 360.0 * i / group["count"])
        out.append([round((cx + group["ring"] * math.cos(a) - frame.cx)
                          * frame.scale, 3),
                    round((frame.cy - (cy + group["ring"] * math.sin(a)))
                          * frame.scale, 3),
                    frame.r(group["radius"])])
    return out


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx
                                               + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def edge_distance(pt, ring):
    return min(_seg_dist(pt, ring[i], ring[(i + 1) % len(ring)])
               for i in range(len(ring)))


def _inward_normal(centre, ring):
    """Unit normal of the nearest outline edge, pointing into the body."""
    i = min(range(len(ring)),
            key=lambda k: _seg_dist(centre, ring[k], ring[(k + 1) % len(ring)]))
    a, b = ring[i], ring[(i + 1) % len(ring)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    # the interior is the side the centre of the bead lies on
    if nx * (0 - mid[0]) + ny * (0 - mid[1]) < 0:
        nx, ny = -nx, -ny
    return nx, ny, _seg_dist(centre, ring[i], b)


def nudge_inside(centre, radius, ring, clearance, least=0.0):
    """Slide a circle inwards until it clears the outline.

    A feature drawn tight against the flank ends up overhanging the filleted
    shoulder, so it is moved along the inward normal of the nearest edge.  At
    least `least` millimetres, and further if the geometry needs it - the move
    is always the smallest that puts the whole shape on the flat face.
    """
    want = clearance + radius
    if edge_distance(centre, ring) >= want - 1e-6:
        return centre, 0.0, True          # already wholly on the flat face
    moved = 0.0
    for _ in range(80):
        d = edge_distance(centre, ring)
        if d >= want - 1e-6 and moved >= least - 1e-6:
            return centre, moved, True
        shortfall = max(0.0, want - d)
        step = max(shortfall, least - moved)
        if step <= 1e-9:
            step = 0.02
        nx, ny, _ = _inward_normal(centre, ring)
        centre = [centre[0] + nx * step, centre[1] + ny * step]
        moved += step
    return centre, moved, edge_distance(centre, ring) >= want - 1e-6


def nudge_box(box, ring, clearance):
    """Slide a rectangle towards the centre line until it clears the outline."""
    x0, y0, x1, y1 = box
    moved = 0.0
    for _ in range(40):
        corners = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        if min(edge_distance(c, ring) for c in corners) >= clearance:
            break
        # which side is closer to the outline?
        left = min(edge_distance(c, ring) for c in (corners[0], corners[3]))
        right = min(edge_distance(c, ring) for c in (corners[1], corners[2]))
        step = 0.1
        if left <= right:
            x0 += step
            x1 += step
            moved += step
        else:
            x0 -= step
            x1 -= step
            moved -= step
    return [x0, y0, x1, y1], moved


def collect(doc, frame):
    """Sort the sketch parts into the arrays the SCAD template consumes."""
    sil = simplify(frame.ring(doc["silhouette"][:-1]), OUTLINE_TOL_MM)
    out = dict(silhouette=sil,
               tread=clip_below(sil, frame.xy(0, TREAD_TOP_PX)[1]
                                - TREAD_SPLIT_MM),
               tread_y=round(frame.xy(0, TREAD_TOP_PX)[1] - TREAD_SPLIT_MM, 3),
               strokes=[], rings=[], wheel_rings=[], tyre=[], wheel=[],
               seam=[], lights=[], nudges=[])
    silhouette = frame.ring(doc["silhouette"][:-1])

    for part in doc["parts"]:
        pid, level, kind = part["id"], part["level"], part["kind"]
        # detail sitting on the raised steel wheel is cut at the wheel's height
        on_wheel = pid in ("spare_holes", "spare_nuts", "spare_hub")

        if kind == "polyline":
            out["strokes"].append(frame.ring(part["points"]))
        elif kind == "lines":
            if level == "etch":
                for line in part["lines"]:
                    out["strokes"].append(frame.ring(line))
            elif level == "raised_seam":
                # a pair of parallel lines bounds a band: that band is the pad
                lines = part["lines"]
                for i in range(0, len(lines) - 1, 2):
                    a, b = lines[i], lines[i + 1]
                    out["seam"].append(frame.ring([a[0], a[1], b[1], b[0]]))
        elif kind == "round_rect":
            # the clearance pass works in millimetres, like the outline
            box_mm, moved = nudge_box(frame.box_mm(part["box"]), silhouette,
                                      FILLET_MM + FACE_MARGIN_MM)
            box = frame.box_px(box_mm) if abs(moved) > 0.01 else part["box"]
            out["strokes"].append(round_rect_loop(frame, box, part["radius"]))
            if abs(moved) > 0.01:
                out["nudges"].append("%s moved %+.2f mm" % (pid, moved))
        elif kind == "ring_array":
            (out["wheel_rings"] if on_wheel else out["rings"]).extend(
                ring_array(part, frame))
        elif kind == "circle":
            c = frame.xy(*part["c"])
            if on_wheel:
                out["wheel_rings"].append([c[0], c[1], frame.r(part["r"])])
            elif level == "raised_tyre":
                out["tyre"].append([c[0], c[1], frame.r(part["r"]), None])
            elif level == "raised_wheel":
                out["wheel"].append([c[0], c[1], frame.r(part["r"])])
        elif kind == "circles" and level == "lights":
            for c_px, r_px in zip(part["centres"], part["radii"]):
                c = frame.xy(*c_px)
                r = frame.r(r_px)
                # the cove is part of the dome's footprint, so the target is
                # the face fillet only: the smallest move that keeps the whole
                # raised shape on the flat face, and never less than the
                # principal's 3 mm
                before = c
                c, moved, ok = nudge_inside(c, r + PAD_COVE_MM, silhouette,
                                            FILLET_MM, least=LAMP_NUDGE_MM)
                if not ok:
                    raise SystemExit("lamp at %.1f,%.1f cannot clear the face "
                                     "fillet - shrink it or move it by hand"
                                     % (c[0], c[1]))
                out["lights"].append([c[0], c[1], r])
                if moved > 0.01:
                    out["nudges"].append("lamp at %+.0f,%+.0f moved %.2f mm"
                                         % (c_px[0], c_px[1], moved))

    # the tyre pad is an annulus: its outer edge minus the steel wheel's edge
    if len(out["tyre"]) == 1 and len(out["wheel"]) == 1:
        t, w = out["tyre"][0], out["wheel"][0]
        if abs(t[0] - w[0]) < 1e-6 and abs(t[1] - w[1]) < 1e-6:
            t[3] = w[2]
    for t in out["tyre"]:
        if t[3] is None:
            raise SystemExit("spare tyre has no inner radius: the steel wheel "
                             "part must share its centre")
    return out


# ---- emit --------------------------------------------------------------
def fmt(v):
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def emit_points(name, pts, comment=None):
    """A flat point list: one [x, y] per line, easy to diff and to read."""
    lines = []
    if comment:
        lines.append("// " + comment)
    lines.append("%s = [" % name)
    for i, pt in enumerate(pts):
        lines.append("    [%s]%s" % (", ".join(fmt(v) for v in pt),
                                     "," if i < len(pts) - 1 else ""))
    lines.append("];")
    return "\n".join(lines)


def emit_list(name, rows, comment=None):
    lines = []
    if comment:
        lines.append("// " + comment)
    lines.append("%s = [" % name)
    for i, row in enumerate(rows):
        if isinstance(row[0], list):
            body = "[%s]" % ", ".join("[%s]" % ", ".join(fmt(v) for v in pt)
                                      for pt in row)
        else:
            body = "[%s]" % ", ".join(fmt(v) for v in row)
        lines.append("    %s%s" % (body, "," if i < len(rows) - 1 else ""))
    lines.append("];")
    return "\n".join(lines)


def text_of(doc, frame, data, view_name):
    head = '''// GENERATED - do not edit by hand.
// Source: references/defender/%s-bead-sketch.json (the approved clean sketch)
// Tool:   tools/bead_scad.py
//
// Face plane in millimetres, y up, origin at the centre of the silhouette.
// Geometry is emitted at the reference width %s mm; the template scales the
// face plane by width / DATA_WIDTH and leaves the depths in millimetres.
''' % (view_name, fmt(frame.width_mm))

    chunks = [head,
              "DATA_WIDTH = %s;" % fmt(frame.width_mm),
              "DATA_HEIGHT = %s;   // silhouette height at the reference width"
              % fmt(frame.height_mm),
              ""]

    sil = data["silhouette"]
    chunks.append(emit_points("SILHOUETTE", sil,
                              comment="the bead profile, closed"))
    chunks.append("")
    chunks.append(emit_list("ETCH_STROKES", data["strokes"],
                            comment="engraved lines: one polyline each"))
    chunks.append("")
    chunks.append(emit_list("ETCH_RINGS", data["rings"],
                            comment="engraved circles: centre and radius"))
    chunks.append("")
    chunks.append(emit_list("ETCH_WHEEL_RINGS", data["wheel_rings"],
                            comment="engraved circles on the raised steel wheel"))
    chunks.append("")
    chunks.append(emit_list("RAISED_TYRE", data["tyre"],
                            comment="spare tyre pad: centre, outer r, inner r"))
    chunks.append("")
    chunks.append(emit_list("RAISED_WHEEL", data["wheel"],
                            comment="steel wheel pad: centre and radius"))
    chunks.append("")
    chunks.append(emit_list("RAISED_SEAM", data["seam"],
                            comment="waist seam pads, one closed polygon each"))
    chunks.append("")
    chunks.append("TREAD_Y = %s;   // the chassis line: bottom of the body"
                  % fmt(data["tread_y"]))
    chunks.append("")
    chunks.append(emit_list("TYRE_TREAD", data["tread"],
                            comment="road-wheel footprint: the profile below "
                                    "the bumper, where the wheels sit"))
    chunks.append("")
    chunks.append(emit_list("LIGHTS", data["lights"],
                            comment="round lamps: centre and radius"))
    chunks.append("")

    return "\n".join(chunks)


def write_scad(doc, frame, data, out_path, view_name):
    text = text_of(doc, frame, data, view_name)
    old = open(out_path).read() if os.path.exists(out_path) else None
    with open(out_path, "w") as fh:
        fh.write(text)
    return old != text


def data_path(view_name=DEFAULT_VIEW):
    view = viewdata.load(view_name)
    return os.path.join(TEMPLATES, "bead_defender_%s_data.scad" % view.STEM)


def render_text(view_name=DEFAULT_VIEW):
    """The generated SCAD as text, without touching the templates folder."""
    view = viewdata.load(view_name)
    doc = json.load(open(viewdata.out_paths(view)["sketch_json"]))
    frame = Frame(doc)
    data = collect(doc, frame)
    return text_of(doc, frame, data, view.STEM), frame, data, doc


def generate(view_name=DEFAULT_VIEW):
    view = viewdata.load(view_name)
    paths = viewdata.out_paths(view)
    doc = json.load(open(paths["sketch_json"]))
    frame = Frame(doc)
    data = collect(doc, frame)
    out_path = data_path(view_name)
    changed = write_scad(doc, frame, data, out_path, view.STEM)
    return dict(path=out_path, changed=changed, frame=frame, data=data,
                doc=doc)


def report(res, view_name=DEFAULT_VIEW):
    f, d = res["frame"], res["data"]
    print("%s -> %s%s" % (view_name, os.path.relpath(res["path"], REPO),
                          "" if res["changed"] else "  (unchanged)"))
    print("  1 px = %.4f mm   face spans %.2f x %.2f mm at the reference width"
          % (f.scale, f.width_mm, f.height_mm))
    print("  %d profile points (%d before the %.2f mm wobble clean-up)"
          % (len(res["data"]["silhouette"]),
             len(res["doc"]["silhouette"]) - 1, OUTLINE_TOL_MM))
    for note in res["data"]["nudges"]:
        print("  cleared to fit the face fillet: " + note)
    for key, label in (("strokes", "etched polylines"),
                       ("rings", "etched rings"),
                       ("wheel_rings", "rings on the steel wheel"),
                       ("tyre", "tyre pads"), ("wheel", "wheel pads"),
                       ("seam", "seam pads"), ("lights", "lamps")):
        print("  %-24s %d" % (label, len(d[key])))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--view", default=DEFAULT_VIEW,
                    help=", ".join(viewdata.available()))
    ap.add_argument("--check", action="store_true",
                    help="report only, write nothing")
    args = ap.parse_args()
    if args.check:
        view = viewdata.load(args.view)
        doc = json.load(open(viewdata.out_paths(view)["sketch_json"]))
        frame = Frame(doc)
        report(dict(path="(not written)", changed=False, frame=frame,
                    data=collect(doc, frame), doc=doc), args.view)
        return
    report(generate(args.view), args.view)


if __name__ == "__main__":
    main()
