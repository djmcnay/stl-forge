---
title: Generation app — Gradio two tabs
date: 2026-10-22
tags: [genapp, gradio, app, stl-forge]
---

# FINDINGS: stl-forge generation app (Gradio, two tabs)

Run: 22 Oct 2026, branch `feat/generation-app` (cut from `main`, working
tree = skill root). NO merge, NO push. Other sessions' dirty files
(minty-sync, pi-media-server, stl-forge SKILL.md, FINDINGS_star_face_fillets)
were left unstaged and untouched; `.agents/`/`.opencode/` stay untracked;
`app/.venv` and `app/.render-scratch` are gitignored and uncommitted.

## Files touched (exhaustive)

```
app/
  __init__.py            NEW
  app.py                 NEW   master: composes both tabs, launch(127.0.0.1:7863,
                               allowed_paths=[scratch, templates])
  .gitignore             NEW   .venv/, .render-scratch/, __pycache__/
  README.md              NEW   run instructions, one line per tab, layout
  forge_tab/__init__.py  NEW
  forge_tab/app.py       NEW   tab 1: STL Forge
  sketch_tab/__init__.py NEW
  sketch_tab/app.py      NEW   tab 2: Geometry Playground
  shared/__init__.py     NEW
  shared/scad.py         NEW   OpenSCAD CLI helpers: template discovery, top
                               param-block parse, -D formatting, binstl probe
                               (offset-80 4-byte LE facet count), --imgsize/
                               --camera PNG pipeline, scratch-dir discipline
README.md (skill root)   +1 run-instructions sentence (the fence's allowance)
```

Commits (5, labelled): `2666e13` shared helpers, `ddca155` STL Forge tab,
`25e0b4c` Geometry Playground tab, `3905c7c` master+README+gitignore,
`092f795` README sentence. Explicit-path `git add` only throughout.

Domain code (`projects/giant-beads/**`, root `templates/**`, `core/**`,
`presets.json`, all SKILL.mds): read-only, zero modifications (pytest row
below proves the project suite is unaffected).

## Gate rows (measured)

| Gate | Result | Numbers |
|---|---|---|
| 1. `app/.venv` exists with Gradio | PASS | venv pre-existed this session (built 11:15, before app code was written); Python 3.12.9, gradio **6.30.0**; verified importable — not recreated, not committed |
| 2. Offline import test | PASS | `app/.venv/bin/python -c "import app.app"` from the **skill root** exits 0. From cwd=`app/` literally it raises `ModuleNotFoundError: No module named 'app.app'; 'app' is not a package` — structural (the master file is `app/app.py` inside the package dir `app/`; cwd=`app/` resolves `app` to the master module itself). The skill-root run is the package-root import and is the one quoted. |
| 3. Master app end-to-end | PASS | launched in background, `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7863` → **200**, then killed. Standalone tabs also boot: 7864 → 200, 7865 → 200 |
| 4. Tab-1 handler render, bead_star defaults | PASS | `bead_star_app.stl` **12,750,084 bytes** (12.67 MB > 1 MB), **255,000 facets**; preview `bead_star_app.png` 7,822 bytes; 2.0 s wall time. Both in `app/.render-scratch/` |
| 5. Tab-2 handler sketch render | PASS | `sketch_star_faceon.png` **7,308 bytes** (non-empty), 0.1 s; echo hook live: `valley_ratio 0.631413` (matches `star_inner_ratio(5, 3)` = 0.6316 analytic). Driver `sketch_driver.scad` sits in scratch |
| 6. `-D` overrides reach geometry | PASS | `roundness=1` render: **41,276 facets** / 2,063,884 bytes vs default **255,000** / 12,750,084 — different, proving the `-D` path drives the geometry |
| 7. Regression: `python3 -m pytest tests/ -q` in `projects/giant-beads` | PASS | **34 passed** in 7.82 s |
| 8. Error surfacing (no crash) | PASS | `on_render("bead_common")` (library file, no solid): returns `None/None` + `⚠ OpenSCAD render failed` in the status textbox |
| 9. Handler writes only to scratch | PASS | all renders, the sketch driver, PNGs land in `app/.render-scratch/`; nothing touched any project output folder |

