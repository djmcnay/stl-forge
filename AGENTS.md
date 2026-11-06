# AGENTS.md — stl-forge layout contract

This file is the agent-facing enforcement of the repo structure.
Human overview: `README.md`. Agent skill contract: `SKILL.md`.
Utilities detail: `utilities/README.md`. Vault rules: `vault/README.md`.

Root layout (no other top-level content; tool-installed dirs in
`.agents/` / `.opencode/` are owned by their tools, do not hand-edit):

```
.
├── README.md        # human overview (maintain with every structural change)
├── AGENTS.md        # this contract
├── SKILL.md         # skill contract for agents picking up this repo
├── .gitignore       # *.stl / *.3mf / .tmp / regr-* ignored
├── LICENSE
├── utilities/       # shared pipeline + tools (see below)
├── projects/        # finished part families (see below)
└── vault/           # Obsidian vault for learnings (YYYYMMDD + tags)
```

## utilities/

Code shared between projects (or generic tooling). Current files:

- `forge.py` — generic renderer/packager (run from repo root:
  `python3 utilities/forge.py --out <dir>`). Path base is
  `utilities/`; project templates resolve via `REPO_ROOT/projects/*/templates`.
- `core/` — STL probe + preview annotation helpers.
- `templates/box.scad` + `presets.json` — the open-top box example family.
- `references/` — CAD-route / Bambu / shape-acceptance references.
- `scripts/` — one-off scripts (`.gitkeep` if empty).

App panels are per-project, not master utilities: a project may add
`projects/<project>/app/` (e.g. `projects/giant-beads/app/`, renders
only to its own `.render-scratch/`).

Rule: anything used by TWO projects goes in `utilities/`, not copied per
project. A template used by one project only lives under that project.

## projects/<project>/

Each finished family owns its parameters and renders. Required skeleton
(create all dirs even if empty, with `.gitkeep` where needed):

```
projects/<project>/
├── README.md          # project overview + param story (non-coders must cope)
├── main.py            # optional one-command builder (stdlib only)
├── presets.json       # named presets consumed by main.py / forge.py
├── param-defaults.json # canonical defaults snapshot (keep in sync with templates)
├── templates/         # completed .scad templates (SKILL.md references these)
├── tests/             # project-specific unit tests
├── tools/             # project-specific helpers
├── app/               # optional per-project app (e.g. Gradio panel; .render-scratch ignored)
├── solidcraft/        # SolidCraft models (DO NOT DELETE; never clean these)
├── stl/               # generated STLs, GITIGNORED (never commit .stl)
└── .tmp/              # WIP / scratch, GITIGNORED and purged regularly
```

- `templates/` is the committed, reviewed geometry. No `.tmp` copies
  in `templates/`, no stray `.scad` at project root.
- `main.py` (if present) must work from any cwd (resolve relative to
  `__file__`). It imports `forge` from `utilities/` via a sys.path shim.
- `param-defaults.json` mirrors the parameter defaults in
  `templates/*.scad` + `presets.json` so a new agent can copy defaults
  without reading SCAD. Update it in the same commit as any template
  default change; tests may assert on it.
- `solidcraft/` is long-lived model state. Never delete, never move to
  `.tmp/`, never empty it for tidiness.
- `stl/` and `.tmp/` are always gitignored. If a render lands in git
  status, the ignore has broken — fix the ignore, don't commit the mesh.
- Regression archives (`regr-*`, huge probe STLs/PNGs/logs) belong in
  `.tmp/archived-regr-*` until purged — never at project root, never
  tracked.

## vault/

Obsidian vault for learnings (see `vault/README.md` for the full rule):

- Files only, no subfolders. Every learnings file is `YYYYMMDD_topic.md`
  with YAML frontmatter (`title`, `date`, `tags`).
- Stray `FINDINGS_*.md` at root or in `projects/` belong in `vault/` —
  rename with `git mv`, add frontmatter, keep the body byte-identical.

## Placement rules (anti-proliferation)

- New markdown learning / investigation note → `vault/`, never scattered.
- New reference doc for the generic pipeline → `utilities/references/`.
- New shared `.scad` helper → only in `utilities/templates/` if it is a
  completed template, or in `projects/<p>/templates/` if it belongs to
  that family.
- New project → `projects/<name>/` skeleton above; update root `README.md`
  (project list) in the same commit.
- Deliverable/draft STLs for the principal → `~/Downloads/stl-forge/`
  (the allowed external folder). Not in the repo.

## Verification before pushing

```bash
python3 utilities/forge.py --out <scratch>/stl-check   # exit 0, summary table
python3 -m pytest projects/<project>/tests -q
git status --short   # no *.stl / *.3mf staged
```

- Never `git add -A` without checking `git status --short` shows only
  source + docs (renders/`regr-*` were historically swept into history).
- After any geometry change: render the affected preset, validate the
  binary STL (`84 + 50*n`), and refresh the deliverable STL for the
  principal. A template default change and `param-defaults.json` update
  ship together.
