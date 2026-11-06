---
title: Generation app polish round 3 — log stream, anvil H1, violet ground
date: 2026-10-22
tags: [genapp, gradio, polish, app]
---

# FINDINGS: genapp polish round 3 (log stream, anvil H1, violet ground)

Branch `feat/genapp-polish3`, cut from main at c724728. Working dir
`skills/stl-forge`. Two labelled commits, explicit-path adds only; other
sessions' dirty files remain unstaged and untouched:

- 187fe44 `genapp polish 3: status textbox to appending session log stream
  (bounded 200, full stderr on FAIL) plus violet orbit ground via Model3D
  clear_color` (app/forge_tab/app.py, app/README.md)
- 450dade `genapp polish 3: master anvil H1, plain STL-forge tab label
  (blade emoji off)` (app/app.py)

## Files touched

- `app/forge_tab/app.py` (log stream + clear_color)
- `app/README.md` (one sentence: the probe/status sentence now describes the
  appending session log)
- `app/app.py` (anvil H1, plain tab label)

Skill-root README.md untouched (no sentence needed; it never mentions the
status box). BRIEF_genapp_polish3.md not deleted.

## Gate rows (measured)

| Gate | Result |
| --- | --- |
| Dash scan over touched files | 0 (app/app.py 0, app/forge_tab/app.py 0, app/README.md 0). Skill-root README.md holds 13 pre-existing em dashes but was not authored or edited this round. |
| Boot on 7863 | curl `200` |
| Log stream, handler level (on_render, touched wire-target fn): defaults then roundness=1 | seed + 2 lines, both quoted below; second line shows `roundness=1` among full params |
| Log stream, wire level (gradio_client, `/on_select` named endpoint; the change/reset endpoints are @gr.render-bound and not API-exposed) | 3 successive `/on_select` calls each return the ACCUMULATING joined log: seed + prior lines + one new line per call; FAIL call appends full openscad stderr (quoted below) |
| Log bound | 250 simulated events in-process -> `len(_SESSION_LOG) == 200` exactly (del keeps the newest 200, oldest dropped) |
| H1 | `grep -n "# ⚒ STL-forge" app/app.py` -> line 41. U+1F6E0 count in app/app.py: 0. |
| clear_color set | app/forge_tab/app.py line 358: `model3d = gr.Model3D(value=boot_stl, clear_color=(0.10, 0.02, 0.16, 1.0),` |
| Regression | `python3 -m pytest projects/giant-beads/tests/ -q` -> 34 passed (9.75s) |
| Sketch tab | untouched this round; `/on_sketch` live through gradio_client -> face-on PNG `sketch_star_faceon.png` + readout `valley ratio 0.6314` |

### Quoted log texts

Handler level (on_render, in-process through the real Blocks build):

```
2026-10-22T13:27:18 app booted, gradio 6.30.0, 6 templates
2026-10-22T13:27:21 bead_star(width=120, roundness=12, points=5, petal_depth=3, hole_diameter=20) ... OK 255000 facets 12750084 bytes
2026-10-22T13:27:22 bead_star(width=120, roundness=1, points=5, petal_depth=3, hole_diameter=20) ... OK 41276 facets 2063884 bytes
```

Wire level (gradio_client, 3rd call forces the failure):

```
2026-10-22T13:27:58 app booted, gradio 6.30.0, 6 templates
2026-10-22T13:28:55 bead_star(file defaults) ... OK 255000 facets 12750084 bytes
2026-10-22T13:28:56 bead_star(file defaults) ... OK 255000 facets 12750084 bytes
2026-10-22T13:28:57 parametric_heart_reference(file defaults) ... FAIL openscad exit 1: Current top level object is not a 3D object.
```

The scripted `parametric_heart_reference` render goes through the same
`scad.RenderError` path as any openscad exit-code failure, so larger
stderr bodies (the whole console tail, capped at 800 chars by
`scad._run`) land in the log unchanged.

## Notes and limits

1. **Mesh body colour is NOT reachable in gradio 6.30** via native means.
   Verified in the installed source (`app/.venv/.../gradio/components/
   model3d.py` line 40/71/93): the only colour prop is `clear_color`,
   "a tuple of 4 floats between 0 and 1 representing RGBA values" (and it
   defaults to `self.clear_color = clear_color or [0, 0, 0, 0]`). There is
   no material/mesh-colour prop, so per the brief no custom CSS/HTML/JS
   was added. The only native alternative is `clear_color` itself, now set
   to dark violet `(0.10, 0.02, 0.16, 1.0)`; the grey mesh gains contrast
   but its own colour stays native-unedited. No other prop moves it.
2. **Monospace for the log**: gradio 6.30 ships NO native monospace class
   of its own - compiled CSS carries only the `--font-mono` theme variable
   (no utility class selectors). The log box is tagged via the native
   `elem_classes=["stl-session-log"]` hook as the brief's alternative, and
   per the brief ("otherwise skip CSS") no custom CSS was added.
3. **Old-guard paths preserved as log entries**: the stale-controls guard
   and the no-template path now append FAIL entries (the info the old
   status box used to show is not lost); non-RenderError exceptions keep
   the traceback tail the old box printed.
4. **Boot-line semantics**: `_seed_boot_log()` seeds exactly one line
   (`app booted, gradio 6.30.0, 6 templates`). The build-time defaults
   render is deliberately NOT logged on success (it is not a UI event and
   the gate counts seed + event lines); its FAILURE would be logged
   immediately after the boot line with the full stderr, so nothing breaks
   silently before first touch.
5. **Bound unit**: truncation counts ENTRIES (one per render event), each
   normally one line; a FAIL entry can carry a small multiline stderr tail
   (<= 800 chars) so painted lines may slightly exceed 200 but memory
   stays bounded. Measured: 250 events -> exactly 200 entries.
6. gradio_client view_api names the log output
   `session_log_newest_at_bottom` (violet Model3D exposes no colour at the
   API layer, as expected).
7. Sketch tab's standalone run keeps its own H2 header (brief permits its
   docstring; no H1 conflict). Forge tab's standalone header likewise
   untouched - the blade emoji left only the MASTER tab label.