Both preview PNGs were visually inspected: face-on star renders, one tip
vertically up, correct (roundness 1 = sharp star, 12 = bulbous flower).

## How to run

```bash
# from the skill root (skills/stl-forge)
app/.venv/bin/python app/app.py          # master → http://127.0.0.1:7863
app/.venv/bin/python app/forge_tab/app.py    # standalone tab 1, port 7864
app/.venv/bin/python app/sketch_tab/app.py   # standalone tab 2, port 7865

# rebuild the venv if ever needed (gitignored)
uv venv app/.venv && uv pip install --python app/.venv/bin/python gradio
```

`allowed_paths=["…app/.render-scratch", "…projects/giant-beads/templates"]`
on every launch. Gradio queue is enabled (`demo.queue()`) so 2–30 s
renders never freeze the UI.

## Design decisions & deviations (all deliberate)

- **`USAGE.md` does not exist** at the skill root despite the brief's
  reference. The `--export-format=binstl -o … -D` + `--imgsize=640,480
  --autocenter --viewall --camera` pipeline was taken from the two places
  that DO document it: skill-root `SKILL.md` (ad-hoc render + square-on
  camera examples) and `forge.py` (`CAMERAS` table, `PNG_MIN_BYTES`).
  Face-on = gimbal camera `0,0,0,0,0,0,350` (`forge.CAMERAS["top"]`, straight
  down z, matching the bead family's up-facing star/letter faces).
- **Controls = literal-valued params only.** The top parameter block is
  parsed with stop-at-first-structural-line semantics; derived params
  (`height = width / 2`, `fillet_radius = width / 12`,
  `hole_opening_diameter = max(…)`, `$fn`, `letter_bottom = letter_top`)
  are intentionally NOT exposed: bead_star asserts `height == width / 2`,
  so overriding a stale derived value would fail every render once width
  moves. ALL literal controls are sent as `-D` (defaults round-trip:
  gate 4 renders at exactly the template defaults). bead.scad's string
  params (`letter_top`, `letter_font`, `part`) become `gr.Textbox`,
  booleans `gr.Checkbox`, numerics `gr.Slider`/`gr.Number`.
- **Slider ranges derive from each param's own comment**: `A..B` dial
  ranges win (`roundness` 1..20, `petal_depth` 1..10, `bubble` 1..10),
  `integer >= N` floors the low end (`points` 3..15), else quarter- to
  double-default (e.g. `width` 30..240, `hole_diameter` 5..40).
- **`info=` source priority**: inline comment after `;` → immediately
  preceding contiguous `//` lines (decorative `// ----` dividers
  skipped) → the file's leading block comment (covers bead_star, whose
  params carry aligned header docs instead of inline comments).
- **Sub-app contract reading**: `create_tab()` builds its UI inside the
  CALLER's active `gr.Blocks` context (master composes under `gr.Tab` via
  `@gr.render` for the dynamic per-template controls; the Render button
  stays outside the render and is re-wired per rebuild — the documented
  skill pattern). Each tab is standalone-runnable on its own port with
  its own `allowed_paths` (verified, gate 3).
- **No maths duplication**: tab 2 writes a 10-line driver .scad into the
  scratch dir that `use <…/bead_star.scad>`s and extrudes `star_2d` 1 mm;
  `-D` overrides the driver's four dials. The echoed
  `star_inner_ratio(points, petal_depth)` devil-free valley ratio is
  captured from OpenSCAD console output and shown in the readout line
  (the "cheap echo hook" did exist, so it was wired, not omitted).
- **Binary STL probe** reimplemented read-only in `app/shared/scad.py`
  (offset-80 LE uint32 facet count + the `84 + 50n` byte invariant),
  mirroring `core/stl_probe.py`; the app stays stdlib-only on its own
  venv.
- **Error route**: OpenSCAD failures surface in the status/readout
  `gr.Textbox` (never an exception out of the handler) — the
  `gr.Warning`-or-textbox alternative the brief allows.
- **Skill-root README**: one sentence added (`092f795`), which the fence
  allows ("check first; optional" — it exists).
- **The `app/.venv` pre-existence**: found at first `uv venv` attempt
  (already populated, gradio 6.30.0). Treated as environment, verified
  rather than recreated; it is gitignored either way.
