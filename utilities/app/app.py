#!/usr/bin/env python3
"""stl-forge app: master Blocks composition of the two tabs.

Composes the STL Forge and Geometry Playground tabs (each a module
exporting create_tab(), per the sub-app contract) into one control
panel and serves it on 127.0.0.1:7863 with allowed_paths for every
served directory. Renders land only in app/.render-scratch/.

Run:  utilities/app/.venv/bin/python utilities/app/app.py   (from the repo root)
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    _APP_DIR = Path(__file__).resolve().parent
    if str(_APP_DIR) not in sys.path:
        sys.path.insert(0, str(_APP_DIR))
    try:  # prefer the package-relative side so modules stay singletons
        from app.forge_tab.app import create_tab as forge_create_tab
        from app.sketch_tab.app import create_tab as sketch_create_tab
        from app.shared import scad
    except ImportError:
        from forge_tab.app import create_tab as forge_create_tab
        from sketch_tab.app import create_tab as sketch_create_tab
        from shared import scad
else:
    from .forge_tab.app import create_tab as forge_create_tab
    from .sketch_tab.app import create_tab as sketch_create_tab
    from .shared import scad

import gradio as gr

PORT = 7863
TITLE = "stl-forge"


def build_demo() -> gr.Blocks:
    with gr.Blocks(title=TITLE) as demo:
        gr.Markdown("# ⚒ STL-forge\n"
                    "Control panel for the giant-beads templates. "
                    "Renders go to `app/.render-scratch/`, never to a "
                    "project output folder.")
        with gr.Tab("STL-forge"):
            forge_create_tab()
        with gr.Tab("Geometry Playground"):
            sketch_create_tab()
    return demo


if __name__ == "__main__":
    demo = build_demo()
    demo.queue()
    demo.launch(server_name="127.0.0.1", server_port=PORT,
                allowed_paths=[str(scad.SCRATCH_DIR),
                               str(scad.TEMPLATES_DIR)])
