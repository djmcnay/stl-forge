"""Pure family-contract tests for the giant-beads Gradio app.

No Gradio import and no OpenSCAD render: these cover the rules the UI
depends on (global values, per-bead overrides, family heights, and the
doughnut's automatic mouth) so the app cannot drift from the templates.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app import family  # noqa: E402


def test_family_has_the_eight_requested_beads():
    assert family.BEAD_SLUGS == (
        "letter", "bear", "defender_profile", "defender_rear",
        "heart", "star", "doughnut", "shallot")


def test_default_state_is_the_family_defaults():
    state = family.default_state()
    assert state["width"] == 120
    assert state["hole"] == 20
    assert state["selected"] == "letter"
    assert set(state["beads"]) == set(family.BEAD_SLUGS)


def test_global_width_and_hole_flow_to_every_bead():
    state = family.default_state()
    state["width"] = 160
    state["hole"] = 25
    for slug in family.BEAD_SLUGS:
        params = family.effective_params(state, slug)
        assert params["width"] == 160
        assert params["hole_diameter"] == 25


def test_per_bead_override_does_not_leak_to_siblings():
    state = family.default_state()
    state["width"] = 160
    state["hole"] = 25
    state["beads"]["shallot"].update(
        override=True, width=200, hole=30)

    assert family.effective_width(state, "shallot") == 200
    assert family.effective_hole(state, "shallot") == 30
    assert family.effective_width(state, "letter") == 160
    assert family.effective_hole(state, "heart") == 25
    assert family.effective_width(state, "star") == 160


def test_family_height_rules_are_proportional():
    assert family.bead_dimensions("letter", 120) == (120, 60)
    assert family.bead_dimensions("bear", 120) == (120, 60)
    assert family.bead_dimensions("defender_profile", 120) == (120, 30)
    assert family.bead_dimensions("defender_rear", 120) == (120, 30)
    assert family.bead_dimensions("heart", 120) == (120, 60)
    assert family.bead_dimensions("star", 120) == (120, 60)
    assert family.bead_dimensions("doughnut", 120) == (60, 30)
    assert family.bead_dimensions("shallot", 120) == (60, 120)
    assert family.bead_dimensions("shallot", 160) == (80, 160)


def test_doughnut_mouth_matches_outer_edge_by_default():
    state = family.default_state()
    assert family.effective_params(state, "doughnut")["r_mouth"] == -1


def test_doughnut_mouth_can_be_independent():
    state = family.default_state()
    state["beads"]["doughnut"]["params"]["match_mouth"] = False
    state["beads"]["doughnut"]["params"]["r_mouth"] = 7.5
    assert family.effective_params(state, "doughnut")["r_mouth"] == 7.5


def test_family_summary_tracks_width():
    summary = family.family_summary(120)
    assert "bear" in summary
    assert "Defender" in summary
    assert "60 mm" in summary
    assert "30 mm" in summary
    assert "120 mm" in summary


def test_default_controls_do_not_duplicate_global_size():
    for bead in family.BEADS:
        keys = {control.key for control in bead.controls}
        assert "width" not in keys
        assert "hole_diameter" not in keys


def test_settings_note_records_a_per_bead_override():
    state = family.default_state()
    state["beads"]["shallot"].update(override=True, width=200, hole=30)
    note = family.settings_text(state)
    assert "Shallot spacer" in note
    assert "per-bead override" in note
    assert "Ø100 x 200 mm" in note


def test_settings_note_marks_the_automatic_doughnut_mouth():
    note = family.settings_text(family.default_state())
    assert "r_mouth: auto (matches the outer fillet)" in note


def test_settings_note_uses_bear_width_and_thickness():
    note = family.settings_text(family.default_state())
    assert "Bear bead" in note
    assert "120 mm cheek width x 60 mm thick" in note
