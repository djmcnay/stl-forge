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


def collect(doc, frame):
    """Sort the sketch parts into the arrays the SCAD template consumes."""
    out = dict(silhouette=simplify(frame.ring(doc["silhouette"][:-1]),
                                   OUTLINE_TOL_MM),
               strokes=[], rings=[], wheel_rings=[], tyre=[], wheel=[],
               seam=[], lights=[])
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
            out["strokes"].append(round_rect_loop(frame, part["box"],
                                                  part["radius"]))
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
                out["lights"].append([c[0], c[1], frame.r(r_px)])

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
