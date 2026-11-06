#!/usr/bin/env python3
"""STL Forge tab: template -> live-rendered binary STL (no Render button).

Sub-app contract (house rule): this module exports create_tab() that is
used INSIDE a gr.Blocks context (the master calls it under gr.Tab;
standalone mode wraps it in its own Blocks under __main__). NATIVE
Gradio components only - no custom HTML/CSS/JS.

UX revision (genapp polish round 2): the tab is a 1/3 : 2/3 gr.Row
split - LEFT column: template dropdown, the parsed parameter controls
and the Reset button; RIGHT column: the interactive gr.Model3D
binary-STL orbit view, a full-width DownloadButton (always bound to
the latest rendered `{stem}_app.stl` in app/.render-scratch/) and the
session log under it (errors must stay visible).

UX revision (genapp polish round 3): the one-shot status textbox is now
an APPENDING session log - each render event appends ONE entry, newest
at the bottom, bounded at the last 200 entries. Entries carry an ISO
timestamp, the template and params applied, and the full result
(`... OK N facets M bytes`) or the full OpenSCAD stderr on failure, so
debugging happens in the UI, not in a shell. The running log lives in
a module-level list; every handler returns the joined text. Monospace
tagging uses the native elem_classes hook only (no custom CSS: gradio
6.30 ships no native monospace class).

Live render contract: there is no Render button. Every parameter
control's .change event and the dropdown's own .select event drive the
render handler (always_last trigger so stale intermediate renders are
dropped, never a backlog). The handler chains its STL path to BOTH the
gr.Model3D orbit view and the DownloadButton value, so a download
always offers the CURRENT render. Each render request is logged to
app/.render-scratch/render-log.txt (draggable-slider proof: grep the
log for the value). Handlers are idempotent and write ONLY into
app/.render-scratch/. Selecting a template rebuilds the controls from
its parsed parameter block (@gr.render) and renders that template's
file defaults immediately - the defaults are also rendered once at
build time so the view is never empty on first load.

INTERACTIVITY (gradio 6.30 defect, fixed): controls created inside a
@gr.render function are hydrated by the frontend WITHOUT the
interactive=true default that build-time components get, so every
rendered slider docks disabled and cannot be dragged. The fix: build
the controls with explicit interactive=True.

Handler-level entry (usable without the UI, e.g. for tests):
run_bead_render(stem, overrides) -> dict with stl path, facet count
and byte size. Every artefact lands in app/.render-scratch/ - never in
a project output folder.

The -D override contract: ALL control values are sent (defaults must
round-trip cleanly); only literal-valued template params become
controls, because derived params (height = width / 2 ...) must recompute
- bead_star asserts height == width / 2, and stale overrides would fail
that assert every time.
"""
from __future__ import annotations

import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):  # run directly: python forge_tab/app.py
    _APP_DIR = Path(__file__).resolve().parents[1]
    if str(_APP_DIR) not in sys.path:
        sys.path.insert(0, str(_APP_DIR))

try:  # prefer the package import so app.shared stays a single module
    from ..shared import scad
except ImportError:
    from shared import scad

import gradio as gr

# Port for standalone runs (the master app owns 7863).
STANDALONE_PORT = 7864


def run_bead_render(stem: str, overrides: dict) -> dict:
    """Render one template at the given -D overrides (handler-level).

    Returns {"stl", "facets", "bytes", "probe"}. Raises
    scad.RenderError with the OpenSCAD console tail on failure. Writes
    ONLY into the scratch dir (scad.render_stl names the file
    `<stem>_app.stl`, which is also the download filename).
    """
    stl_path = scad.render_stl(stem, overrides)
    facets, size = scad.probe_binary_stl(stl_path)   # offsets 80, 4-byte LE
    return {"stl": str(stl_path), "facets": facets, "bytes": size,
            "probe": scad.probe_line(stl_path)}


_RENDER_LOG = scad.SCRATCH_DIR / "render-log.txt"

# --- session log stream (polish round 3) -------------------------------------
# The running log lives in this module-level list (one server process),
# bounded at the last LOG_MAX_ENTRIES entries; every handler appends ONE
# entry per render event (newest at the BOTTOM, oldest at top - natural
# log reading order) and returns the joined text for the log textbox.

