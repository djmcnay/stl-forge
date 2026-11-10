"""The giant-bead family: defaults, effective parameters, and renders.

The app is deliberately a thin layer over the .scad templates.  This
module owns the family rules (which parameters are global, which are
per-bead, and how a bead's effective parameters are assembled) plus the
OpenSCAD render/cache and the family zip.  It knows nothing about
Gradio, so the family logic can be tested without a browser.

Global family size = width + string-hole diameter.  Every bead inherits
both; a bead may override either one without changing its siblings.
Height is a family rule, not a free dial:

    letter / bear / heart / star   height = width / 2
    doughnut spacer         height = width / 4
    shallot spacer          height = width
    Defender profile / rear        height = 30

That keeps the eight templates proportional and honours the assertions
inside the .scad files.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

try:  # package import (normal app run)
    from .shared import scad
except ImportError:  # direct run: python app/app.py
    from shared import scad

DEFAULTS_FILE = scad.PROJECT_DIR / "param-defaults.json"
_DEFAULTS = json.loads(DEFAULTS_FILE.read_text(encoding="utf-8"))

_TEMPLATE_DEFAULTS = {
    stem: {p.name: p.value for p in scad.parse_template_params(stem)}
    for stem in (
        "bead",
        "bead_bear",
        "bead_defender_profile",
        "bead_defender_rear",
        "bead_heart",
        "bead_star",
        "bead_spacer_small",
        "bead_spacer_wide",
    )
}

DEFAULT_WIDTH = int(_DEFAULTS["main_defaults"]["width"])
DEFAULT_HOLE = float(_DEFAULTS["bead_scad"]["hole_diameter"])
FAMILY_ZIP = "giant-bead-family.zip"


def _td(template: str, name: str):
    """Template default for a literal declaration."""
    return _TEMPLATE_DEFAULTS[template][name]


def _json_default(template: str, name: str):
    """JSON-contract default for a derived or snapshot value."""
    return _DEFAULTS[template][name]


def fmt_num(value: float | int) -> str:
    """Compact human number: 120, 60, 9.375, 2.5."""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    text = f"{number:.3f}".rstrip("0").rstrip(".")
    return text or "0"


@dataclass(frozen=True)
class ControlSpec:
    """One native control in a bead's settings panel."""

    key: str
    kind: str  # slider | text | dropdown | checkbox
    label: str
    info: str = ""
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    choices: tuple[str, ...] = ()
    default: Any = None
    integer: bool = False
    pass_to_scad: bool = True


@dataclass(frozen=True)
class BeadSpec:
    """A bead option and its per-bead (non-global) controls."""

    slug: str
    label: str
    template: str
    blurb: str
    output: str
    controls: tuple[ControlSpec, ...]
    fixed: tuple[tuple[str, Any], ...] = ()
    kind: str = "letter"  # letter | doughnut | shallot

    @property
    def fixed_params(self) -> dict[str, Any]:
        return dict(self.fixed)


