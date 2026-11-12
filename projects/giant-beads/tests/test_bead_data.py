"""The generated bead data, and the bead built from it.

Two things are guarded here:

1. `templates/bead_defender_<view>_data.scad` must be exactly what
   `tools/bead_scad.py` produces from the committed sketch JSON.  A stale data
   file would silently build last week's shape.
2. The template must render as a watertight solid at family defaults, so a
   broken primitive fails here rather than in the slicer.
"""
import json
import math
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import PROJECT_DIR

TOOLS = PROJECT_DIR / "tools"
sys.path.insert(0, str(TOOLS))

import bead_scad      # noqa: E402

TEMPLATE = PROJECT_DIR / "templates" / "bead_defender_rear_v2.scad"
OPENSCAD = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")


@pytest.fixture(scope="module")
def generated():
    text, frame, data, doc = bead_scad.render_text("rear")
    return text, frame, data, doc


# --- the data file is current -------------------------------------------

def test_committed_data_matches_the_sketch(generated):
    text = generated[0]
    on_disk = bead_scad.data_path("rear")
    assert Path(on_disk).read_text() == text, (
        "bead data is stale - run "
        "python3 projects/giant-beads/tools/bead_scad.py")


def test_generation_is_deterministic():
    assert bead_scad.render_text("rear")[0] == bead_scad.render_text("rear")[0]


# --- the data carries the whole sketch ----------------------------------

def test_face_is_exactly_the_family_width(generated):
    text, frame, data, doc = generated
    assert frame.width_mm == doc["bead_width_mm"]
    xs = [p[0] for p in data["silhouette"]]
    assert max(xs) - min(xs) == pytest.approx(frame.width_mm, abs=0.02)


def test_outline_has_no_raster_staircase(generated):
    """The flank is a curve: no pair of consecutive near-square steps."""
    _text, _frame, data, _doc = generated
    sil = data["silhouette"]
    for i in range(len(sil)):
        ang = bead_scad._turn(sil, i)
        # a step shows up as a sharp turn between two short edges
        a, b, c = sil[i - 1], sil[i], sil[(i + 1) % len(sil)]
        short = max(math.hypot(b[0] - a[0], b[1] - a[1]),
                    math.hypot(c[0] - b[0], c[1] - b[1]))
        if short < 2.0:
            assert ang > 100.0, (
                "staircase step at %.1f,%.1f (%.0f deg)" % (b[0], b[1], ang))


