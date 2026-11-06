# FINDINGS: generation app UX revision (columns, live render, reset)

Run: 22 Oct 2026, branch `feat/genapp-ux-revision` (cut from `main`,
working tree = skill root). NO merge, NO push. Other sessions' dirty
files (minty-sync, pi-media-server, FINDINGS_star_face_fillets) were
left unstaged and untouched; `.agents/`/`.opencode/`/BRIEF_genapp_ux.md
stay untracked; `app/.venv` and `app/.render-scratch` are gitignored.
Gradio skill read first (SKILL.md + references/api-signatures.md +
references/event-listeners.md + references/examples.md); the dynamic
per-template wiring follows the skill's documented `@gr.render`
"Render Merge" pattern (stable components declared after the render
block, event wiring re-bound inside the render function on every
rebuild).

## Files touched (exhaustive)

```
app/forge_tab/app.py     REVISED  50:50 columns (left: dropdown +
                                  @gr.render controls + Reset + status;
                                  right: ONLY gr.Model3D), no Render
                                  button, control .change / dropdown
                                  .select live renders (always_last),
                                  Reset = file defaults without rebuild,
                                  boot-time defaults render
app/sketch_tab/app.py    REVISED  same column split, sliders render live
                                  on .change, Reset sketch (no rebuild +
                                  re-render), gr.update() keeps previous
                                  PNG on failure
app/README.md            REVISED  ONE sentence replaced (the fence's
                                  cap): live/no-button/column layout,
                                  supersedes the old Render-button text
```

Commits (`feat/genapp-ux-revision`, explicit-path `git add` only):
`2c013f0` forge tab, `4160063` sketch tab, `aea3dad` README sentence.
Nothing outside `app/**` modified (final `git status --porcelain`
verified: only the three files above, plus other sessions' pre-existing
dirty files). Skill-root `README.md` untouched — it describes no
button/readout layout, so its one-sentence allowance was not needed.

## Gate rows (measured)