BEADS: tuple[BeadSpec, ...] = (
    BeadSpec(
        slug="letter",
        label="Letter bead",
        template="bead.scad",
        blurb="A round bead with the same letter on both flat faces.",
        output="giant-bead-letter.stl",
        fixed=(("part", "body"),),
        controls=(
            ControlSpec(
                "letter_top", "text", "Letter",
                "Top face. The bottom repeats it.",
                default=_td("bead", "letter_top"),
            ),
            ControlSpec(
                "letter_font", "dropdown", "Typeface",
                "Use a font installed on this machine.",
                choices=(
                    "Arial Rounded MT Bold",
                    "Arial",
                    "Courier",
                    "Times New Roman",
                ),
                default=_td("bead", "letter_font"),
            ),
            ControlSpec(
                "letter_space", "slider", "Letter size",
                "Letter fits a circle of width x this.",
                minimum=0.35, maximum=0.80, step=0.05,
                default=_td("bead", "letter_space"),
            ),
            ControlSpec(
                "letter_bold", "slider", "Weight",
                "Faux bold, millimetres per side.",
                minimum=0.0, maximum=2.0, step=0.1,
                default=_td("bead", "letter_bold"),
            ),
        ),
    ),
    BeadSpec(
        slug="bear",
        label="Bear bead",
        template="bead_bear.scad",
        blurb="A broad bear face with a raised muzzle and eyes and etched features.",
        output="giant-bead-bear.stl",
        controls=(
            ControlSpec(
                "ear_size", "slider", "Ear size",
                "Scales the ears and their inner-ear pockets.",
                minimum=0.80, maximum=1.20, step=0.05,
                default=_td("bead_bear", "ear_size"),
            ),
            ControlSpec(
                "eye_spacing", "slider", "Eye spacing",
                "Moves the eyes apart without changing their size.",
                minimum=0.80, maximum=1.20, step=0.05,
                default=_td("bead_bear", "eye_spacing"),
            ),
            ControlSpec(
                "muzzle_size", "slider", "Muzzle size",
                "Scales the muzzle and its nose and mouth.",
                minimum=0.85, maximum=1.15, step=0.05,
                default=_td("bead_bear", "muzzle_size"),
            ),
            ControlSpec(
                "detail_relief", "slider", "Detail relief",
                "Scales the recessed and raised face details.",
                minimum=0.50, maximum=1.50, step=0.10,
                default=_td("bead_bear", "detail_relief"),
            ),
        ),
    ),
    BeadSpec(
        slug="defender_profile",
        label="Defender profile",
        template="bead_defender_profile.scad",
        blurb="A Defender 90 side silhouette with etched windows, doors and steel wheels.",
        output="giant-bead-defender-profile.stl",
        kind="defender_profile",
        controls=(
            ControlSpec(
                "fillet_radius", "slider", "Edge fillet",
                "Gentle face and bottom fillet, mm.",
                minimum=2.0, maximum=8.0, step=0.5,
                default=_td("bead_defender_profile", "fillet_radius"),
            ),
            ControlSpec(
                "detail_relief", "slider", "Etch depth",
                "Scales the door, window and wheel grooves.",
                minimum=0.50, maximum=1.50, step=0.10,
                default=_td("bead_defender_profile", "detail_relief"),
            ),
        ),
    ),
    BeadSpec(
        slug="defender_rear",
        label="Defender rear",
        template="bead_defender_rear.scad",
        blurb="A Defender 90 rear end with a spare wheel, lights and rear-door etches.",
        output="giant-bead-defender-rear.stl",
        kind="defender_rear",
        controls=(
            ControlSpec(
                "fillet_radius", "slider", "Edge fillet",
                "Gentle face and bottom fillet, mm.",
                minimum=2.0, maximum=8.0, step=0.5,
                default=_td("bead_defender_rear", "fillet_radius"),
            ),
            ControlSpec(
                "detail_relief", "slider", "Etch depth",
                "Scales the rear-door, light and spare-wheel grooves.",
                minimum=0.50, maximum=1.50, step=0.10,
                default=_td("bead_defender_rear", "detail_relief"),
            ),
        ),
    ),
    BeadSpec(
        slug="heart",
        label="Heart bead",
        template="bead_heart.scad",
        blurb="A heart face with the family's softened edge.",
        output="giant-bead-heart.stl",
        controls=(
            ControlSpec(
                "roundness", "slider", "Roundness",
                "1 is sharp and elongated; 10 is a full bubble.",
                minimum=1, maximum=10, step=1,
                default=_td("bead_heart", "roundness"),
                integer=True,
            ),
        ),
    ),
    BeadSpec(
        slug="star",
        label="Star bead",
        template="bead_star.scad",
        blurb="A star that can be dialled all the way into a flower.",
        output="giant-bead-star.stl",
        controls=(
            ControlSpec(
                "roundness", "slider", "Roundness",
                "1 sharp star, 10 bulbous, 20 flower.",
                minimum=1, maximum=20, step=1,
                default=_td("bead_star", "roundness"),
                integer=True,
            ),
            ControlSpec(
                "points", "slider", "Points",
                "Number of tips or petals.",
                minimum=3, maximum=16, step=1,
                default=_td("bead_star", "points"),
                integer=True,
            ),
            ControlSpec(
                "petal_depth", "slider", "Petal depth",
                "How far the valleys cut inward.",
                minimum=1, maximum=10, step=1,
                default=_td("bead_star", "petal_depth"),
                integer=True,
            ),
        ),
    ),
    BeadSpec(
        slug="doughnut",
        label="Doughnut spacer",
        template="bead_spacer_small.scad",
        blurb="A squat ring with a filleted hole and a rounded outer edge.",
        output="giant-bead-doughnut.stl",
        kind="doughnut",
        controls=(
            ControlSpec(
                "curvature", "slider", "Outer curve",
                "0 is a flat washer, 0.5 medium, 1 a full doughnut.",
                minimum=0.0, maximum=1.0, step=0.05,
                default=_td("bead_spacer_small", "curvature"),
            ),
            ControlSpec(
                "match_mouth", "checkbox", "Match hole to outer edge",
                "On: the hole fillet follows the outer fillet automatically.",
                default=True,
                pass_to_scad=False,
            ),
            ControlSpec(
                "r_mouth", "slider", "Hole mouth fillet",
                "Off only: set the hole mouth radius independently.",
                minimum=0.5, maximum=15.0, step=0.25,
                default=_json_default("bead_spacer_small_scad", "r_mouth_eff"),
            ),
        ),
    ),
    BeadSpec(
        slug="shallot",
        label="Shallot spacer",
        template="bead_spacer_wide.scad",
        blurb="A tall barrel that swells at the middle like a banana shallot.",
        output="giant-bead-shallot.stl",
        kind="shallot",
        controls=(
            ControlSpec(
                "curvature", "slider", "Barrel curve",
                "2 is the shallot parabola; higher values fill the shoulders.",
                minimum=1.0, maximum=4.0, step=0.1,
                default=_td("bead_spacer_wide", "curvature"),
            ),
        ),
    ),
)

