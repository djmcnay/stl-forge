"""The view contract: every elevation is data, and the engines stay generic.

These tests exist because the pipeline has to survive being extended - the
principal intends to trace the side and the front the same way.  If a view is
half-finished, or if view numbers creep back into an engine, that must fail
here rather than at render time on someone's third attempt.
"""
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import levels        # noqa: E402
import viewdata      # noqa: E402


@pytest.fixture(scope="module")
def rear():
    return viewdata.load("rear")


def test_at_least_one_view_is_available():
    assert "rear" in viewdata.available()


@pytest.mark.parametrize("name", viewdata.available())
def test_view_satisfies_the_contract(name):
    view = viewdata.load(name)
    assert view.NAME == name
    for key in viewdata.REQUIRED:
        assert hasattr(view, key), key


def test_view_files_exist(rear):
    for path in (rear.OVERLAY, rear.PHOTO):
        assert Path(path).is_file(), path


def test_view_roles_are_known_levels(rear):
    for part in rear.PARTS:
        assert part["role"] in levels.ROLE_COLOUR, part["id"]
        assert part["name"], part["id"]
        assert part["probes"], part["id"]


def test_sketch_parts_use_sketch_levels(rear):
    parts = rear.build_parts()
    assert parts
    ids = [p["id"] for p in parts]
    assert len(ids) == len(set(ids)), "duplicate part id"
    for part in parts:
        assert part["level"] in levels.LEVEL_COLOUR, part["id"]


def test_edits_are_described_in_words(rear):
    # every edit on the ink must be readable on the sheets, or the principal
    # cannot check it
    assert rear.EDITS_REMOVED and rear.EDITS_ADDED
    text = " ".join(rear.EDITS_NOTES)
    assert "roof inner panel line" in text


def test_silhouette_is_a_closed_polygon():
    import bead_sketch
    sil = bead_sketch.silhouette_polygon()
    assert len(sil) > 20
    first, last = sil[0], sil[-1]
    assert abs(first[0] - last[0]) < 1e-6 and abs(first[1] - last[1]) < 1e-6
    area = 0.0
    for (x0, y0), (x1, y1) in zip(sil, sil[1:]):
        area += x0 * y1 - x1 * y0
    assert abs(area) / 2 > 1e5, "silhouette collapsed"


@pytest.mark.parametrize("engine", ["part_map.py", "bead_sketch.py"])
def test_engines_carry_no_view_data(engine, rear):
    src = (TOOLS / engine).read_text()
    # the data blocks belong to the view module
    for marker in ("BODY_EDGE = [", "FLARE_WEDGES = [", "PARTS = [",
                   "def build_parts"):
        assert marker not in src, marker
    # and no path or filename of a particular elevation
    assert Path(rear.OVERLAY).name not in src
    assert Path(rear.PHOTO).name not in src
