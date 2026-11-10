"""The generated bead data, and the bead built from it.

Two things are guarded here:

1. `templates/bead_defender_<view>_data.scad` must be exactly what
   `tools/bead_scad.py` produces from the committed sketch JSON.  A stale data
   file would silently build last week's shape.
2. The template must render as a watertight solid at family defaults, so a
   broken primitive fails here rather than in the slicer.
"""
import json
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
         "-D", "width=60", "-D", "height=15", "-D", "hole_diameter=8",
         "-D", "fillet_radius=1.5", "-D", "$fn=48", str(TEMPLATE)],
        check=True, capture_output=True)
    data = stl.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    assert n > 1000
    assert len(data) == 84 + 50 * n, "not a binary STL"
    assert b"OpenSCAD" in data[:80]


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
    # the raised heights are fractions of the family thickness, as specified
    for name, div in (("lights_height", 20), ("tyre_height", 10),
                      ("wheel_height", 15), ("seam_height", 20)):
        assert re.search(rf"(?m)^{name}\s*=\s*height\s*/\s*{div};", text), name