BEAD_BY_SLUG = {bead.slug: bead for bead in BEADS}
BEAD_SLUGS = tuple(bead.slug for bead in BEADS)


def default_params(bead: BeadSpec) -> dict[str, Any]:
    """Fresh per-bead parameter values from the template/JSON defaults."""
    return {c.key: copy.deepcopy(c.default) for c in bead.controls}


def default_state() -> dict[str, Any]:
    """The whole family in one JSON-friendly, per-session state dict."""
    return {
        "selected": "letter",
        "width": DEFAULT_WIDTH,
        "hole": DEFAULT_HOLE,
        "beads": {
            bead.slug: {
                "override": False,
                "width": DEFAULT_WIDTH,
                "hole": DEFAULT_HOLE,
                "params": default_params(bead),
            }
            for bead in BEADS
        },
    }


def effective_width(state: dict, slug: str) -> float:
    bead = state["beads"][slug]
    return float(bead["width"] if bead["override"] else state["width"])


def effective_hole(state: dict, slug: str) -> float:
    bead = state["beads"][slug]
    return float(bead["hole"] if bead["override"] else state["hole"])


def effective_params(state: dict, slug: str) -> dict[str, Any]:
    """OpenSCAD -D overrides for one bead at the current family settings."""
    bead_spec = BEAD_BY_SLUG[slug]
    bead_state = state["beads"][slug]
    params = bead_spec.fixed_params
    for control in bead_spec.controls:
        if not control.pass_to_scad:
            continue
        value = bead_state["params"].get(control.key, control.default)
        if control.integer:
            value = int(round(float(value)))
        elif control.kind == "slider":
            value = float(value)
        params[control.key] = value

    # The doughnut's mouth is auto (-1) unless the user explicitly opted
    # out of matching it to the outer edge.
    if slug == "doughnut":
        if bead_state["params"].get("match_mouth", True):
            params["r_mouth"] = -1
        else:
            params["r_mouth"] = float(bead_state["params"]["r_mouth"])

    params["width"] = effective_width(state, slug)
    params["hole_diameter"] = effective_hole(state, slug)
    return params


def bead_dimensions(slug: str, width: float) -> tuple[float, float]:
    """(face/outer diameter, height) for a bead at a given family width."""
    if slug == "shallot":
        return width / 2, width
    if slug == "doughnut":
        return width / 2, width / 4
    if slug in {"defender_profile", "defender_rear"}:
        return width, 30.0
    return width, width / 2


def bead_meta(state: dict, slug: str, result: "RenderResult") -> str:
    width = effective_width(state, slug)
    hole = effective_hole(state, slug)
    diameter, height = bead_dimensions(slug, width)
    if slug == "bear":
        size = f"{fmt_num(width)} mm cheek width × {fmt_num(height)} mm thick"
    elif slug == "defender_profile":
        size = (f"{fmt_num(width)} mm long × {fmt_num(width * 58 / 120)} mm tall"
                f" × {fmt_num(height)} mm thick")
    elif slug == "defender_rear":
        size = (f"{fmt_num(width)} mm wide × {fmt_num(width * 128 / 120)} mm tall"
                f" × {fmt_num(height)} mm thick")
    else:
        size = f"Ø{fmt_num(diameter)} × {fmt_num(height)} mm"
    return (
        f"{size}  ·  Ø{fmt_num(hole)} mm hole  \n"
        f"`{result.facets:,} facets · {scad.human_bytes(result.bytes)}"
        f" · {result.seconds:.1f} s`"
    )


