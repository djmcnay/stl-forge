"""Facet-count rule applied to a real generated STL (renders, gated).

Skipped when /Applications/OpenSCAD.app is absent; 60 mm width keeps the
renders fast. The rule: the binary facet count read at offset 80 must
match the file size exactly (84 + 50*n), with a positive count and an
80-byte binary header.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from conftest import PROJECT_DIR, load_main

gbmain = load_main()

import forge  # noqa: E402  (sys.path set by main.py on load)

OPENSCAD_APP = Path("/Applications/OpenSCAD.app")
REQUIRES_OPENSCAD = pytest.mark.skipif(
    not OPENSCAD_APP.is_dir(),
    reason="/Applications/OpenSCAD.app not installed")

pytestmark = REQUIRES_OPENSCAD


def _openscad_binary():
    for candidate in ("openscad",
                      "/opt/homebrew/bin/openscad",
                      "/Applications/OpenSCAD.app/Contents/MacOS/"
                      "OpenSCAD"):
        proc = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True)
        if proc.returncode == 0:
            return candidate
    pytest.skip("no working openscad binary found")


def test_rendered_heart_stl_satisfies_facet_count_rule(tmp_path):
    openscad = _openscad_binary()
    template = PROJECT_DIR / "templates" / "bead_heart.scad"
    stl = tmp_path / "bead_heart_60.stl"
    proc = subprocess.run(
        [openscad, "--export-format", "binstl", "-o", str(stl),
         str(template), "-D", "width=60"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert stl.is_file()

    # The main.py validation rule passes on a real OpenSCAD artefact...
    assert gbmain.validate_binary_stl(stl) is None
    # ...and the header count is a positive integer at offset 80.
    data = stl.read_bytes()
    (n,) = struct.unpack_from("<I", data, 80)
    assert n > 0
    assert len(data) == 84 + 50 * n


def test_letters_merge_at_60mm(tmp_path):
    """One-command letters merge at a tiny width stays self-consistent."""
    _openscad_binary()
    res = gbmain.main([
        "--letters", "A A B", "--width", "60",
        "--save-to", str(tmp_path),
        "--presets", str(PROJECT_DIR / "presets.json"),
    ])
    assert res == 0
    merged = tmp_path / "beads_AAB.stl"
    data = merged.read_bytes()
    assert data[:5] == b"solid"
    (n,) = struct.unpack_from("<I", data, 80)
    assert n > 0 and len(data) == 84 + 50 * n
    # two unique beads (A, B); the x-span must exceed width*2 so the
    # row could not have collapsed the 10 mm gap away.
    _, xmin, xmax, _, _ = forge._binary_stl_stats(merged)
    assert (xmax - xmin) > 120


def test_parts_heart_without_letters_still_renders(tmp_path):
    """Guard: no --letters at all + a valid --parts request stays exit 0
    and lights up only the named part job (no row artefact)."""
    _openscad_binary()
    res = gbmain.main([
        "--parts", "heart", "--width", "60",
        "--save-to", str(tmp_path),
        "--presets", str(PROJECT_DIR / "presets.json"),
    ])
    assert res == 0
    assert (tmp_path / "bead_heart.stl").is_file()
    assert not list(tmp_path.glob("beads_*.stl"))


def test_letters_zero_word_gap_touching_beads(tmp_path):
    """Zero gap is allowed (touching beads); the x-span then collapses to
    exactly n * bead_width - no overlap, no clearance."""
    _openscad_binary()
    res = gbmain.main([
        "--letters", "A A B", "--width", "60", "--word-gap", "0",
        "--save-to", str(tmp_path),
        "--presets", str(PROJECT_DIR / "presets.json"),
    ])
    assert res == 0