| Gate | Result | Numbers |
|---|---|---|
| 1. Layout structurally correct | PASS | In-process Blocks introspection + live `/config` of the booted master: rows **2**, each a 50:50 pair of `gr.Column(scale=1, min_width=320)`; buttons exactly **2** (`Reset`, `Reset sketch`), **0** Render buttons; `model3d` **1**, `image` **1** (old app had 2 images + probe outputs), `dropdown` **1**, `slider` **4**. Rendered `/config` of the RUNNING server shows dependency triggers `select` (dropdown, once), `change`/`change,load` → **always_last**, `click` → resets |
| 2. Dynamic wiring materialises | PASS | Simulated page-load render (`Renderable.apply("bead_star")` under the same `LocalContext` gradio sets for real events): dependencies **7 → 13**: **5** control `.change` deps (inputs = dropdown + 5 controls = 6) targeting Model3D + status, `trigger_mode="always_last"`; **1** Reset `.click` (input = template dropdown) with outputs [5 slider values, Model3D, status] — outputs at positions 6/7 verified bound to the model3d/status components |
| 3. Master boots on 7863 | PASS | `curl -o /dev/null -w '%{http_code}'` → **200**; served `/config` shows Model3D `value` = served `bead_star_app.stl` (boot-time defaults render) — the right column is never empty, and no facet/byte or preview widgets exist next to it |
| 4. Change-driven render, defaults | PASS | `on_render("bead_star", *defaults)` → **255,000 facets / 12,750,084 bytes**, **md5 143833c3…**, 1.2 s |
| 5. Live override roundness=1 | PASS | **41,276 facets / 2,063,884 bytes**, **md5 e733ec9e…** — differs from gate 4 (reproduces the previous run's gate 6 numbers exactly), 0.61 s |
| 6. Sketch handler at defaults | PASS | `on_sketch(120, 5, 12, 3)` → PNG **7,308 bytes** (non-empty), 0.12 s, echo hook live: `valley ratio 0.6314` |
| 7. Reset = file defaults | PASS | After gate-5's changed-value renders, `on_reset("bead_star")` returned **[120, 12, 5, 3, 20]**, byte-equal to `[p.value for p in parse_template_params("bead_star")]` for all 5 controls; status "✓ bead_star reset to file defaults · facets 255,000 \| 12,750,084 bytes" |
| 8. Reset re-render byte-determinism | PASS | reset render md5 **143833c3…** == fresh `on_render` at those defaulted values md5 **143833c3…** == gate-4 defaults md5 — byte-identical across 3 independent openscad invocations |
| 9. Error path (no traceback) | PASS | `on_render("bead_common")` and `on_reset("bead_common")` both return cleanly: `⚠ OpenSCAD render failed / openscad exited 1 (bead_common STL): Current top level object is empty.` in the status widget; gr.update() keeps the previous STL/PNG on screen. A stale-arity call (control set ≠ parsed param count) also degrades to a status note, never a crash |
| 10. Regression suite | PASS | `python3 -m pytest projects/giant-beads/tests/ -q` → **34 passed** in 7.93 s |
| 11. Scratch-dir discipline | PASS | all renders land only in `app/.render-scratch/` (`bead_star_app.stl`, `sketch_star_faceon.png`, `sketch_driver.scad`); no project output folder touched |

## Design decisions & deviations (all deliberate)

- **Slimmed `run_bead_render`** (handler-level entry): the face-on PNG
  render was removed — nothing displays it now, and it would add
  ~1–2 s to every live event. Returns `{"stl","facets","bytes","probe"}`
  (module docstring updated; this tab is its only caller repo-wide).
- **The facet/byte probe survived as STATUS TEXT**: the brief bans the
  readout *widget* in the right column; the probe line lives on inside
  the left-column status textbox ("✓ bead_star · facets 255,000 |
  12,750,084 bytes"), which doubles as the mandated visible error
  surface.
- **`trigger_mode="always_last"`** on every live `.change`: Reset
  writes default values into the controls, and gradio fires each
  control's `.change` on value updates — always_last collapses that
  cascade (and rapid consecutive slider moves) to the newest state
  instead of a backlog of stale renders. Reset itself still renders
  authoritatively, so Reset → at most one redundant follow-up render.
- **Reset re-parses the .scad file** rather than using cached values —
  same file as the build-time parse, so "single source of defaults"
  holds; controls are never rebuilt by Reset (gate 7 returned values
  could have come straight from the file, gate 8 proves the render
  determinism).
- **Boot-time defaults render** (master and both standalone tabs) so
  the first page load is never empty; failures degrade to a status
  note instead of aborting the app.
- **Incident: stale server on 7863.** The FIRST curl-200 came from a
  leftover pre-revision server (PID 61714, started 11:24 by the
  previous generation-app session; my boot log showed
  "Cannot find empty port"). Killed it, relaunched, and re-verified
  every boot row against the revised app; server stopped afterwards.
- **app/README.md fence cap**: exactly one sentence replaced. The
  Geometry Playground bullet's trailing clause still carries the old
  "Render sketch" wording inside its (unedited) semicolon sentence;
  the new sentence explicitly supersedes it, but the orchestrator may
  want a second sentence at some later pass.
- **Sketch tab got the same 50:50 split** although the brief's
  column clause names STL Forge only — the Reset-in-left-column rule
  is stated for BOTH tabs, so the mirrored shape makes it literal.
- **Known race (inherited, noted)**: a control `.change` fired just
  before a template switch could queue one render with a mixed control
  set; the new stale-arity guard converts that into a status note
  ("re-select the template") instead of a nonsense render.

## How to run

```bash
# from the skill root (skills/stl-forge)
app/.venv/bin/python app/app.py                # master → http://127.0.0.1:7863
app/.venv/bin/python app/forge_tab/app.py      # standalone tab 1, port 7864
app/.venv/bin/python app/sketch_tab/app.py     # standalone tab 2, port 7865
```
