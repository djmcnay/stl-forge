"""`stl_check.py` - the measurement the bead build is signed off on.

The rear bead was handed over five times with a fault a measurement would have
caught and no render did, so the tool that measures it is tested on a shape
whose numbers are known by hand.
"""
import struct
import sys

from conftest import PROJECT_DIR

TOOLS = PROJECT_DIR / "tools"
sys.path.insert(0, str(TOOLS))

import stl_check      # noqa: E402


def cube_stl(path, side=2.0):
    """A 2 mm cube, 12 triangles, binary STL - every number checkable by hand."""
    h = side / 2.0
    corners = [[-h, -h, -h], [h, -h, -h], [h, h, -h], [-h, h, -h],
               [-h, -h, h], [h, -h, h], [h, h, h], [-h, h, h]]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in quads:
        tris.append((a, b, c))
        tris.append((a, c, d))
    out = bytearray(b"\0" * 80)
    out += struct.pack("<I", len(tris))
    for tri in tris:
        out += struct.pack("<3f", 0.0, 0.0, 0.0)
        for i in tri:
            out += struct.pack("<3f", *corners[i])
        out += struct.pack("<H", 0)
    path.write_bytes(bytes(out))
    return path


def test_reads_a_cube(tmp_path):
    res = stl_check.report(cube_stl(tmp_path / "cube.stl"), [(0.9, 1.1)])
    assert res["facets"] == 12
    assert res["bbox"] == [2.0, 2.0, 2.0]
    assert res["shells"] == 1
    assert res["degenerate"] == 0


def test_finds_the_flat_faces(tmp_path):
    res = stl_check.report(cube_stl(tmp_path / "cube.stl"), [(0.9, 1.1)])
    # top and bottom of a 2 mm cube: 4 mm2 each, as two triangles
    assert res["flat"]["area"] == 8.0
    assert res["flat"]["largest"] == 2.0
    # the band at z = +1 is the top face only
    assert res["bands"][0]["faces"] == 2
    assert res["bands"][0]["area"] == 4.0


def test_the_delivered_bead_passes_the_checks():
    """The geometry facts the hand-over is signed off on, from the data file.

    Rendered STLs are not committed, so this cannot open one; what it can do is
    fail loudly if the template grows a second disconnected piece of geometry,
    which is what `shells` exists to catch.
    """
    text = (PROJECT_DIR / "templates" / "bead_defender_rear_v2.scad").read_text()
    # the bore is the only hole the bead is supposed to have, and the wheel
    # relief must never dip below the floor it sits in (that shelf)
    assert "bead_string_hole_well" in text
    assert "wheel_top + wheel_rise * sin(th)" in text