LOG_MAX_ENTRIES = 200

_SESSION_LOG: list[str] = []
_EXIT_RE = re.compile(r"openscad exited (\S+) \([^)]*\):\n?", re.S)


def _iso_now() -> str:
    """ISO timestamp prefix for a log entry."""
    return datetime.now().isoformat(timespec="seconds")


def _fail_text(e: Exception) -> str:
    """Failure body for a log entry.

    OpenSCAD RenderErrors become `openscad exit <code>: <full stderr>`
    (the whole console tail, multiline, so debugging happens in the UI,
    not in a shell); any other exception keeps the traceback tail the old
    status textbox used to show.
    """
    if isinstance(e, scad.RenderError):
        m = _EXIT_RE.match(str(e))
        if m:
            return f"openscad exit {m.group(1)}: {str(e)[m.end():].strip()}"
        return str(e)
    return f"{e}\n{traceback.format_exc()[-800:]}"


def _pairs(stem: str, values) -> str:
    """`name=value` pairs for the log entry's params section."""
    try:
        names = [p.name for p in scad.parse_template_params(stem)]
    except Exception:  # noqa: BLE001 - log failures are non-fatal
        names = []
    return ", ".join(f"{n}={v}" for n, v in zip(names, values))


def _push_log(entry: str) -> str:
    """Append ONE entry to the running session log, truncate to the last
    LOG_MAX_ENTRIES entries to bound memory, return the joined text."""
    _SESSION_LOG.append(entry)
    if len(_SESSION_LOG) > LOG_MAX_ENTRIES:
        del _SESSION_LOG[:-LOG_MAX_ENTRIES]
    return "\n".join(_SESSION_LOG)


def _seed_boot_log() -> None:
    """Seed the log with the boot line (once per process) so the stream
    is never empty on first load: `app booted, gradio x.y.z, N templates`."""
    if not _SESSION_LOG:
        n = len(scad.list_templates())
        _push_log(f"{_iso_now()} app booted, gradio {gr.__version__}, "
                  f"{n} templates")


def _log_render(stem: str, values) -> None:
    """Append one probe line to the scratch render log.

    Interactivity proof instrument: dragging a slider must land here
    with the NEW value (grep app/.render-scratch/render-log.txt).
    Logging itself must never break a render.
    """
    try:
        scad.SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        with open(_RENDER_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"render request: {stem} ({_pairs(stem, values)})\n")
    except Exception:  # noqa: BLE001 - log failures are non-fatal
        pass


def _ok_entry(stem: str, pairs: str, result: dict) -> str:
    """One OK log entry: ISO timestamp, template/params, full result."""
    return (f"{_iso_now()} {stem}({pairs}) "
            f"... OK {result['facets']} facets {result['bytes']} bytes")


def _overrides(stem: str, values) -> dict:
    """Zip control values onto the template's parsed parameter names."""
    names = [p.name for p in scad.parse_template_params(stem)]
    return dict(zip(names, values))


def on_render(stem: str, *values):
    """Gradio change handler: merge control values onto parsed names.

    Returns `(model3d, download, log)`: the STL path is chained to
    BOTH the orbit view and the DownloadButton value (the download
    always offers the CURRENT rendered `<stem>_app.stl`) and the log
    textbox receives the full session log with ONE new entry. OpenSCAD
    failures append a FAIL entry carrying the full stderr (never a
    raised crash); gr.update() keeps the previous STL on screen.
    """
    if not stem:  # unknown template: log it, keep the view as-is
        return gr.update(), gr.update(), _push_log(
            f"{_iso_now()} (no template) ... FAIL no template selected")
    try:
        params = scad.parse_template_params(stem)
        pairs = ", ".join(f"{p.name}={v}" for p, v in zip(params, values))
        if len(values) != len(params):  # stale pre-rebuild control set
            return gr.update(), gr.update(), _push_log(
                f"{_iso_now()} {stem}({pairs}) ... FAIL stale controls "
                f"({len(values)} values vs {len(params)} parameters) - "
                f"re-select the template")
        _log_render(stem, values)
        result = run_bead_render(stem, dict(zip([p.name for p in params],
                                                values)))
        return result["stl"], result["stl"], _push_log(
            _ok_entry(stem, pairs, result))
    except Exception as e:  # noqa: BLE001 - last-ditch, still no crash
        return gr.update(), gr.update(), _push_log(
            f"{_iso_now()} {stem}({_pairs(stem, values)}) "
            f"... FAIL {_fail_text(e)}")