def family_summary(width: float) -> str:
    """Markdown for the global height rule at the current family width."""
    return (
        "**Heights from this width**  \n"
        f"Letter, bear, heart, star **{fmt_num(width / 2)} mm**  \n"
        f"Doughnut **{fmt_num(width / 4)} mm** · "
        f"Shallot **{fmt_num(width)} mm**  \n"
        "Defender profile and rear **30 mm thick**"
    )


def params_key(params: dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


@dataclass
class RenderResult:
    slug: str
    path: Path
    facets: int
    bytes: int
    seconds: float
    params: dict[str, Any] = field(default_factory=dict)


_CACHE: dict[tuple[str, str, int], RenderResult] = {}


def render_bead(state: dict, slug: str, force: bool = False) -> RenderResult:
    """Render one bead into the scratch dir; reuse an identical render."""
    bead = BEAD_BY_SLUG[slug]
    params = effective_params(state, slug)
    stem = bead.template.removesuffix(".scad")
    template = scad.template_path(stem)
    mtime = int(template.stat().st_mtime)
    key = (slug, params_key(params), mtime)
    if not force and key in _CACHE:
        cached = _CACHE[key]
        if cached.path.is_file():
            return cached

    started = time.perf_counter()
    path = scad.render_stl(
        stem, params,
        out_path=scad.SCRATCH_DIR / bead.output,
    )
    seconds = time.perf_counter() - started
    facets, size = scad.probe_binary_stl(path)
    result = RenderResult(slug, path, facets, size, seconds, params)
    _CACHE[key] = result
    return result


def settings_text(state: dict) -> str:
    """Plain-text note bundled inside the family zip."""
    lines = [
        "Giant bead family",
        "=================",
        "",
        f"Family width : {fmt_num(state['width'])} mm",
        f"Family hole  : {fmt_num(state['hole'])} mm",
        "",
        "Height rule: letter/bear/heart/star = width/2, "
        "doughnut = width/4, shallot = width.",
        "Defender beads are 30 mm thick.",
        "",
    ]
    for bead in BEADS:
        width = effective_width(state, bead.slug)
        hole = effective_hole(state, bead.slug)
        diameter, height = bead_dimensions(bead.slug, width)
        overridden = bool(state["beads"][bead.slug]["override"])
        if bead.slug == "bear":
            size = f"{fmt_num(width)} mm cheek width x {fmt_num(height)} mm thick"
        elif bead.slug == "defender_profile":
            size = (f"{fmt_num(width)} mm long x {fmt_num(width * 58 / 120)} mm tall"
                    f" x {fmt_num(height)} mm thick")
        elif bead.slug == "defender_rear":
            size = (f"{fmt_num(width)} mm wide x {fmt_num(width * 128 / 120)} mm tall"
                    f" x {fmt_num(height)} mm thick")
        else:
            size = f"Ø{fmt_num(diameter)} x {fmt_num(height)} mm"
        lines += [
            f"{bead.label}  ({bead.template})",
            f"  size   : {size}",
            f"  hole   : Ø{fmt_num(hole)} mm",
            f"  size source: {'per-bead override' if overridden else 'family'}",
        ]
        auto_mouth = (
            bead.slug == "doughnut"
            and state["beads"][bead.slug]["params"].get(
                "match_mouth", True)
        )
        for key, value in sorted(
                effective_params(state, bead.slug).items()):
            if key in {"width", "hole_diameter"}:
                continue
            if key == "r_mouth" and auto_mouth:
                lines.append("  r_mouth: auto (matches the outer fillet)")
                continue
            lines.append(f"  {key}: {value}")
        lines.append("")
    return "\n".join(lines)


def build_family_zip(
        state: dict,
        progress: Callable[..., None] | None = None,
) -> tuple[Path, list[RenderResult]]:
    """Render all eight beads and return a ready-to-download zip."""
    results: list[RenderResult] = []
    total = len(BEADS)
    for index, bead in enumerate(BEADS, start=1):
        if progress:
            progress((index - 1) / total,
                     desc=f"Rendering {bead.label.lower()}…")
        results.append(render_bead(state, bead.slug))

    zip_path = scad.SCRATCH_DIR / FAMILY_ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for result in results:
            bead = BEAD_BY_SLUG[result.slug]
            archive.write(result.path, arcname=bead.output)
        archive.writestr("family-settings.txt", settings_text(state))
    if progress:
        progress(1.0, desc="Family zip ready")
    return zip_path, results


def error_text(exc: BaseException) -> str:
    """The full reason, for the collapsed render log."""
    return f"{type(exc).__name__}: {exc}"
