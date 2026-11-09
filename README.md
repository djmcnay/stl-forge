# stl-forge

A headless, code-first parametric STL workshop: parameters in, validated
binary STL files + preview PNGs out — no GUI, no network, Python stdlib
only. It started as an OpenSCAD skill; the common bead machinery and the
projects using it now live here as a standalone repo so agents can pick it
up and build from the templates.

## Layout

```
.
├── README.md        this file (human overview)
├── AGENTS.md        agent layout contract (structure enforcement)
├── SKILL.md         skill contract for agents (OpenSCAD pipeline + bead guide)
├── utilities/       shared pipeline — see utilities/README.md
│   ├── forge.py         generic renderer/packager
│   ├── templates/box.scad + presets.json   the box example family
│   ├── core/            STL probe + preview annotation
│   └── references/      CAD routes, Bambu, shape acceptance
├── projects/
│   ├── giant-beads/   giant pony / letter beads (see its README; app/ is per-project)
│   └── cards/         card-game accessories (UNO Junior deck box first)
├── vault/           Obsidian vault for learnings (YYYYMMDD + tags; see vault/README.md)
```

Rules (full contract in `AGENTS.md`):

- `utilities/` is anything shared between projects.
- `projects/<name>/` owns a finished family end-to-end (templates, presets,
  tests, tools, README). Every project has `templates/`, `stl/` (gitignored),
  `tests/`, `solidcraft/` (never delete), `tools/`, `main.py` (if needed),
  `param-defaults.json`, `README.md` and `.tmp/` (gitignored WIP, purged
  regularly).
- Generated meshes never commit (`*.stl` / `*.3mf` ignored). Only templates
  and parameters commit; regression archives live under `.tmp/`.
- Learnings and investigation notes go in `vault/YYYYMMDD_topic.md`, never
  scattered at the root or inside a project.

## Projects

- **`projects/giant-beads/`** — giant beads for friendship bracelets
  (letter bead with the fillet-well / "gravitational well" string hole,
  heart bead, star/flower bead). One-command builder:

  ```bash
  python3 projects/giant-beads/main.py \
      --width 120 --letters "C A M I L A" --parts heart,star,flower
  ```

  See `projects/giant-beads/README.md` for the family, parameters
  and mouth recipe.

- **`projects/cards/`** — playing-card accessories. The first part is a
  parametric UNO Junior deck box (56 x 87 mm cards, 15 mm deck, 2 mm
  walls, engraved Artemis logo). Validated card sizes and corner radii
  live in `projects/cards/card-sizes.json`; the model is a SolidCraft
  design at `projects/cards/solidcraft/uno-junior-box.sc`.

- **Box family (utilities example)** — open-top storage boxes via
  `utilities/forge.py`:

  ```bash
  python3 utilities/forge.py --out /tmp/stl-check              # all four box presets
  python3 utilities/forge.py --only drawer_organiser --out /tmp/boxes
  python3 utilities/forge.py \
      --presets projects/giant-beads/presets.json --out /tmp/beads-check
  ```

## Quick start

Prerequisites: OpenSCAD 2021.01+ on PATH (`openscad --version`);
macOS `brew install openscad@snapshot`. Python 3 stdlib only
(`core/annotate_preview.py` needs Pillow, the Gradio app needs its own
venv — see `projects/giant-beads/app/README.md`).

Build is headless through the OpenSCAD CLI (`--export-format=binstl`).
The pipeline emits **binary STL by design** (80-byte header + uint32 facet
count at offset 80 + 50 bytes/triangle; file size exactly `84 + 50*n`).
Measure geometry from the STL vertex stream (`utilities/core/stl_probe.py`),
never from preview proportions. The Gradio generation app is served with
`projects/giant-beads/app/.venv/bin/python projects/giant-beads/app/app.py` at
http://127.0.0.1:7863.

Tests:

```bash
python3 -m pytest projects/giant-beads/tests -q
```

## Delivery

Render the requested artefacts into the principal's designated output
folder (`~/Downloads/stl-forge/` for this repo). The deliverable folder
holds the combined `<name>.stl` of the requested preset plus its previews;
split `_body`/`_letter` parts stay in scratch unless explicitly asked.
Ship the runnable recipe (`forge.py`, presets, templates) beside the STL,
re-copied fresh and smoke-tested from inside the folder. Bead deliveries
carry a Bambu-native `.3mf` (one object = two parts, extruder 1/2
pre-assigned) and an annotated verification PNG
(`utilities/core/annotate_preview.py`). An STL carries no object concept
(bare triangle soup): several separate solids travel in one file, and the
slicer splits them via *Split → To objects*.