def _render_defaults(stem: str | None):
    """`(result dict, None)` for a defaults render, else `(None, exc)`.

    The error is returned as the raw exception so every caller can shape
    its own log entry (full stderr body via _fail_text).
    """
    if not stem:
        return None, None
    try:
        result = run_bead_render(stem, _overrides(stem, []))
        return result, None
    except Exception as e:  # noqa: BLE001
        return None, e


def on_select(stem: str | None):
    """Gradio select handler (the dropdown's own event): render the new
    template's file defaults immediately - the view is never empty, and
    the download button is pointed at the fresh render. One log entry
    per call (OK with facet/byte counts, or FAIL with full stderr)."""
    result, error = _render_defaults(stem)
    if result:
        return (result["stl"], result["stl"], _push_log(
            _ok_entry(stem, "file defaults", result)))
    return gr.update(), gr.update(), _push_log(
        f"{_iso_now()} {stem or '(no template)'}(file defaults) ... FAIL "
        f"{_fail_text(error) if error else 'no template selected'}")


def on_reset(stem: str | None):
    """Gradio click handler for Reset: put the template's file defaults
    back into the SAME controls (no rebuild) and re-render at defaults,
    chaining the fresh render to both orbit view and download button.

    The .scad file is the single source of the defaults (whatever the
    parser returned - re-parsed here, same file). No exception escapes;
    a failed re-render appends a FAIL log entry (full stderr) with the
    previous STL kept on screen.
    """
    defaults: list = []
    try:
        params = scad.parse_template_params(stem) if stem else []
        defaults = [p.value for p in params]
    except scad.RenderError:
        pass  # the defaults render below re-raises the same story
    result, error = _render_defaults(stem)
    if result:
        return [*defaults, result["stl"], result["stl"], _push_log(
            _ok_entry(stem, "file defaults (reset)", result))]
    fail = (_fail_text(error) if error else ("no template selected"
                                             if not stem else "render failed"))
    return [*defaults, gr.update(), gr.update(), _push_log(
        f"{_iso_now()} {stem or '(no template)'}"
        f"(file defaults (reset)) ... FAIL {fail}")]


def _make_control(param: scad.ScadParam):
    """One native control per parsed parameter, info= from its own comment.

    interactive=True is REQUIRED: gradio 6.30 hydrates @gr.render-injected
    components without the interactive default, so an omitted
    interactive docks every one of these controls disabled and the
    sliders cannot be dragged (round 2 bug fix, see module docstring).
    """
    if isinstance(param.value, bool):
        return gr.Checkbox(value=param.value, label=param.name,
                           info=param.info or None, interactive=True)
    rng = scad.slider_range(param)
    if isinstance(param.value, (int, float)) and rng is not None:
        lo, hi = rng
        return gr.Slider(minimum=lo, maximum=hi, value=param.value,
                         step=1.0 if isinstance(param.value, int) else 0.1,
                         label=param.name, info=param.info or None,
                         interactive=True)
    if isinstance(param.value, (int, float)):
        return gr.Number(value=param.value, label=param.name,
                         info=param.info or None, interactive=True)
    return gr.Textbox(value=param.value, label=param.name,
                      info=param.info or None, interactive=True)


