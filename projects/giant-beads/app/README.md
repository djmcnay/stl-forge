# Giant beads app

A single-page, native-Gradio workbench for the five-bead family:

- **Letter bead** (`bead.scad`)
- **Heart bead** (`bead_heart.scad`)
- **Star bead** (`bead_star.scad`)
- **Doughnut spacer** (`bead_spacer_small.scad`)
- **Shallot spacer** (`bead_spacer_wide.scad`)

The page is arranged as a three-pane bench: family size and bead choice
on the left, the orbit view in the middle, and the selected bead's shape
controls plus download actions on the right. The goal is to size the
whole set, shape one bead at a time, then download the STLs. It is not a
CAD editor.

## Run

From the repo root:

```bash
projects/giant-beads/app/.venv/bin/python projects/giant-beads/app/app.py
```

Serves at http://127.0.0.1:7863. Renders land only in the gitignored
`app/.render-scratch/` directory.

## Build the venv (once)

```bash
uv venv projects/giant-beads/app/.venv
uv pip install --python projects/giant-beads/app/.venv/bin/python gradio
```

The app was built and smoke-tested with Gradio 6.31.0 and OpenSCAD
2026.10.11. OpenSCAD must be on `PATH`.

## Family model

**Global** (left column):

- **Width**: the face/enclosing-circle diameter, 60 to 240 mm.
- **String hole**: the throat diameter, 10 to 40 mm.
- **Heights** are shown as a readout because the templates define them
  from the family width:
  - letter, heart, star: `width / 2`
  - doughnut spacer: `width / 4`
  - shallot spacer: `width`

**Per bead** (right column):

- Shape controls only (letter/font/size/weight, heart roundness, star
  roundness/points/petal depth, doughnut curvature/mouth, shallot
  curvature).
- **Override family size** opens per-bead width and hole sliders. The
  override belongs to that bead; switching beads does not leak it to a
  sibling. This is how to make one extra-fat shallot without changing
  the rest of the set.
- **Reset this bead** restores that bead's shape defaults and clears its
  size override.

Every change renders the selected bead live through the OpenSCAD CLI.
Sliders use `.change` with `always_last` so typing in the number box and
dragging both work, while stale requests are dropped. Text fields apply
on Enter or blur.

## Downloads

- **Download bead** downloads the current render as
  `giant-bead-<bead>.stl`.
- **Build family zip** renders all five at the current family and
  override settings, then reveals **Download family zip**. The zip
  contains the five STLs plus `family-settings.txt` with the effective
  parameters for the set.

Both use `gr.DownloadButton`, so the browser's normal download folder
and download prompt decide where the file lands. The app does not write
into `~/Downloads` itself.

## Design notes

- Native Gradio components only. The default house theme is **Aurora
  Hex**: midnight royal purple, one teal action colour, violet
  selection, and a lavender-to-mint page wash only in light mode. No
  orange or brown.
- `aurora_hex.py` is the reusable theme class shared with the
  `gradio-design` skill. `theme.py` subclasses it and appends only the
  viewer and bead-select CSS. No custom HTML or JavaScript.
- The viewer stage is aubergine and the mesh keeps its cool lavender
  default; the old warm brass filter is gone.
- The viewer toolbar's Undo/Clear buttons are hidden; the app owns the
  render state.
- The page keeps the working surface first: family size, bead choice,
  viewer, then the selected bead's controls.

## Layout

```
app/
  app.py          # Blocks layout, state, and event wiring
  family.py       # bead specs, global/override rules, render cache, zip
  aurora_hex.py   # reusable Aurora Hex Gradio theme
  theme.py        # app subclass: viewer CSS
  shared/scad.py  # OpenSCAD parsing, -D formatting, render, STL probe
```

`family.py` has no Gradio dependency, so its rules are covered by
`tests/test_app_family.py` without launching a browser or OpenSCAD.
