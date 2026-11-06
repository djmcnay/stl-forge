#!/usr/bin/env python3
"""Geometry Playground tab: live star/petal sketch -> face-on PNG.

Drives the star/petal sketch functions in
projects/giant-beads/templates/bead_star.scad (star_2d, star_radius,
star_inner_ratio) WITHOUT re-implementing any maths in Python - the
.scad file is the single source of truth and duplicating it is a
maintenance defect. A tiny driver .scad written into the scratch dir
`use`s bead_star.scad, extrudes star_2d ~1 mm, and echoes the valley
ratio via star_inner_ratio (the cheap echo hook).

UX revision (principal's brief): NO Render button - each slider's
.change event renders live (sketch renders ~0.1 s), and a Reset button
restores the four file-spec defaults without rebuilding the widgets.
Layout mirrors the STL Forge tab: 50:50 columns - sliders + Reset +
readout on the left, ONLY the face-on PNG on the right.

Sub-app contract: create_tab() is used inside a gr.Blocks context
(master composes it under gr.Tab; standalone under __main__ on port
7865). Renders are fast and small: 1 mm extrusion, 512x512 PNG.
"""
from __future__ import annotations

import re
import sys
import traceback
from pathlib import Path

if __package__ in (None, ""):  # run directly: python sketch_tab/app.py
    _APP_DIR = Path(__file__).resolve().parents[1]
    if str(_APP_DIR) not in sys.path:
        sys.path.insert(0, str(_APP_DIR))

try:  # prefer the package import so app.shared stays a single module
    from ..shared import scad
except ImportError:
    from shared import scad

import gradio as gr

STANDALONE_PORT = 7865
SKETCH_PNG = "sketch_star_faceon.png"
DRIVER_SCAD = "sketch_driver.scad"

# Fixed dials (the principal's spec for designing the flower bead) -
# also the single source of the Reset defaults below.
SLIDERS = [
    # (name, min, max, default, step)
    ("width", 20, 240, 120, 1),
    ("points", 3, 24, 5, 1),
    ("roundness", 1, 20, 12, 1),
    ("petal_depth", 1, 10, 3, 1),
]
SLIDER_DEFAULTS = [row[3] for row in SLIDERS]
SLIDER_INFO = {
    "width": "enclosing-circle diameter (mm)",
    "points": "number of tips/petals (integer)",
    "roundness": "1 = sharp star, 10 = bulbous, 20 = flower",
    "petal_depth": "valley depth",
}

_DRIVER_TEMPLATE = """\
// Geometry Playground driver - star_2d outline extruded ~1 mm.
// Definitions come from bead_star.scad via use<>: the .scad functions
// (star_2d / star_radius / star_inner_ratio) stay the single source of
// truth; nothing is re-implemented here. -D flags override the values
// below per render.
use <{star_path}>
width = 120;
points = 5;
roundness = 12;
petal_depth = 3;
echo(valley_ratio = star_inner_ratio(points, petal_depth));
linear_extrude(height = 1)
    star_2d(diameter = width, points = points,
            roundness = roundness, depth = petal_depth);
"""

_ECHO_RE = re.compile(r"ECHO:\s*valley_ratio\s*=\s*(-?[\d.]+(?:[eE][+-]?\d+)?)")


def run_sketch_render(width: float, points: float, roundness: float,
                      petal_depth: float) -> dict:
    """Render one face-on sketch PNG (handler-level, no UI needed).

    Returns {"png", "valley_ratio" (float | None), "line"}. Writes ONLY
    into the scratch dir (driver + PNG). Raises scad.RenderError on
    OpenSCAD failure.
    """
    scad.SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    driver = scad.SCRATCH_DIR / DRIVER_SCAD
    driver.write_text(
        _DRIVER_TEMPLATE.format(
            star_path=str(scad.template_path("bead_star")).replace("\\", "/")),
        encoding="utf-8")
    png = scad.SCRATCH_DIR / SKETCH_PNG
    proc = scad._run(
        ["-o", str(png), "--imgsize=512,512", "--autocenter", "--viewall",
         "--camera", scad.CAMERA_FACEON, str(driver)]
        + scad.format_d_args({"width": width, "points": points,
                              "roundness": roundness,
                              "petal_depth": petal_depth}),
        "sketch face-on PNG")
    m = _ECHO_RE.search((proc.stdout or "") + (proc.stderr or ""))
    valley = float(m.group(1)) if m else None
    size = png.stat().st_size
    line = (f"valley ratio {valley:.4f} \u00b7 {size:,} bytes \u00b7 {png.name}"
            if valley is not None else
            f"{size:,} bytes \u00b7 {png.name} (no echo hook found)")
    return {"png": str(png), "valley_ratio": valley, "line": line}


