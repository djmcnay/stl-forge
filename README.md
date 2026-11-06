# stl-forge

Headless, code-first parametric STL generation through the OpenSCAD CLI:
parameters in, validated binary STL files + preview PNGs out — no GUI, no
network, Python stdlib only. The skill is TWO things at once:

1. **A general parametric geometry / OpenSCAD template skill.** `forge.py`
   at the root is the generic renderer/packager: it runs `templates/*.scad`
   against named presets (`presets.json`) through the `openscad` CLI,
   validates every artefact, renders shaded preview PNGs (iso/front/top/
   bottom/hole), and prints a summary table. `templates/box.scad` is the
   generic open-top box family; any preset can point at any template via
   its `"template"` key.
2. **A host for finished "projects".** `projects/<name>/` directories own a
   completed part family end-to-end: their own `templates/`, `presets.json`,
   `tests/`, `README.md` and a one-command `main.py` that generates
   parameterised STL artefacts. The active project is
   `projects/giant-beads/` (giant letter beads, heart bead, star/flower
   bead) — see its README for the family, parameters and provenance.

## Target tree

```
skills/stl-forge/
├── SKILL.md                 agent contract (trimmed; points at the READMEs)
├── README.md                this file
├── forge.py                 generic renderer/packager (root families)
├── presets.json             root presets — the box family ONLY
├── templates/box.scad       generic open-top box template
├── core/                    STL probe + preview annotation utilities
│   ├── __init__.py
│   ├── stl_probe.py         format-agnostic STL inspector (bbox, slice-z)
│   └── annotate_preview.py  delivery verification overlay (needs Pillow)
├── references/              alt-cad-routes.md, bambu-3mf.md,
│                            shape-acceptance.md
└── projects/
    └── giant-beads/
        ├── README.md        the giant-bead family doc
        ├── main.py          ONE-COMMAND entry (see below)
        ├── presets.json     bead_D, bead_default, bead_smooth
        ├── templates/       bead.scad, bead_heart.scad, bead_star.scad
        │                    + parametric_heart_reference.scad,
        │                      parametric_star_flower.scad (provenance)
        ├── tests/           pytest suite (spec parsing, naming, STL rule)
        └── references/      heart-bead.md (family verification bands)
```

## Example commands

From the repo root:

```bash
# Root suite: all four box presets -> STLs + previews (exit 0 = all valid)
python3 skills/stl-forge/forge.py --out /tmp/stl-check

# A subset
python3 skills/stl-forge/forge.py --only drawer_organiser,cable_tidy --out /tmp/boxes

# Point forge.py at a preset file that lives with its project
python3 skills/stl-forge/forge.py --presets skills/stl-forge/projects/giant-beads/presets.json --out /tmp/beads-check
```

`forge.py`'s CLI surface is stable: `--only n1,n2` (subset), `--out DIR`
(output dir), `--word WORD` (one row-layout STL of the word's unique
letters), `--word-gap MM` (clear gap between neighbouring beads, default
10), and `--presets PATH` (preset file; default: root `presets.json`).

### The one-liner (project entry)

```bash
python3 skills/stl-forge/projects/giant-beads/main.py \
    --width 120 --letters "C A M I L A" --parts heart,star,flower
```

That single command renders `beads_CAMILA.stl` (one bead per UNIQUE letter,
row layout, clear 10 mm gap), `bead_heart.stl`, `bead_star.stl` and
`bead_flower.stl`. Default save location: `$HOME/Downloads` (created if
missing); `--save-to PATH` redirects; `--previews` additionally writes PNG
previews into `<save-to>/previews/`. `--preset bead_D` renders one bead
preset (body + letter + assembly STLs plus the Bambu `.3mf`), and
`--spec '{"letters":"CAMILA","parts":"heart,star,flower","width":120,
"save_to":"/tmp/out"}'` is the alternate dict input form (spec fields
first, explicit flags override). Exit 0 ONLY when every requested artefact
exists and is a valid binary STL — facet count `n` at offset 80 with
exactly `84 + 50*n` bytes — and each failed job prints a precise stderr
message.

For an interactive GUI alternative, the native-Gradio control panel in
`app/` (template parameter dials + star-sketch playground, renders to
scratch only; see `app/README.md`) is served with
`skills/stl-forge/app/.venv/bin/python skills/stl-forge/app/app.py` at
http://127.0.0.1:7863.

## Running the tests

```bash
python3 -m pytest skills/stl-forge/projects/giant-beads/tests -q
```