def create_tab() -> dict:
    """Build this tab inside the ACTIVE gr.Blocks context.

    1/3 : 2/3 gr.Row columns (native components, no custom CSS): the
    LEFT column holds the dropdown, the @gr.render'ed per-template
    controls and the Reset button; the RIGHT column holds the
    gr.Model3D orbit view, then the full-width DownloadButton bound to
    the latest render's `<stem>_app.stl`, then the appending session
    log (gr.Textbox, autoscroll, interactive=False).
    Control .change and dropdown .select drive the render handler;
    reset/select wiring is re-bound to the fresh controls on every
    rebuild. Stable components referenced inside the render body are
    created after it - the documented @gr.render late-binding pattern
    (skill examples.md "Render Merge").
    """
    _seed_boot_log()
    templates = scad.list_templates()
    default_stem = ("bead_star" if "bead_star" in templates
                    else (templates[0] if templates else None))

    # Boot-time defaults render so the orbit view is never empty on the
    # first page load (select/change events cover later interactions).
    # This is a build-time render, not a UI event, so it does NOT append
    # a log entry on success; on failure a FAIL entry carries the full
    # stderr so the user still sees what broke before touching anything.
    boot_result, boot_error = _render_defaults(default_stem)
    boot_stl = boot_result["stl"] if boot_result else None
    if boot_result is None and boot_error is not None and default_stem:
        _push_log(f"{_iso_now()} {default_stem}(file defaults) "
                  f"... FAIL {_fail_text(boot_error)}")

    with gr.Row():
        with gr.Column(scale=1, min_width=320):
            template_dd = gr.Dropdown(
                choices=templates, value=default_stem, label="Template",
                info="projects/giant-beads/templates/*.scad - the controls "
                     "below are parsed from this file's top parameter "
                     "block; every change renders immediately")
            @gr.render(inputs=template_dd)
            def _build_controls(stem):
                params = scad.parse_template_params(stem) if stem else []
                controls = [_make_control(p) for p in params]
                for control in controls:  # live render: no Render button
                    control.change(on_render,
                                   inputs=[template_dd, *controls],
                                   outputs=[model3d, download_btn, log_stream],
                                   trigger_mode="always_last")
                # Reset re-binds to the fresh controls on every rebuild;
                # it only ever updates values, never rebuilds widgets.
                reset_btn.click(on_reset, inputs=template_dd,
                                outputs=[*controls, model3d,
                                         download_btn, log_stream])
                if not controls:
                    gr.Markdown(f"*No literal-valued top parameters parsed "
                                f"from `{stem or '(none)'}.scad` - this "
                                f"template exposes nothing to dial.*")
            reset_btn = gr.Button("Reset", variant="secondary")
        with gr.Column(scale=2, min_width=320):
            # clear_color is the only mesh-adjacent knob gradio 6.30
            # exposes natively (a 4-float RGBA background tuple); the
            # mesh body colour itself is NOT reachable, so the violet
            # palette comes from the dark-violet viewer background.
            model3d = gr.Model3D(value=boot_stl, clear_color=(0.10, 0.02, 0.16, 1.0),
                                 label="Binary STL (interactive orbit view)")
            # DownloadButton always holds the latest rendered STL path;
            # with no render yet it stays inert (value None, never a
            # crash). scad.render_stl names the file <stem>_app.stl, so
            # the offered download filename is the contract's own.
            download_btn = gr.DownloadButton(label="Download STL",
                                             value=boot_stl,
                                             variant="primary")
            # Appending session log (round 3): one entry per render
            # event, newest at the BOTTOM (autoscroll keeps the view on
            # the latest line), interactive=False (read-only log).
            # Monospace: tagged via the native elem_classes hook - gradio
            # 6.30 ships no native monospace class, so no custom CSS.
            log_stream = gr.Textbox(
                label="Session log (newest at bottom)",
                value="\n".join(_SESSION_LOG),
                lines=14, autoscroll=True, interactive=False,
                elem_classes=["stl-session-log"])

    template_dd.select(on_select, inputs=template_dd,
                       outputs=[model3d, download_btn, log_stream])

    return {"template": template_dd, "reset": reset_btn,
            "model3d": model3d, "download": download_btn,
            "log": log_stream}


if __name__ == "__main__":  # standalone run of this tab only
    with gr.Blocks(title="STL Forge") as demo:
        gr.Markdown("## \U0001F6E0 STL-forge\n"
                    "Pick a giant-beads template, dial its parameters - "
                    "every change renders the binary STL live into the "
                    "scratch dir. Reset puts the file defaults back; the "
                    "Download STL button offers the current render.")
        create_tab()
    demo.queue().launch(server_name="127.0.0.1",
                        server_port=STANDALONE_PORT,
                        allowed_paths=[str(scad.SCRATCH_DIR),
                                       str(scad.TEMPLATES_DIR)])