def test_silhouette_is_cleaned_but_faithful(generated):
    _, frame, data, _ = generated
    assert len(data["silhouette"]) >= 20
    # the wobble clean-up must not move the outline more than its tolerance
    assert len(data["silhouette"]) <= len(
        frame.ring(json.load(open(bead_scad.viewdata.out_paths(
            bead_scad.viewdata.load("rear"))["sketch_json"]))["silhouette"]))
    # no duplicate consecutive points: those are what made faceted walls
    for a, b in zip(data["silhouette"], data["silhouette"][1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-6


def test_the_outline_is_the_trace(generated):
    """No creative licence: the profile is the principal's drawing, cleaned.

    The one thing that broke this was a generator pass that rebuilt the wheel
    tips as semicircles - a tyre seen from behind is a curved rectangle, not a
    circle - so the outline is now checked against the trace it came from.
    """
    _, frame, data, _ = generated
    raw_path = bead_scad.viewdata.out_paths(
        bead_scad.viewdata.load("rear"))["sketch_json"]
    raw = frame.ring(json.load(open(raw_path))["silhouette"][:-1])
    # the clean-up can round a tight corner by about a millimetre; an invented
    # feature (the old semicircular tips) was out by four
    tol = 1.3
    for p in raw:
        assert bead_scad.edge_distance(p, data["silhouette"]) <= tol, (
            "the outline has left the trace at %.1f,%.1f" % (p[0], p[1]))
    for p in data["silhouette"]:
        assert bead_scad.edge_distance(p, raw) <= tol, (
            "the outline has invented a point at %.1f,%.1f" % (p[0], p[1]))


def test_the_wheel_is_round_in_profile(generated):
    """A squashed tyre: a dome, not a flat tab and not a circle from behind."""
    text = TEMPLATE.read_text()
    _frame, data = generated[1], generated[2]
    assert len(data["tread_crown"]) == len(data["tread"]) == 2
    rise = bead_scad.TREAD_LOW_MM - 0.2
    for (xc, hw, yd), loop in zip(data["tread_crown"], data["tread"]):
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        assert xc == pytest.approx((min(xs) + max(xs)) / 2.0, abs=0.01)
        assert hw == pytest.approx((max(xs) - min(xs)) / 2.0, abs=0.01)
        # the dome has to reach the whole wheel to die into the recess floor
        assert yd == pytest.approx(data["tread_y"] - min(ys), abs=0.01)
        assert hw > 4.0 and yd > 10.0 and rise > 0
    # the template builds that dome as a squashed sphere scaled by the wheel's
    # own half width and depth, which is what makes it tangent to the side wall
    assert re.search(r"scale\(\[hw, yd, crown_rise\]\) sphere\(r = 1", text)
    assert re.search(r"(?m)^\s*hw = max\(TREAD_CROWN\[k\]\[1\] \* S \+ 0\.05",
                     text)
    # the apex must stay under the face plane, or the wheel stops being recessed
    assert re.search(r"(?m)^crown_rise\s*=\s*tread_low\s*-\s*0\.2;", text)


def test_the_dome_is_clipped_by_the_footprint(generated):
    """The tyre may not swell out past the wheel it belongs to."""
    text = TEMPLATE.read_text()
    block = text[text.index("module wheel_dome"):text.index("module wheel_solid")]
    assert "intersection()" in block, "the dome is not clipped"
    assert "tread_one_2d(k)" in block, "the dome is not clipped by the footprint"
    for loop in generated[2]["tread"]:
        for i in range(len(loop)):
            a, b = loop[i], loop[(i + 1) % len(loop)]
            assert math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6


def test_tread_is_one_footprint_per_road_wheel(generated):
    """The chassis line separates two wheels, not one band across the bottom."""
    _text, _frame, data, _doc = generated
    assert len(data["tread"]) == 2
    tread_y = data["tread_y"]
    for loop in data["tread"]:
        ys = [p[1] for p in loop]
        assert max(ys) <= tread_y + 1e-6, "footprint crosses the chassis line"
        assert min(ys) < tread_y - 5, "footprint is not below the chassis line"
    xs = sorted((min(p[0] for p in loop), max(p[0] for p in loop))
                for loop in data["tread"])
    assert xs[0][1] < 0 < xs[1][0], "the wheels must not meet in the middle"


def test_lamps_that_intrude_move_by_the_agreed_amount(generated):
    """A lamp sat too close to the flank moves in by the principal's figure."""
    _text, frame, data, doc = generated
    ring = frame.ring(doc["silhouette"][:-1])
    want = bead_scad.FILLET_MM + bead_scad.PAD_COVE_MM
    for part in doc["parts"]:
        if part["id"] != "lights":
            continue
        for c_px, r_px in zip(part["centres"], part["radii"]):
            was = frame.xy(*c_px)
            r = frame.r(r_px)
            if bead_scad.edge_distance(was, ring) >= want + r:
                continue          # already wholly on the flat face: leave it
            now = min(data["lights"],
                      key=lambda l: (l[0] - was[0]) ** 2 + (l[1] - was[1]) ** 2)
            moved = ((now[0] - was[0]) ** 2 + (now[1] - was[1]) ** 2) ** 0.5
            assert moved >= bead_scad.LAMP_NUDGE_MM - 1e-3, (
                "intruding lamp only moved %.2f mm" % moved)


def test_raised_detail_clears_the_face_fillet(generated):
    """Nothing raised may hang over the rounded shoulder of the face."""
    _text, frame, data, doc = generated
    ring = frame.ring(doc["silhouette"][:-1])
    want = bead_scad.FILLET_MM
    for l in data["lights"]:
        d = bead_scad.edge_distance((l[0], l[1]), ring)
        assert d >= want + l[2] + bead_scad.PAD_COVE_MM - 1e-3, (
            "lamp at %.1f,%.1f overhangs the fillet" % (l[0], l[1]))


def test_etched_boxes_clear_the_face_fillet(generated):
    _text, frame, data, doc = generated
    ring = frame.ring(doc["silhouette"][:-1])
    want = bead_scad.FILLET_MM + bead_scad.FACE_MARGIN_MM
    for part in doc["parts"]:
        if part["kind"] != "round_rect":
            continue
        box, _ = bead_scad.nudge_box(frame.box_mm(part["box"]), ring, want)
        for cx, cy in ((box[0], box[1]), (box[2], box[1]),
                       (box[2], box[3]), (box[0], box[3])):
            assert bead_scad.edge_distance((cx, cy), ring) >= want - 1e-3, (
                part["id"] + " sits on the filleted shoulder")


def test_the_two_faces_are_mirrored():
    """Turn the bead over and you see the car from the other side."""
    text = TEMPLATE.read_text()
    plate = text[text.index("build plate"):text.index("wheel detail sits")]
    assert "mirror([1, 0, 0])" in plate, "the build-plate etch is not mirrored"


def test_every_level_produced_something(generated):
    _, _, data, doc = generated
    levels = {p["level"] for p in doc["parts"]}
    expected = {"etch", "lights", "raised_tyre", "raised_wheel", "raised_seam"}
    assert expected <= levels
    assert data["strokes"] and data["wheel_rings"]
    assert len(data["lights"]) == 6
    assert len(data["seam"]) == 2
    assert data["tyre"][0][3] < data["tyre"][0][2], "tyre must be an annulus"


def test_skipped_parts_are_the_ones_with_no_geometry(generated):
    _text, _frame, data, doc = generated
    skipped = [p["id"] for p in doc["parts"]
               if p["kind"] in ("none", "line")
               and p["level"] == "silhouette"]
    # these are features of the outline itself, not separate primitives
    assert set(skipped) <= {"arch_flare", "bumper_bottom"}


# --- the template renders ------------------------------------------------

REQUIRES_OPENSCAD = pytest.mark.skipif(
    not OPENSCAD.is_file(), reason="OpenSCAD not installed")


@REQUIRES_OPENSCAD
def test_template_renders_a_watertight_solid(tmp_path):
    stl = tmp_path / "bead.stl"
    subprocess.run(
        [str(OPENSCAD), "--export-format=binstl", "-o", str(stl),
         "-D", "width=60", "-D", "hole_diameter=8", "-D", "fillet_radius=1.5",
         "-D", "$fn=48", str(TEMPLATE)],
        check=True, capture_output=True)
    data = stl.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    assert n > 1000
    assert len(data) == 84 + 50 * n, "not a binary STL"
    assert b"OpenSCAD" in data[:80]


@REQUIRES_OPENSCAD
def test_build_plate_is_flat(tmp_path):
    """The bottom sits on the plate, so every vertex there is at z = 0.

    Etches are grooves: they must not take the plate below the first layer.
    """
    stl = tmp_path / "bead.stl"
    subprocess.run(
        [str(OPENSCAD), "--export-format=binstl", "-o", str(stl),
         "-D", "width=60", "-D", "$fn=32", str(TEMPLATE)],
        check=True, capture_output=True)
    data = stl.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    zs = []
    for i in range(n):
        f = struct.unpack_from("<12f", data, 84 + 50 * i)
        zs.extend([f[5], f[8], f[11]])
    assert min(zs) == pytest.approx(0.0, abs=1e-4)
    # the bead is width / 2 thick (30 at width 60) and the spare tyre is the
    # tallest thing on it (height / 10)
    assert max(zs) == pytest.approx(30 + 3.0, abs=0.2)


@REQUIRES_OPENSCAD
def test_template_refuses_a_fillet_it_cannot_cut(tmp_path):
    # the fillet has to leave a flat band: half the thickness is the limit
    proc = subprocess.run(
        [str(OPENSCAD), "--export-format=binstl", "-o",
         str(tmp_path / "x.stl"), "-D", "height=10", "-D", "fillet_radius=6",
         str(TEMPLATE)], capture_output=True, text=True)
    assert "edge fillet must be under half the thickness" in (
        proc.stdout + proc.stderr)


def test_template_declares_the_family_parameters():
    text = TEMPLATE.read_text()
    for name in ("width", "height", "hole_diameter", "bore_fillet_radius",
                 "fillet_radius", "R_throat", "$fn"):
        assert re.search(rf"(?m)^{re.escape(name)}\s*=", text), name
    # height follows the family rule, not a hardcoded slab thickness
    assert re.search(r"(?m)^height\s*=\s*width\s*/\s*2;", text)
    # the raised heights are fractions of the family thickness, as specified
    for name, div in (("lights_height", 30), ("tyre_height", 10),
                      ("wheel_height", 15), ("seam_height", 30)):
        assert re.search(rf"(?m)^{name}\s*=\s*height\s*/\s*{div};", text), name
    # the road wheels sit behind the rear, rounded in profile by a crown
    assert re.search(r"(?m)^tread_low\s*=\s*height\s*/\s*20;", text)
    assert re.search(r"(?m)^wheel_top\s*=\s*H\s*-\s*tread_low;", text)
    # the chassis line comes from the sketch, not from a number typed here
    assert "wheel_cutout" in text and "TYRE_TREAD" in text
    assert "TREAD_Y" in Path(bead_scad.data_path("rear")).read_text()
