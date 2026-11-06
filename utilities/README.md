# utilities/ — shared pipeline

Everything used by more than one project lives here. Projects import or
shell out to these paths; projects must not copy them.

| Path | What |
|---|---|
| `forge.py` | Generic headless renderer/packager. Reads `presets.json` beside it (or `--presets PATH`), resolves each preset's `template` under `utilities/templates/` then `projects/*/templates/`, renders binary STLs + preview PNGs, validates, and emits Bambu `.3mf` for multi-part presets. |
| `templates/box.scad` | Open-top storage-box family (example generic template). |
| `presets.json` | Box-family presets only (`drawer_organiser`, `cable_tidy`, `screw_tray`, `pencil_cup`). Bead presets live with their project. |
| `core/stl_probe.py` | Format-agnostic STL inspector (bbox, slice-z; reads binary and ASCII). |
| `core/annotate_preview.py` | Delivery verification overlay (needs Pillow). |
| `references/` | `alt-cad-routes.md`, `bambu-3mf.md`, `disc-golf.md`, `shape-acceptance.md`. |
| `scripts/` | One-off maintenance scripts. |
| `app/` | Gradio generation app (renders to `utilities/app/.render-scratch/` only). |

## Run from the repo root

```bash
python3 utilities/forge.py --out <scratch>/stl-check          # all box presets
python3 utilities/forge.py --only drawer_organiser --out <dir>
python3 utilities/forge.py --presets projects/giant-pony-beads/presets.json --out <dir>
```

`forge.py` base is the `utilities/` directory (`HERE`), project templates
resolve via `REPO_ROOT/projects`. See root `README.md` for the full CLI
and validation rules, and `AGENTS.md` for placement rules.
