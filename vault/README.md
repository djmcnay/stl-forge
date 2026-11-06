# vault/ — Obsidian vault for learnings

This folder is an Obsidian vault for investigation notes, findings and
design decisions. It exists to stop dozens of markdown files scattering
across the repo.

## Naming

Every note file is named `YYYYMMDD_topic.md` — the date the work was done,
then a kebab-case topic:

```text
20261022_bead-flower-step1.md   # 2026-10-22, bead flower step 1
```

- Flat only: no subfolders. Indexing is by filename + tags, not folders.
- `YYYYMMDD` is the content date (when the investigation happened), not
  the date you tidy the file. Never invent a date — use the run date.
- Topic is short, specific, searchable: `generation-app`, `shared-mouth`,
  `star-face-fillets`.

## Frontmatter

Every note starts with YAML frontmatter:

```yaml
---
title: <human title>
date: <YYYY-MM-DD>
tags: [<tag>, <tag>, ...]
---

<body unchanged>
```

- `title` is the one-line summary.
- `date` is ISO `YYYY-MM-DD` (same date as the filename).
- `tags` are relevant to the note (project / topic / tool, e.g.
  `bead`, `flower`, `giant-pony-beads`, `openscad`, `gradio`).
  Use at least the project and the tool.

## What goes here vs. elsewhere

- New investigation / findings / reconstruction notes → `vault/`.
- Standing reference docs for the pipeline (`alt-cad-routes` etc.) stay
  in `utilities/references/`.
- Project facts (parameters, mouth recipes, verification bands) stay in
  the project's own `README.md` / `references/`.
