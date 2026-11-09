"""Spec parsing / normalisation tests for giant-beads main.py (no renders)."""
import json
from pathlib import Path

import pytest

from conftest import load_main, PROJECT_DIR

gbmain = load_main()


# --- letters: normalisation + unique-letter dedup, order preserved -------

def test_normalise_word_strips_separators_keeps_order():
    assert gbmain.normalise_word("C A M I L A") == "CAMILA"
    assert gbmain.normalise_word("camila") == "CAMILA"
    assert gbmain.normalise_word("A-B, C!") == "ABC"
    assert gbmain.normalise_word("") == ""
    assert gbmain.normalise_word("123 21") == ""


def test_dedupe_letters_preserves_first_occurrence_order():
    assert gbmain.dedupe_letters("CAMILA") == ["C", "A", "M", "I", "L"]
    assert gbmain.dedupe_letters("ABBA") == ["A", "B"]
    assert gbmain.dedupe_letters("AAAA") == ["A"]
    assert gbmain.dedupe_letters("") == []


def test_letters_full_pipeline_dedupes():
    word = gbmain.normalise_word("C A M I L A")
    assert len(gbmain.dedupe_letters(word)) == 5


# --- parts: mapping to template + overrides ------------------------------

def test_parse_parts_maps_all_three():
    jobs = gbmain.parse_parts("heart,star,flower")
    assert [(name, tmpl) for name, tmpl, _ in jobs] == [
        ("heart", "bead_heart.scad"),
        ("star", "bead_star.scad"),
        ("flower", "bead_star.scad"),
    ]
    overrides = dict(jobs[2][2])
    assert overrides == {"roundness": 20, "petal_depth": 3}
    assert jobs[0][2] == {} and jobs[1][2] == {}


def test_parse_parts_maps_spacer_wide():
    jobs = gbmain.parse_parts("spacer_wide")
    assert [(name, tmpl) for name, tmpl, _ in jobs] == [
        ("spacer_wide", "bead_spacer_wide.scad"),
    ]
    assert jobs[0][2] == {}


def test_parse_parts_harmless_if_empty():
    assert gbmain.parse_parts(None) == []
    assert gbmain.parse_parts("") == []


def test_parse_parts_rejects_unknown():
    with pytest.raises(ValueError):
        gbmain.parse_parts("heart,cone")


# --- save_to default resolution ------------------------------------------

def test_resolve_save_to_default_is_downloads(monkeypatch):
    monkeypatch.setenv("HOME", "/tmp/fake-home")
    assert gbmain.resolve_save_to(None) == Path("/tmp/fake-home/Downloads")


def test_resolve_save_to_explicit_path_wins():
    assert gbmain.resolve_save_to("/tmp/explicit-dir") == Path("/tmp/explicit-dir")


# --- output naming rules --------------------------------------------------

def test_output_naming():
    assert gbmain.merged_stl_name("CAMILA") == "beads_CAMILA.stl"
    assert gbmain.part_stl_name("heart") == "bead_heart.stl"
    assert gbmain.part_stl_name("star") == "bead_star.stl"
    assert gbmain.part_stl_name("flower") == "bead_flower.stl"
    assert gbmain.part_stl_name("spacer_wide") == "bead_spacer_wide.stl"


# --- --spec alternate input form ------------------------------------------

def test_spec_fields_then_flags_precedence():
    ns = gbmain.parse_args([
        "--spec", json.dumps({"letters": "CAMILA", "width": 100,
                              "save_to": "/tmp/from-spec"}),
        "--width", "120",
    ])
    cfg = gbmain.config_from_args(ns)
    assert cfg.letters == "CAMILA"
    assert cfg.width == 120          # explicit flag overrides the spec
    assert cfg.save_to == "/tmp/from-spec"  # spec passes through


def test_spec_rejects_unknown_keys():
    ns = gbmain.parse_args(["--spec", '{"colour": "red"}'])
    with pytest.raises(ValueError):
        gbmain.config_from_args(ns)


def test_spec_key_names_exact():
    ns = gbmain.parse_args([
        "--spec", json.dumps({"parts": "heart", "preset": "bead_D"})])
    cfg = gbmain.config_from_args(ns)
    assert cfg.parts == "heart"
    assert cfg.preset == "bead_D"


# --- presets file ----------------------------------------------------------

def test_project_presets_only_beads():
    data = json.loads(
        (PROJECT_DIR / "presets.json").read_text(encoding="utf-8"))
    presets = data["presets"]
    assert sorted(presets) == ["bead_D", "bead_default", "bead_smooth"]
    for name, p in presets.items():
        assert p["template"].startswith("bead")
        if name != "bead_smooth":
            assert p["hole_diameter"] == 20
            assert p["width"] == 120


# --- STL validation rule ---------------------------------------------------

def _fake_binary_stl(path: Path, n_facets: int, header: bytes = None):
    # OpenSCAD's own binstl header ("OpenSCAD Model") is what real
    # artefacts carry; the word-merge writer emits a "solid ..." header.
    header = header if header is not None else b"OpenSCAD Model"
    header = header + b"\0" * (80 - len(header))
    body = bytes(range(50)) * n_facets
    import struct
    path.write_bytes(
        header + struct.pack("<I", n_facets) + body)


def test_validate_binary_stl_accepts_wellformed(tmp_path):
    for header in (b"OpenSCAD Model",
                   b"solid giant-beads row-layout (bin)"):
        stl = tmp_path / f"ok_{abs(hash(header))}.stl"
        _fake_binary_stl(stl, 2, header=header)
        assert gbmain.validate_binary_stl(stl) is None


def test_validate_binary_stl_rejects_bad(tmp_path):
    ascii_stl = tmp_path / "ascii.stl"
    ascii_stl.write_bytes(
        b"solid ascii\n facet normal 0 0 1\n  outer loop\n"
        * 100)
    assert "not a binary" in gbmain.validate_binary_stl(ascii_stl)

    truncated = tmp_path / "trunc.stl"
    _fake_binary_stl(truncated, 5)
    data = truncated.read_bytes()[:-10]
    truncated.write_bytes(data)
    assert "84 + 50" in gbmain.validate_binary_stl(truncated)

    zero = tmp_path / "zero.stl"
    _fake_binary_stl(zero, 0)
    assert "facet count" in gbmain.validate_binary_stl(zero)

    missing = tmp_path / "absent.stl"
    err = gbmain.validate_binary_stl(missing)
    assert err and "missing" in err