def on_sketch(width, points, roundness, petal_depth):
    """Gradio change handler: errors surface in the readout, never crash;
    gr.update() keeps the previous PNG on screen."""
    try:
        result = run_sketch_render(width, points, roundness, petal_depth)
    except scad.RenderError as e:
        return gr.update(), f"\u26a0 OpenSCAD render failed\n{e}"
    except Exception as e:  # noqa: BLE001 - last-ditch, still no crash
        return gr.update(), (f"\u26a0 render failed: {e}"
                             f"\n{traceback.format_exc()[-400:]}")
    return result["png"], f"\u2713 sketch \u00b7 {result['line']}"


def on_reset():
    """Gradio click handler for Reset: the SLIDERS spec's file defaults
    back into the SAME four widgets (no rebuild) + a re-render at those
    defaults. No exception escapes; failures surface in the readout."""
    try:
        result = run_sketch_render(*SLIDER_DEFAULTS)
        png, line = result["png"], (f"\u2713 sketch reset \u00b7 "
                                    f"{result['line']}")
    except scad.RenderError as e:
        png, line = gr.update(), f"\u26a0 OpenSCAD render failed\n{e}"
    except Exception as e:  # noqa: BLE001 - last-ditch, still no crash
        png, line = gr.update(), f"\u26a0 reset render failed: {e}"
    return [*SLIDER_DEFAULTS, png, line]


def create_tab() -> dict:
    """Build this tab inside the ACTIVE gr.Blocks context.

    50:50 columns like the STL Forge tab: LEFT = the four sliders, the
    Reset button and the readout; RIGHT = ONLY the face-on PNG. Every
    slider's .change renders live - there is no Render button.
    """
    # Boot-time defaults render so the view is never empty on first load.
    try:
        boot = run_sketch_render(*SLIDER_DEFAULTS)
        boot_png, boot_line = boot["png"], f"\u2713 sketch \u00b7 {boot['line']}"
    except Exception as e:  # noqa: BLE001 - boot never crashes the app
        boot_png, boot_line = None, f"\u26a0 sketch boot render failed: {e}"

    with gr.Row():
        with gr.Column(scale=1, min_width=320):
            sliders = [
                gr.Slider(minimum=lo, maximum=hi, value=dflt, step=step,
                          label=name, info=SLIDER_INFO[name])
                for name, lo, hi, dflt, step in SLIDERS]
            reset_btn = gr.Button("Reset sketch", variant="secondary")
            readout = gr.Textbox(label="Readout", lines=2, value=boot_line)
        with gr.Column(scale=1, min_width=320):
            sketch_png = gr.Image(
                type="filepath", value=boot_png,
                label="Face-on outline (star_2d extruded 1 mm)")

    for slider in sliders:  # live render: no Render button
        slider.change(on_sketch, inputs=sliders,
                      outputs=[sketch_png, readout],
                      trigger_mode="always_last")
    reset_btn.click(on_reset, inputs=None,
                    outputs=[*sliders, sketch_png, readout])

    return {"sliders": sliders, "reset": reset_btn,
            "png": sketch_png, "readout": readout}


if __name__ == "__main__":  # standalone run of this tab only
    with gr.Blocks(title="Geometry Playground") as demo:
        gr.Markdown("## Geometry Playground\n"
                    "Dial the star/petal sketch from bead_star.scad - every "
                    "slider change renders the face-on outline instantly. "
                    "Reset puts the file defaults back.")
        create_tab()
    demo.queue().launch(server_name="127.0.0.1",
                        server_port=STANDALONE_PORT,
                        allowed_paths=[str(scad.SCRATCH_DIR),
                                       str(scad.TEMPLATES_DIR)])
