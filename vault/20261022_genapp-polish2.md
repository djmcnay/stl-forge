---
title: Generation app polish round 2 — layout, download, interactivity fix
date: 2026-10-22
tags: [genapp, gradio, polish, app]
---

# FINDINGS: generation app polish round 2 (layout, download, interactivity fix)

Branch `feat/genapp-polish2` (cut from main checkout). Three labelled
commits, never merged, never pushed:

- `c76247c` forge: fix locked rendered-slider interactivity (gradio 6.30)
- `8be3f02` master: STL Forge tab label to `🛠 STL-forge`, header drops
  "-generation app"
- `d9338f1` app README: one-sentence layout truth

## Files touched

- `app/forge_tab/app.py` (interactivity fix, 1/3 : 2/3 split,
  DownloadButton, status move, render-log instrument)
- `app/app.py` (header markdown + tab label only)
- `app/README.md` (one sentence)
- `app/.venv` rebuilt (uv, per app/README build commands): its
  `libpython3.12.dylib` was broken, `python -c "import gradio"` failed
  with a dylib error before the round could be measured at all.

`app/sketch_tab/app.py`; `app/shared/scad.py` untouched. Other sessions'
dirty files (SKILL.md, FINDINGS_star_face_fillets.md, minty-sync,
pi-media-server) stayed unstaged/untouched; the brief is intact.

## Gate rows (measured)

| Gate | Result | Numbers |
|---|---|---|
| Dash gate over every touched file | PASS for authored text | `0 app/app.py`, `0 app/forge_tab/app.py`, `0 app/sketch_tab/app.py`, `3 app/README.md` (all 3 pre-existing, untouched lines 6/17/23 - see deviations), `13 README.md` (root, not touched). macOS grep has no `-P`; the identical Python scan printed U+2014/U+2013 counts per file |
| Boot: master app on 7863 | PASS | `curl -o /dev/null -w "%{http_code}"` = 200; log shows `Running on local URL: http://127.0.0.1:7863` |
| Interactivity (UI level) | PASS | Headless Chromium (playwright, outside the repo): all 5 forged-rendered sliders now report `enabled=True` (were `False` before the fix); dragging roundness moved the value 12 -> 19 and the status readout re-rendered (255,000 facets / 12,750,084 bytes -> 252,304 facets / 12,615,284 bytes) |
| Interactivity (handler level, instrument) | PASS | `render-log.txt` in `app/.render-scratch/`: browser drag landed as `render request: bead_star (width=120, roundness=19, points=5, petal_depth=3, hole_diameter=20)`; a direct roundness=1 invocation logged `render request: bead_star (width=120, roundness=1, ...)` |
| Two renders differ byte-wise | PASS | `on_render` direct: roundness 12 -> 12,750,084 bytes (255,000 facets); roundness 1 -> 2,063,884 bytes (41,276 facets); `DIFFER byte-wise: True` |
| Download chain | PASS | Handler/client results: download value path == orbit value path == render handler STL path (`app/.render-scratch/bead_star_app.stl`); `gradio_client` `on_select` returns orbit and download byte-identically (same served path), `GET /gradio_api/file=` = 200, 12,750,084 bytes non-zero, binary STL invariant holds (84 + 50*n); served copy md5-identical to the scratch render at equal roundness |
| Status placement | PASS | Code-level: in `create_tab()` the right `gr.Column(scale=2)` builds `model3d`, then `download_btn`, then `status`; `/config` layout shows column scale=2 children `model3d -> downloadbutton -> textbox "Probe / status"`; left column children are dropdown, render placeholder, Reset only. The left status textbox is gone |
| Regression suite | PASS | `python3 -m pytest projects/giant-beads/tests/ -q` = `34 passed` (also 34 passed before the branch edits) |
| Sketch tab unchanged | PASS | `git diff` empty for `app/sketch_tab/app.py`; client: `on_sketch` readout `valley ratio 0.6314`, `on_reset` returns `(120, 5, 12, 3)` and re-echoes the same valley ratio; live PNG renders 7,308 bytes |
| Title | PASS | Tab label exactly `🛠 STL-forge` (`/config` `tabitem` label); master header markdown is `# stl-forge` with no "-generation app" wording; Geometry Playground label untouched |

## Root cause of the locked-slider defect (one paragraph)

Not the suspected wiring faults: no `interactive=False` was dotted
anywhere and no handler wrote back into its own inputs; the SSE queue
showed the on-load render dependency completing successfully with the
correct components AND their change dependencies injected
(`api_name="on_render") and the endpoints were callably wired. The
actual cause is a gradio 6.30 frontend hydration defect: components
created inside a `@gr.render` function reach the browser through the
queue's render_config update, and the built-in
`interactive = value ?? true` defaulting that build-time components get
is never applied on that injection path, so `shared.interactive` is
undefined-falsy for every injected widget and the Slider element
(`let Y = t(() => !R.shared.interactive)`) renders with
`disabled=true`. Since the STL Forge tab derives its whole control set
from `@gr.render`, every parameter slider/control was permanently
locked while the identical build-time sketch sliders stayed usable. The
minimal cause-level fix is to construct each rendered control with
explicit `interactive=True`, which rides along on every re-render
(probes: control in render without the flag = disabled with or without
a listener; with `interactive=True` = enabled and draggable).

## Deviations

1. `app/README.md` keeps 3 em dashes on lines 6, 17 and 23. They are
   pre-existing text I did not author and the brief's hard rule says to
   leave such occurrences alone and list them, so the touched-file dash
   count is 3 instead of 0 while every string I wrote is dash-free
   (hyphens only). The root `README.md` was not touched at all; its 13
   em dashes are pre-existing.
2. `app/.venv` had to be rebuilt (`libpython3.12.dylib` missing) before
   anything could be measured; rebuilt strictly per the app README
   (gradio 6.30.0, gradio_client 2.7.2, Python 3.12.9).
3. The radio-free DownloadButton filename: `scad.render_stl` already
   writes `app/.render-scratch/{stem}_app.stl`, so binding the raw
   render path satisfies the `<stem>_app.stl` contract with no copy
   step; clicking then serves gradio's own on-demand copy
   (byte-identical, same basename).
4. An extra chromium-based interactivity probe environment was kept
   outside the repo (`$TMPDIR/opencode`), never inside `app/`.
