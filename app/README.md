# stl-forge generation app

A native-Gradio control panel over the `projects/giant-beads` templates.
Two tabs:

- **STL Forge** - pick a template from `projects/giant-beads/templates/*.scad`;
  its top parameter block is parsed into one control per literal-valued
  parameter (`info=` from the file's own comments). Both tabs are live with
  no Render button: template selection rebuilds the controls and every
  control change renders straight through the OpenSCAD CLI
  (`--export-format=binstl`, one `-D key=value` per control, defaults
  round-trip cleanly) into a 1/3 : 2/3 column split - left = template
  dropdown + controls + Reset, right = the interactive `gr.Model3D`
  binary-STL orbit view with a full-width `gr.DownloadButton` (always
  bound to the latest `<stem>_app.stl` render) and an appending session
  log under it (one entry per render, newest at the bottom, full
  OpenSCAD stderr on failure).
- **Geometry Playground** - four sliders (width, points, roundness,
  petal_depth) drive the star/petal sketch in `bead_star.scad` via a
  tiny driver file that `use`s it (the .scad maths stays the single
  source of truth); "Render sketch" shows a fast face-on PNG of
  `star_2d` extruded 1 mm plus the echoed valley ratio.

Renders land ONLY in `app/.render-scratch/` (gitignored) - this app is a
control panel, not a delivery mechanism.

## Run

From the skill root (the app builds its own venv; the Hermes venv is not
a dependency):

```
app/.venv/bin/python app/app.py
```

Serves the master app at http://127.0.0.1:7863 (allowed_paths cover the
scratch and templates dirs).

Each tab also stands alone, per the sub-app contract:

```
app/.venv/bin/python app/forge_tab/app.py    # STL Forge only,  port 7864
app/.venv/bin/python app/sketch_tab/app.py   # Playground only, port 7865
```

## Build the venv (once)

```
cd <skill root>
uv venv app/.venv
uv pip install --python app/.venv/bin/python gradio
```

## Layout

```
app/
  app.py               # master: composes the two tabs, launch(port=7863)
  forge_tab/app.py     # tab 1: template dropdown + parameter controls + render
  sketch_tab/app.py    # tab 2: star/petal sketch dials + face-on PNG
  shared/scad.py       # OpenSCAD CLI helpers (render, parse, probe)
```
