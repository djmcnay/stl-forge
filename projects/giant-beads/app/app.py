#!/usr/bin/env python3
"""Giant beads: a native-Gradio bench for the five-bead family.

The page has three jobs, in order: set the shared family size, shape one
bead, take the STLs.  The family values live in the left column, the
selected bead's shape controls in the right, and the orbit view in the
middle.  A per-bead size override is available without disturbing its
siblings.

Everything renders through the project's .scad templates via the
OpenSCAD CLI.  The app writes only into gitignored
`app/.render-scratch/`; downloads go through the browser's own download
folder (gr.DownloadButton).  No custom HTML or JavaScript.

Run from the repo root:

    projects/giant-beads/app/.venv/bin/python \
        projects/giant-beads/app/app.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

if __package__ in (None, ""):
    _APP_DIR = Path(__file__).resolve().parent
    if str(_APP_DIR) not in sys.path:
        sys.path.insert(0, str(_APP_DIR))
    from family import (  # type: ignore[no-redef]
        BEADS,
        BEAD_BY_SLUG,
        DEFAULT_HOLE,
        DEFAULT_WIDTH,
        bead_meta,
        bead_title,
        build_family_zip,
        default_params,
        default_state,
        error_text,
        family_summary,
        render_bead,
    )
    from shared import scad  # type: ignore[no-redef]
    from theme import theme  # type: ignore[no-redef]
else:
    from .family import (
        BEADS,
        BEAD_BY_SLUG,
        DEFAULT_HOLE,
        DEFAULT_WIDTH,
        bead_meta,
        bead_title,
        build_family_zip,
        default_params,
        default_state,
        error_text,
        family_summary,
        render_bead,
    )
    from .shared import scad
    from .theme import theme

import gradio as gr

PORT = 7863
TITLE = "Giant beads"


def _make_control(control):
    """One native control from the family spec."""
    if control.kind == "slider":
        return gr.Slider(
            minimum=control.minimum,
            maximum=control.maximum,
            value=control.default,
            step=control.step,
            label=control.label,
            info=control.info or None,
            interactive=True,
        )
    if control.kind == "text":
        return gr.Textbox(
            value=control.default,
            label=control.label,
            info=control.info or None,
            max_lines=1,
            interactive=True,
        )
    if control.kind == "dropdown":
        return gr.Dropdown(
            choices=list(control.choices),
            value=control.default,
            label=control.label,
            info=control.info or None,
            interactive=True,
        )
    if control.kind == "checkbox":
        return gr.Checkbox(
            value=bool(control.default),
            label=control.label,
            info=control.info or None,
            interactive=True,
        )
    raise ValueError(f"unsupported control kind: {control.kind}")


def _set_value(settings: dict, bead: str, key: str, value):
    """Immutable-ish state update for one per-bead shape control."""
    state = copy.deepcopy(settings)
    state["beads"][bead]["params"][key] = value
    return state


def _make_setter(bead: str, key: str):
    def setter(settings, value):
        return _set_value(settings, bead, key, value)
    return setter


def _make_override_setter(bead: str):
    def setter(settings, enabled):
        state = copy.deepcopy(settings)
        item = state["beads"][bead]
        item["override"] = bool(enabled)
        if enabled:
            item["width"] = state["width"]
            item["hole"] = state["hole"]
        return state
    return setter


def _make_override_width_setter(bead: str):
    def setter(settings, value):
        state = copy.deepcopy(settings)
        state["beads"][bead]["width"] = int(round(float(value)))
        return state
    return setter


def _make_override_hole_setter(bead: str):
    def setter(settings, value):
        state = copy.deepcopy(settings)
        state["beads"][bead]["hole"] = round(float(value), 1)
        return state
    return setter


def _make_reset_function(bead):
    def reset(settings):
        state = copy.deepcopy(settings)
        item = state["beads"][bead.slug]
        item["override"] = False
        item["width"] = state["width"]
        item["hole"] = state["hole"]
        item["params"] = default_params(bead)
        updates = [
            state,
            gr.update(value=False),
            gr.update(value=state["width"]),
            gr.update(value=state["hole"]),
            gr.update(visible=False),
        ]
        if bead.slug == "doughnut":
            updates.append(gr.update(visible=False))
        updates.extend(
            gr.update(value=item["params"][control.key])
            for control in bead.controls
        )
        return updates
    return reset


def build_demo() -> gr.Blocks:
    boot_state = default_state()
    try:
        boot_result = render_bead(boot_state, boot_state["selected"])
        boot_stl = str(boot_result.path)
        boot_meta = bead_meta(boot_state, boot_state["selected"], boot_result)
        boot_log = "No render errors."
    except Exception as exc:  # noqa: BLE001 - boot must not crash the app
        boot_result = None
        boot_stl = None
        boot_meta = (
            "**The first render did not complete.** "
            "Adjust a setting or pick another bead to try again."
        )
        boot_log = error_text(exc)

    with gr.Blocks(
        title=TITLE,
        fill_width=True,
    ) as demo:
        gr.Markdown(
            "# Giant beads\n"
            "One family, five beads. Set the shared size, shape one bead "
            "at a time, then take the set.",
            elem_classes=["workbench-header"],
        )

        settings = gr.State(copy.deepcopy(boot_state))

        with gr.Row(equal_height=False):
            # ---- family + bead list + family download -----------------
            with gr.Column(scale=3, min_width=280):
                with gr.Group(elem_classes=["bench-card"]):
                    gr.Markdown("## Family size", elem_classes=["section-title"])
                    gr.Markdown(
                        "Shared by every bead unless overridden.",
                        elem_classes=["family-summary"],
                    )
                    family_width = gr.Slider(
                        minimum=60,
                        maximum=240,
                        value=DEFAULT_WIDTH,
                        step=1,
                        label="Width",
                        info="Enclosing-circle diameter of the face, mm.",
                        interactive=True,
                    )
                    family_hole = gr.Slider(
                        minimum=10,
                        maximum=40,
                        value=DEFAULT_HOLE,
                        step=1,
                        label="String hole",
                        info="Throat diameter, mm.",
                        interactive=True,
                    )
                    summary = gr.Markdown(
                        family_summary(DEFAULT_WIDTH),
                        elem_classes=["family-summary"],
                    )

                with gr.Group(elem_classes=["bench-card"]):
                    gr.Markdown("## Beads", elem_classes=["section-title"])
                    picker = gr.Radio(
                        choices=[(bead.label, bead.slug) for bead in BEADS],
                        value=boot_state["selected"],
                        label="Beads",
                        container=False,
                        show_label=False,
                        elem_classes=["bead-picker"],
                    )

                with gr.Group(elem_classes=["bench-card"]):
                    gr.Markdown("## Take the set", elem_classes=["section-title"])
                    gr.Markdown(
                        "Renders all five at the current family settings.",
                        elem_classes=["family-summary"],
                    )
                    build_btn = gr.Button(
                        "Build family zip", variant="primary", size="lg")
                    family_download = gr.DownloadButton(
                        "Download family zip",
                        value=None,
                        variant="primary",
                        visible=False,
                    )
                    family_note = gr.Markdown(
                        "Five STLs plus a settings note.",
                        elem_classes=["family-summary"],
                    )

            # ---- orbit view + this-bead download ----------------------
            with gr.Column(scale=6, min_width=420):
                title = gr.Markdown(bead_title(BEAD_BY_SLUG[boot_state["selected"]]))
                with gr.Group(elem_classes=["viewer-shell"]):
                    model3d = gr.Model3D(
                        value=boot_stl,
                        display_mode="solid",
                        clear_color=(0.06, 0.09, 0.07, 1.0),
                        height=560,
                        show_label=False,
                        interactive=True,
                    )
                meta = gr.Markdown(boot_meta, elem_classes=["meta"])
                download_current = gr.DownloadButton(
                    "Download this bead",
                    value=boot_stl,
                    variant="primary",
                    size="lg",
                )
                gr.Markdown(
                    "Drag to orbit. Scroll to zoom. Downloads use the "
                    "browser's normal download folder.",
                    elem_classes=["family-summary"],
                )
                with gr.Accordion(
                    "Render log",
                    open=(boot_result is None),
                ) as log_accordion:
                    error_log = gr.Textbox(
                        value=boot_log,
                        show_label=False,
                        lines=8,
                        max_lines=16,
                        interactive=False,
                        elem_classes=["mono"],
                    )

            # ---- selected bead's shape controls -----------------------
            with gr.Column(scale=3, min_width=300):
                gr.Markdown("## Bead settings", elem_classes=["section-title"])
                gr.Markdown(
                    "Shape this bead. Size is inherited from the family "
                    "unless overridden.",
                    elem_classes=["family-summary"],
                )
                panels = {}
                controls_by_bead = {}
                override_widgets = {}
                mouth_groups = {}

                with gr.Group(elem_classes=["bench-card"]):
                    for bead in BEADS:
                        with gr.Column(
                            visible=(bead.slug == boot_state["selected"]),
                            elem_classes=["bead-panel"],
                        ) as panel:
                            controls = {}
                            local_mouth_group = None
                            for control in bead.controls:
                                if control.key == "r_mouth":
                                    with gr.Column(
                                        visible=False,
                                        elem_classes=["override-fields"],
                                    ) as local_mouth_group:
                                        controls[control.key] = _make_control(control)
                                else:
                                    controls[control.key] = _make_control(control)

                            override = gr.Checkbox(
                                value=False,
                                label="Override family size",
                                info="Use a different width or hole just for this bead.",
                                interactive=True,
                            )
                            with gr.Column(
                                visible=False,
                                elem_classes=["override-fields"],
                            ) as override_group:
                                override_width = gr.Slider(
                                    minimum=60,
                                    maximum=300,
                                    value=DEFAULT_WIDTH,
                                    step=1,
                                    label="Bead width",
                                    info="mm",
                                    interactive=True,
                                )
                                override_hole = gr.Slider(
                                    minimum=10,
                                    maximum=60,
                                    value=DEFAULT_HOLE,
                                    step=1,
                                    label="Bead hole",
                                    info="mm",
                                    interactive=True,
                                )
                            reset_btn = gr.Button(
                                "Reset this bead",
                                variant="secondary",
                                size="sm",
                            )

                        panels[bead.slug] = panel
                        controls_by_bead[bead.slug] = controls
                        override_widgets[bead.slug] = (
                            override,
                            override_width,
                            override_hole,
                            override_group,
                            reset_btn,
                        )
                        if local_mouth_group is not None:
                            mouth_groups[bead.slug] = local_mouth_group

        # ---- state setters ---------------------------------------------
        def set_family_width(settings, value):
            state = copy.deepcopy(settings)
            state["width"] = int(round(float(value)))
            return state

        def set_family_hole(settings, value):
            state = copy.deepcopy(settings)
            state["hole"] = round(float(value), 1)
            return state

        def pick_bead(settings, slug):
            state = copy.deepcopy(settings)
            state["selected"] = slug
            return (
                state,
                *[
                    gr.update(visible=(bead.slug == slug))
                    for bead in BEADS
                ],
            )

        family_width.change(
            set_family_width,
            inputs=[settings, family_width],
            outputs=[settings],
            trigger_mode="always_last",
        )
        family_hole.change(
            set_family_hole,
            inputs=[settings, family_hole],
            outputs=[settings],
            trigger_mode="always_last",
        )
        picker.change(
            pick_bead,
            inputs=[settings, picker],
            outputs=[settings, *panels.values()],
            trigger_mode="always_last",
        )

        def make_override_toggle(bead):
            def toggle(settings, enabled):
                state = _make_override_setter(bead.slug)(settings, enabled)
                item = state["beads"][bead.slug]
                return (
                    state,
                    gr.update(visible=bool(enabled)),
                    gr.update(value=item["width"]),
                    gr.update(value=item["hole"]),
                )
            return toggle

        def make_mouth_toggle(bead):
            def toggle(settings, enabled):
                state = copy.deepcopy(settings)
                state["beads"][bead.slug]["params"]["match_mouth"] = bool(enabled)
                auto = _doughnut_auto_mouth(state, bead.slug)
                return (
                    state,
                    gr.update(visible=not bool(enabled)),
                    gr.update(value=auto),
                )
            return toggle

        for bead in BEADS:
            controls = controls_by_bead[bead.slug]
            override, override_width, override_hole, override_group, reset_btn = (
                override_widgets[bead.slug]
            )
            for control in bead.controls:
                if control.key == "match_mouth":
                    # The doughnut's match toggle has its own handler so it
                    # can also reveal the independent mouth slider.
                    continue
                component = controls[control.key]
                setter = _make_setter(bead.slug, control.key)
                if control.kind == "slider":
                    component.change(
                        setter,
                        inputs=[settings, component],
                        outputs=[settings],
                        trigger_mode="always_last",
                    )
                elif control.kind == "text":
                    component.submit(
                        setter,
                        inputs=[settings, component],
                        outputs=[settings],
                        trigger_mode="always_last",
                    )
                    component.blur(
                        setter,
                        inputs=[settings, component],
                        outputs=[settings],
                        trigger_mode="always_last",
                    )
                else:
                    component.change(
                        setter,
                        inputs=[settings, component],
                        outputs=[settings],
                        trigger_mode="always_last",
                    )

            override.change(
                make_override_toggle(bead),
                inputs=[settings, override],
                outputs=[
                    settings,
                    override_group,
                    override_width,
                    override_hole,
                ],
                trigger_mode="always_last",
            )
            override_width.change(
                _make_override_width_setter(bead.slug),
                inputs=[settings, override_width],
                outputs=[settings],
                trigger_mode="always_last",
            )
            override_hole.change(
                _make_override_hole_setter(bead.slug),
                inputs=[settings, override_hole],
                outputs=[settings],
                trigger_mode="always_last",
            )

            if bead.slug in mouth_groups:
                mouth_group = mouth_groups[bead.slug]
                controls["match_mouth"].change(
                    make_mouth_toggle(bead),
                    inputs=[settings, controls["match_mouth"]],
                    outputs=[settings, mouth_group, controls["r_mouth"]],
                    trigger_mode="always_last",
                )

            reset_outputs = [
                settings,
                override,
                override_width,
                override_hole,
                override_group,
            ]
            if bead.slug in mouth_groups:
                reset_outputs.append(mouth_groups[bead.slug])
            reset_outputs.extend(controls.values())
            reset_btn.click(
                _make_reset_function(bead),
                inputs=[settings],
                outputs=reset_outputs,
                trigger_mode="always_last",
            )

        # ---- render on any state change -------------------------------
        def render_state(settings):
            slug = settings["selected"]
            bead = BEAD_BY_SLUG[slug]
            title_md = bead_title(bead)
            summary_md = family_summary(float(settings["width"]))
            # A changed setting makes a previously built family zip
            # stale, so hide it rather than offering the old bundle.
            stale_zip = gr.update(
                value=None, visible=False, label="Download family zip")
            try:
                result = render_bead(settings, slug)
            except Exception as exc:  # noqa: BLE001 - keep the UI alive
                return (
                    gr.update(),
                    gr.update(value=None, interactive=False),
                    title_md,
                    "**This bead did not render.** The view shows the "
                    "previous render. See the render log.",
                    summary_md,
                    error_text(exc),
                    gr.update(open=True),
                    stale_zip,
                    "Five STLs plus a settings note.",
                )
            return (
                str(result.path),
                gr.update(value=str(result.path), interactive=True),
                title_md,
                bead_meta(settings, slug, result),
                summary_md,
                "No render errors.",
                gr.update(open=False),
                stale_zip,
                "Five STLs plus a settings note.",
            )

        settings.change(
            render_state,
            inputs=[settings],
            outputs=[
                model3d,
                download_current,
                title,
                meta,
                summary,
                error_log,
                log_accordion,
                family_download,
                family_note,
            ],
            trigger_mode="always_last",
            show_progress="full",
        )

        # ---- family zip ------------------------------------------------
        def make_zip(settings, progress=gr.Progress()):
            try:
                zip_path, results = build_family_zip(settings, progress)
            except Exception as exc:  # noqa: BLE001 - keep the UI alive
                return (
                    gr.update(),
                    "**The family zip did not build.** See the render log.",
                    error_text(exc),
                    gr.update(open=True),
                )
            zip_size = zip_path.stat().st_size
            note = (
                "**Family zip ready.** "
                f"{len(results)} STLs · {scad.human_bytes(zip_size)}."
            )
            return (
                gr.update(
                    value=str(zip_path),
                    visible=True,
                    label=f"Download family zip ({scad.human_bytes(zip_size)})",
                ),
                note,
                "No render errors.",
                gr.update(open=False),
            )

        build_btn.click(
            make_zip,
            inputs=[settings],
            outputs=[family_download, family_note, error_log, log_accordion],
            show_progress="full",
        )

    return demo


def _doughnut_auto_mouth(state: dict, slug: str) -> float:
    """The doughnut's automatic hole-mouth radius at the current settings."""
    bead = BEAD_BY_SLUG[slug]
    width = float(
        state["beads"][slug]["width"]
        if state["beads"][slug]["override"] else state["width"]
    )
    hole = float(
        state["beads"][slug]["hole"]
        if state["beads"][slug]["override"] else state["hole"]
    )
    curvature = float(
        state["beads"][slug]["params"].get("curvature", 0.5)
    )
    height = width / 4
    r_out = width / 4
    r_throat = hole / 2
    outer_fillet = (height / 2) * (0.25 + 0.75 * curvature)
    r_mouth_max = max(0.0, min(height / 2, r_out - r_throat - outer_fillet))
    return min(outer_fillet, r_mouth_max)


if __name__ == "__main__":
    demo = build_demo()
    demo.queue()
    demo.launch(
        server_name="127.0.0.1",
        server_port=PORT,
        allowed_paths=[str(scad.SCRATCH_DIR), str(scad.TEMPLATES_DIR)],
        theme=theme(),
    )
