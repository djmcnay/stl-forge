"""Input-contract tests for the cards project.

These do not render anything; they guard the validated card data and the
derived box defaults against drift.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def test_poker_is_the_exact_imperial_size():
    poker = load("card-sizes.json")["cards"]["poker"]

    assert poker["width_mm"] == 63.5
    assert poker["height_mm"] == 88.9
    assert poker["nominal"] == {"width_mm": 63, "height_mm": 88}
    assert poker["imperial"]["width_in"] == 2.5
    assert poker["imperial"]["height_in"] == 3.5


def test_uno_junior_is_56_by_87_and_is_not_bridge():
    cards = load("card-sizes.json")["cards"]
    uno = cards["uno-junior"]
    bridge = cards["bridge"]

    assert (uno["width_mm"], uno["height_mm"]) == (56, 87)
    assert (bridge["width_mm"], bridge["height_mm"]) == (57, 89)
    assert uno["width_mm"] != bridge["width_mm"]
    assert uno["height_mm"] != bridge["height_mm"]


def test_corner_radii_are_in_the_industry_band():
    for name, card in load("card-sizes.json")["cards"].items():
        assert 3.0 <= card["corner_radius_mm"] <= 4.0, name


def test_box_internal_cavity_fits_the_card_and_deck():
    box = load("param-defaults.json")["uno_junior_box"]
    inner = box["derived_mm"]
    wall = box["wall_mm"]
    fit = box["fit_clearance_mm"]

    assert inner["inner_width"] == box["card_width_mm"] + fit
    assert inner["inner_depth"] == box["deck_thickness_mm"] + fit
    assert inner["inner_height"] == box["card_height_mm"] + fit
    assert inner["outer_width"] == inner["inner_width"] + 2 * wall
    assert inner["outer_depth"] == inner["inner_depth"] + 2 * wall
    assert inner["outer_height"] == inner["inner_height"] + wall

    # The card must enter, but not rattle.
    assert 0.4 <= inner["inner_width"] - box["card_width_mm"] <= 1.0
    assert 0.4 <= inner["inner_height"] - box["card_height_mm"] <= 1.0
    assert 0.4 <= inner["inner_depth"] - box["deck_thickness_mm"] <= 1.0


def test_box_details_are_physically_possible():
    box = load("param-defaults.json")["uno_junior_box"]
    inner = box["derived_mm"]

    # A chamfer deeper than the wall would break through.
    assert box["entry_chamfer_mm"] < box["wall_mm"]
    # The thumb arch is cut across the card width and must leave side rails.
    assert box["thumb_arch_radius_mm"] == box["thumb_arch_diameter_mm"] / 2
    assert box["thumb_arch_diameter_mm"] < inner["inner_width"]
    assert (inner["inner_width"] - box["thumb_arch_diameter_mm"]) / 2 >= 10
    assert box["thumb_arch_radius_mm"] < box["card_height_mm"]
    # The 45 mm badge must fit the front face with a margin.
    assert box["logo_width_mm"] < inner["outer_width"]
    assert box["logo_depth_mm"] < box["wall_mm"]


def test_preset_matches_the_canonical_defaults():
    preset = load("presets.json")["presets"]["uno-junior-box"]
    box = load("param-defaults.json")["uno_junior_box"]

    assert preset["template"] == "uno_junior_box.scad"
    for key, value in box["scad"].items():
        assert preset[key] == value, key


def test_scad_template_defaults_match_the_snapshot():
    text = (ROOT / "templates" / "uno_junior_box.scad").read_text()
    defaults = {}
    for match in re.finditer(
        r"^\s*([A-Za-z_]\w*)\s*=\s*(-?\d+(?:\.\d+)?)\s*;", text, re.MULTILINE
    ):
        defaults[match.group(1)] = float(match.group(2))

    box = load("param-defaults.json")["uno_junior_box"]["scad"]
    for key, value in box.items():
        assert defaults[key] == value, key


def test_generated_logo_module_is_present():
    logo = (ROOT / "templates" / "artemis_logo.scad").read_text()
    assert "module artemis_logo_2d()" in logo
    assert "ARTEMIS_LOGO_ARTWORK_W = 37.749023;" in logo
    assert "ARTEMIS_LOGO_ARTWORK_H =" in logo