Pure-processing tests always run; renders are gated with
`pytest.mark.skipif` and only execute when `/Applications/OpenSCAD.app`
exists (tiny 60 mm width for speed).

## Prerequisites

- OpenSCAD 2021.01 or newer on PATH (`openscad --version` proves it).
  macOS: `brew install openscad@snapshot` (the plain cask was disabled
  2026-09-01 over a notarisation failure); the app binary sits at
  `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`.
- Python 3, stdlib only (`core/annotate_preview.py` needs Pillow).

## Validation rules (standing)

- The pipeline emits BINARY STL by design (`--export-format=binstl`).
  Binary = 80-byte header + little-endian uint32 facet count at offset 80
  + `n` 50-byte records; file size is exactly `84 + 50*n`. ASCII STLs
  start with "solid"/`facet normal` — awk over them only with
  `--export-format asciistl` forced, or use `core/stl_probe.py`, which
  reads both flavours.
- Measure, never trust: prove geometry from the STL vertex stream, not
  from previews or a run's self-report (`core/stl_probe.py`, cross-section
  probes in the references).
- Multi-bead `--word`/`--letters` output is one STL of several separate
  solids — spacing claims come from a straight-on FRONT render plus a
  per-shell bbox probe, never from an iso view, and each facet goes to the
  NEAREST expected body centre, not a fixed coordinate bucket.

## Presets shape

```json
{"presets": {"<name>": {"width": .., "depth": .., "...": ".."}}}
```

Each preset may carry `"template"` (filename resolved under the root
`templates/` first, then every `projects/*/templates/`), optional `"parts"`
(one `<name>_<part>.stl` per part plus the combined `<name>.stl` for
`part="assembly"`) and `"preview"` (`part` flag added to previews).

Root presets (`presets.json`, `templates/box.scad`, all eight box params;
`floor` 2.4 and `corner_r` 5 for all):

| preset | width | depth | height | wall | div_n | div_m |
|---|---|---|---|---|---|---|
| drawer_organiser | 120 | 80 | 30 | 2.4 | 3 | 2 |
| cable_tidy | 90 | 90 | 40 | 3 | 2 | 2 |
| screw_tray | 60 | 45 | 25 | 2 | 2 | 1 |
| pencil_cup | 25 | 25 | 80 | 2.4 | 1 | 1 |

The bead presets live with their project:
`projects/giant-beads/presets.json` holds `bead_D`, `bead_default` and
`bead_smooth` (identical parameter values to the old shared file).

## Delivery (standing policy, condensed)

Render into the principal's designated project output folder when one is
on record — never hand over a path under `.hermes/` or scratch. The
delivery folder holds the combined `<name>.stl` of the REQUESTED preset
(default `bead_default`) plus that preset's previews; split
`_body`/`_letter` parts and non-requested presets stay in scratch unless
explicitly asked. Letter/name runs ship the merged single STL (the two
colours are painted by hand in Bambu Studio). Overwrite the same
`<name>.stl` filename when geometry supersedes old deliverables; never
delete what is in the folder without snapshotting. Ship the runnable
recipe (`forge.py` or the project template + presets) beside the STL,
re-copied fresh, and smoke-test it from inside the folder. Bead
deliverables carry `bead_*.3mf` (Bambu-native, one object = two parts,
extruder 1/2 pre-assigned — no colour painting; core-spec colour 3MFs get
degraded to Color PAINT by Bambu Studio, see
`references/bambu-3mf.md`) and an ANNOTATED VERIFICATION PNG drawn with
`core/annotate_preview.py`. After EVERY change to the skill, refresh the
default preset's deliverables in the project folder within the same turn.
When the principal is away or asks, the same artefacts also go out on
Telegram in ONE shell call (token from the profile `.env`, `sendPhoto`
with `-F photo=@<path>`, `--form-string` for the caption, and delivery is
only claimed when the parsed reply shows `ok:true` with a
`result.message_id`). Visibility is part of delivery: a target-vs-actual
comparison image goes to the project folder at the first working draft
and at every milestone, BEFORE hours are spent on gates or fits.

## Reference documents

- `references/alt-cad-routes.md` — Fusion headless attempts, TinkerCAD,
  CadQuery, manifold sanity probes.
- `references/bambu-3mf.md` — Bambu `.3mf` schema anatomy, headless load
  tests, multi-object plate composition.
- `references/shape-acceptance.md` — silhouette tuning acceptance
  calibration (metric vs defect class, region awareness, vector
  measurement, known-answer self-tests).
- `projects/giant-beads/references/heart-bead.md` — heart-bead family
  verification bands and construction decisions.
