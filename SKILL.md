---
name: stl-forge
description: "Parametric STL generation from code via the OpenSCAD CLI: generic template pipeline plus finished project families."
version: 0.8.8
author: Araminta Milland-Wilde (araminta), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3D-Printing, CAD, STL, OpenSCAD, Parametric]
    related_skills: [coding-agent-dispatch]
---

# stl-forge

A headless, code-first pipeline for parameterised 3D printing: edit a
parameter block in a `.scad` template, or write named presets into
`presets.json`, run `forge.py`, and out come validated STL files, a Bambu-native
project `.3mf` for every multi-part preset (one object, two parts,
per-part filament slots pre-assigned - no painting in the slicer), plus
shaded preview PNGs (five inspection angles per part: iso, front, top,
bottom, hole) for inspection before slicing. Ships box, bead and heart-bead families.

Scope: simple parametric parts. OpenSCAD is a CSG/parametric language, not a
free-form modeller - organic shapes belong in a mesh editor or a browser-based
tool instead. Students and educators with a Fusion license will find its API
cannot run headless on a desktop (scripts and add-ins execute only inside a
running Fusion session, and Autodesk's Automation API is a separate paid cloud
service), so the OpenSCAD route is the one that automates cleanly.

When weighing other CAD routes (Fusion headless attempts, TinkerCAD,
CadQuery) or a manifold sanity probe, read `references/alt-cad-routes.md`.
When emitting or re-verifying the Bambu `.3mf` output (schema anatomy,
headless load test against the installed slicer binary, composing a
multi-object one-plate file from single-bead 3MFs), read
`references/bambu-3mf.md`.
When tuning a template's silhouette against reference images the
principal supplied (metric choice vs defect class, region-aware
threshold calibration, vector measurement, known-answer self-tests),
read `references/shape-acceptance.md`.
When changing or re-parameterising the heart-bead family (the bubble dial
mapping, the bead-spec bell-mouth string hole, face fillets, or its
measured verification bands), read `references/heart-bead.md`.

## Finished project families (adding one)

A new part family (the flower's rule set seen in practice): new
`templates/<family>.scad` from the round bead's machinery + ONE brief per
step (union first, fillets second, dial tuning after), deliverable
OVERWRITTEN in place in the designated folder every step. The principal
designs interactively in the generation app and states parameters as
literal dial sentences; transcribe them faithfully and never silently add
entanglements (a second fillet, a dome) he has not mentioned.

Completed one-command projects live under `projects/` - currently
`projects/giant-beads/`: a self-contained builder (`main.py`), its own
`presets.json`, `templates/` (bead, bead_heart, bead_star, bead_flower,
sharing the common mouth module `bead_common.scad`) and an input-contract
test suite. NOTE: the legacy `--parts flower` flag still drives
bead_star.scad at roundness 20 (the pre-template flower); the REAL flower
template is `bead_flower.scad` and wiring main.py/presets to it is an
explicit later step, not a given. It renders a word row plus
heart/star/flower artefacts in one call:

```bash
python3 projects/giant-beads/main.py --width 120 --letters "C A M I L A" --parts heart
```

read `projects/giant-beads/README.md` for the full contract. The
template-direct pipeline below remains the library; a finished project is
generated from it and owns its parameters afterwards.

## When to Use

- A physical part is wanted from code: parameters in, STL + previews out.
- Several preset variants of the same object are needed in one batch.
- A parameterised part has already been modelled in `.scad` and needs setting
  to a specific size.

Don't use for: organic/artistic meshes, one-off sculpts, or when a design must
be visually iterated heavily by hand in a GUI - OpenSCAD is the wrong tool for
sculpting, and Fusion 360 (with a running session) is the better interactive
alternative.

## Prerequisites

- OpenSCAD 2021.01 or newer, CLI on PATH (`openscad --version` in a
  `terminal` call proves it). macOS: `brew install openscad@snapshot` (the
  plain `openscad` cask was disabled 2026-09-01 over a notarisation failure;
  on other platforms the openscad.org build or a Linux package works).
- Python 3 with the stdlib only - no third-party packages.
- No API keys, no network. All paths below are repo-relative from the skill
  directory.

## How to Run

Through the `terminal` tool, from the skill directory:

```bash
# Every preset at once, plus shaded previews for inspection
python3 forge.py --out <output-dir>

# One or a few named presets only
python3 forge.py --only cable_tidy --out <output-dir>

# One row-layout STL of a word's unique letters for manual colour painting
python3 forge.py --word CAMILLA --out <output-dir>
```

It emits one row-layout STL of the word's unique letters plus wide iso/front
previews, with the clear gap between neighbouring beads set via `--word-gap`.

Completion criterion: `forge.py` prints a summary table listing every preset
with its STL path, byte size, facet count and preview paths - one row per
STL plus a `<name>:3mf` row per bead preset - and exits 0.

Ad-hoc renders outside the suite (a requested letter, a trial plate):
drive the template directly, never a throwaway preset -
`openscad --export-format=binstl -o out/bead_C.stl templates/bead.scad -D
'part="assembly"' -D 'letter_top="C"' -D 'letter_bottom="C"'` (repeat for
`part="body"` and `part="letter"`; preview PNGs add the `--imgsize`
`--camera` flags shown in USAGE). The matching `<name>.3mf` comes from
`forge.build_bead_3mf(...)`, which takes `pathlib.Path` objects - strings
raise `AttributeError: 'str' object has no attribute 'is_file'` - and
`import forge` is safe (its main is guarded).

Deliverables (standing policy from the principal): render into the
principal's designated project output folder when one is on record - the
preview PNGs there are what gets inspected before printing. Scratch `--out`
paths are for regression runs only, not for handing over. The delivery
folder holds ONE STL: the combined `<name>.stl` of the REQUESTED preset
(standing request: `bead_default`) plus that preset's preview PNGs. Split
`_body`/`_letter` parts and non-requested presets stay in scratch and
cross into the folder only when he explicitly asks for a non-default - the
folder must not accumulate STLs he did not ask for. Variant deliverables
follow ONE naming convention (`<preset>_bubble<N>.stl`): before removing
an old alias or a superseded variant, `cmp` it byte-for-byte against the
copy that survives - a rename without the compare can drop distinct
geometry, and two names for one file is folder clutter too. Ship the runnable
recipe beside the STL on every delivery: `forge.py`, `presets.json`,
`templates/*.scad` - the exact layout forge.py resolves relative to itself,
so it runs from inside the folder - re-copied each time so the recipe
always matches the STL next to it, and smoke-tested from the folder with
`--out` pointed at scratch so the folder stays clean. Never delete or
replace what is already in the delivery folder: snapshot it to profile
scratch first, and when new geometry supersedes the old deliverable,
OVERWRITE the same `<name>.stl` filename rather than leaving only split
parts in its place - a folder missing the bare `<name>.stl` has lost the
deliverable even when every secondary part is present. Bead deliveries additionally
carry `<name>.3mf` ONLY on explicit request (the principal is STL-only
for the moment, and an unasked 3mf is a deliverable he did not want);
still always ship an ANNOTATED
VERIFICATION PNG of the delivered bead - spec circle, centre cross,
letter bbox, labelled (draw it with `scripts/annotate_preview.py`, whose
stdout is the measurement record (the letter path for beads). Comparison images and proof renders meant for the principal's eyes go into the project folder too. Never
hand him a path under `.hermes/` or scratch, hidden directories he does
not browse - scratch is for internal verification only. When he is away
from his desk or asks for it explicitly, the same artefacts (comparison
stitch, verification PNG, status renders) also go to him on Telegram: do
the send in ONE `terminal` shell call - token via
`grep -E '^TELEGRAM_BOT_TOKEN|^TELEGRAM_TOKEN' <profile>/.env`, `sendPhoto`
with `-F photo=@<path>` and `--form-string "caption=..."` (percent-encoding
inside `-F` sends literal %20 garbage; `--form-string` misplacement breaks
curl outright) - and do not claim delivery until the parsed reply shows
`ok:true` with a `result.message_id`, since this endpoint has returned
silent empty bodies and `Not Found` from a mis-assembled call. Copies land
in the project folder in the same motion; Telegram is the channel, the
folder remains the record. VISIBILITY is part of delivery: for any
shape or geometry work, put a target-vs-actual (reference silhouette
beside the current render, captioned with the measured numbers) into
the project folder at the FIRST working draft and again at each
milestone, BEFORE spending hours on gates or fits - he judges
likeness with his own eyes, and a batch he has never seen is work he
cannot approve; when he is away, the same PNG goes to Telegram the
moment it exists (one terminal call, message_id checked). Never let a
quoted ETA pass in silence: if a run slips, post a one-line status
inside the promised window carrying the new bound - the silence, not
the delay, is what draws the interruption. After EVERY
change to this skill - geometry or pipeline - refresh the default
preset's deliverables (STL, .3mf, previews, verification PNG) in the
folder within the same turn, so what the principal opens is never stale.

Deliverable format for LETTER and NAME production runs: the principal's
current preference is the STL ALONE - he paints the two colours by hand in
Bambu Studio - so ship the merged single-STL output plus its previews and
do not spend a dispatch composing a multi-bead `.3mf` unless he asks for
one. Topping up an incomplete alphabet: render only the missing
`bead_<L>.stl` files (part="assembly", template defaults) into the delivery
folder, skip letters already present, and validate each as a binary STL;
do not regenerate or overwrite existing letters unless the principal asks to
supersede them. An STL carries no object concept at all (it is a bare triangle soup),
so several separate solids travel happily in one file: the slicer imports
them as one object and he splits them there via right-click -> Split -> To
objects, or turns on "load one file as multiple objects" in preferences.
The per-bead `.3mf` route stays available for SINGLE-bead deliveries,
where pre-assigned filament slots still earn their keep; it is the
multi-bead batch that is out of favour, not the format wholesale.

## Parameters (templates/box.scad)

All eight are overridable per preset via `presets.json` (any subset accepted;
defaults apply for the rest):

| Key | Meaning | Default |
|---|---|---|
| `width` | outer X (mm) | 120 |
| `depth` | outer Y (mm) | 80 |
| `height` | outer Z (mm) | 30 |
| `wall` | vertical wall thickness (mm) | 2.4 |
| `floor` | base thickness (mm) | 2.4 |
| `corner_r` | outer vertical corner radius (mm) | 5 |
| `div_n` | cells across X | 3 |
| `div_m` | cells across Y | 2 |

## Procedure

1. Add or edit a preset in `presets.json` (same key names as the table
   above; the shipped presets demonstrate typical wall and divider values).
   Completion criterion: JSON parses (`python3 -c "import json;json.load(open('presets.json'))"`).
2. Run `forge.py` (How to Run). Completion criterion: every preset you
   expect appears in the summary with a facet count where digits are shown.
3. Inspect the previews in `<out>/previews/` before printing. Completion
   criterion: object is recognisable in the preview PNGs; nothing renders
   blank (a <5 KB PNG would have failed validation earlier).
4. Drop the chosen STL into your slicer. Parts export in printer-ready
   orientation: z=0 is the bottom face. Completion criterion: the slicer
   imports the STL without a repair pass; if orientation off, rotate there
   (mesh orientation is fixed by design but slicer conventions vary).
5. Scale the library of shapes one family at a time: each preset may carry an
   optional `"template"` key (filename resolved under `templates/`, default
   `"box.scad"`), and forge.py resolves it per preset. Adding a new part
   family means writing `templates/<family>.scad`, adding presets whose
   `"template"` keys point at it, then rerunning the full forge.py
   validation on ALL presets (old and new) so the shared key space does not
   silently change shipped parts. A missing template file is counted as a
   failing row, not a crash.

## Porting bead.scad features onto a non-circular face

The bead family's features (bell-mouth string hole, face fillets, letter
wells) are derived from a REVOLVED cylinder whose wall sits at a constant
`width/2`. Any family whose outline is not a circle breaks that assumption in
one specific place, and the fix is always the same. This applies to every
non-circular family (heart, star, flower), not just the heart:

- BORE LANDING: bead.scad sets `half = width/2` so the flare completes
  exactly on the wall. On a non-circular face the outline crosses the hole
  axis well INSIDE that, so compute the real flank instead from that
  family's own vertex function at the current dial settings: the exact x
  where the outline crosses the hole centre line, found by linear
  interpolation of the consecutive vertex pair straddling it (take a
  vertex that sits exactly on the axis as the crossing itself; a star with
  an even point count and a tip on the axis has its flank exactly at the
  enclosing radius). Set `half = hole_entry_x`. Leave it at width/2 and
  the mouths arrive sharp-lipped, the flare finishing in empty air before
  it reaches material. The flank MOVES as the shape's dials change, so
  recompute per setting rather than pinning one measured number into the
  template. NEVER calibrate with a max-x over a fixed absolute band (the
  original `max x with abs(y) < 0.5` form): vertex spacing scales with
  width, so the band returns a point up to ~0.55 mm proud of the true
  wall and that error shrinks toward zero only at large widths - not
  scale invariant. MOUTH LINEAGE (approved by the principal, so this is canon,
  full recipe in projects/giant-beads/README.md "Approved mouth recipe"):
  bead.scad ships the FILLET-WELL mouth - the shared `bead_string_hole_well`
  module in bead_common.scad, a straight throat bore + a revolved
  quarter-round crater, G1 to the bore and the flat wall, dial
  `r_mouth_max = H/2.25 - r_fillet - R_throat`,
  `r_mouth = min(0.5*d_throat, r_mouth_max)`. The OpenSCAD pattern is
  `rotate([0,90,0]) rotate_extrude(angle=360) polygon(...)` with the arc
  sampled from -90 to 0 degrees (slope 0 at the bore, vertical at the wall,
  centre at (R_throat + r_mouth, hole_entry_x - r_mouth)), mirrored internally
  to cut both mouths in one module call. bead_heart.scad and bead_star.scad
  KEEP the v2 mouth: a straight throat bore + a spherical countersink sunk
  along the LOCAL wall normal at the interpolated crossing (sphere radius
  sqrt(R_open^2 + k^2), k = extra; rim radius = R_open exactly) - a revolved
  well cannot be tangent to their oblique walls, same verdict both kernels. SUNK MEANS INTO THE MATERIAL: bead_common's `scoop_dx = -k *
  n_out[0]` puts the sphere centre at `hole_entry_x - k`, i.e. INSIDE the
  wall (x = 55, not 65, for a +x mouth at width 120), so the bowl is deep and
  runs well inboard of the throat. A re-model that centres the sphere OUTSIDE
  the wall still meets the wall at exactly R_open, so the rim reads correct
  while the scoop is far too shallow - check the sign in the module before
  translating this mouth into another kernel. A bore-axis revolve countersink kisses an oblique wall at one
  grazing point and wedges a fin into the rim - structurally impossible in
  the v2 form; port any new family straight to it. The construction is
  shared CODE, not a shared sentence: all three templates cut their hole
  through the one subtractive module `templates/bead_common.scad`
  (`bead_string_hole(hole_entry_x, n_out, R_throat, R_open, k,
  hole_len)`), forwarding only each family's locally-derived flank
  values - patch the MODULE when the mouth must change so the fix
  populates on every bead at once, and never re-copy the geometry into a
  template.

  Prove any flank
  calibration scale
  invariant the cheap way: render at double the driving dimension and
  require the echoed entry x to double exactly.
- FACE FILLETS cannot be a revolve once the outline is non-circular. Carry
  the quarter-arc as erosion z-slices: a uniform `offset(r=-u)` of the outline
  per slab, 32 slabs, each slab taking its BASE point's inset so the chords
  stay inscribed and match bead.scad's polyline arcs. `hull()` is not a
  substitute - it fills any cleft the outline has. bead_heart.scad and
  bead_star.scad both ship these fillets at the shared family default
  `fillet_radius = width / 12` (10 mm at width 120); when porting a new
  non-circular family, mirror bead_heart.scad's slab construction verbatim
  (the `n_fillet`, `fillet_u`, `fillet_z` tables and the
  bottom/mid/top stack), never invent a fresh arc scheme.
- SLAB COUNT IS A FAMILY DECISION, not a per-template dial: heart and star
  ship the SAME n_fillet (32 - about 0.3 mm steps at a 10 mm radius, which
  shows as fine terraced bands in previews; that banding is the family
  character, not a defect to fix in one template). If the step size must
  change, raise or lower `n_fillet` in EVERY non-circular template in the
  same commit, or the beads stop matching side by side. Do not compare a
  fillet banding read against a smooth-revolve ideal - compare star against
  heart's own preview before calling anything wrong.
- UNION-ORDERED FAMILIES: when a shape is a union of an extruded outline
  and added discs (the flower's stigma rule), FILLET FIRST: build the
  erosion-slab filleted extrusion of the outline BEFORE the union; the
  union partner is a plain cylinder with sharp face rims unless the
  principal asks otherwise. The string hole then computes from the
  UNION outline at y=0, and the union summary ECHO line is the cheapest
  verifier: cross values name the exact landing surface, so a hole mouth
  moving to a different wall shows up in one render stdout instead of a
  measure pass. When an added disc SWALLOWS the outline's valleys (its
  radius exceeds the valley crossing), that is correct unioned geometry:
  the disc surface is the solid's boundary there, not a defect to tune
  away.
- THE OUTER BBOX IS INVARIANT under both operations. A hole and a face fillet
  only remove material, so if either GROWS the outer bbox the calibration is
  wrong: measure it and treat growth as a defect, not as tolerance noise.
- At a sharp plan corner the inset face pulls back by `c / sin(half-angle)`
  while the wall keeps the full tip. That is a real round's behaviour, not a
  bug; expect face extent < width - 2c there.

## Modelling the same bead in another kernel (SolidCraft)

OpenSCAD remains the default and canonical build tool for this skill. This
section is reference only, for the day a bead has to be proved in a B-rep
kernel instead, and it is what a second tool must be measured against.

SolidCraft (v0.23.1, MCP-driven, `solidcraft-cad` skill) was used to re-model
`bead.scad` from scratch, no import, and the result was gated on volume against
this template rather than on a render:

| stage | SolidCraft | this template | delta |
|---|---|---|---|
| body + fillets | 662,983.54 | 663,005 (Pappus) | 0.003% |
| + bore + countersinks | 613,854.78 | 613,560.25 | 0.048% |
| + letter well | 609,642.68 | - | pocket = ink x 5 mm |
| + bottom groove | 600,448.43 | - | ring = 0.8 x perimeter |
| whole bead | 600,448.43 | 597,964.41 | 0.415% |

The 0.415% residue is the `letter_bold = 1 mm` faux-bold dilation, which the
other kernel's sketch offset could not reproduce; price any such residue in
mm3 and name the parameter, never call a re-model equivalent on a visual match.
The stage table is the SPHERE-COUNTSINK lineage's gate; for the current
bead.scad (approved fillet-well dial) the whole-bead gate is
610,079.46 mm3 / 243 faces (SolidCraft) vs 608,548.222 mm3 on the template
(0.25%), and the sphere-mouth contrast build is 597,964.409 mm3.

Three things transfer, and they are the ones that catch a port:

- The stage table IS the gate. Subtract one feature at a time and compare with
  this template's own value; a wrong countersink sign still produces a correct
  looking rim and cost 9,024 mm3 before it was caught (sign note above).
- The letter fit rule must be carried across intact: glyph bbox half-diagonal
  = `width * letter_space / 2 - letter_bold - letter_fit_margin` (43.5 mm at
  defaults). Fitting to the bead's outer width instead of that circle is a
  different, wrong rule.
- Top-face pocket depth is `letter_recess_top + letter_insert_t` (5 mm), not
  the 4 mm recess on its own: the insert slot is part of the same cut.

Whatever kernel produced it, an exported mesh is not a deliverable until it
re-imports CLOSED. SolidCraft's 0.23.1 export leaked (open mesh, null volume)
whenever a primitive cut met a curved face, while profile cuts of the same hole
exported watertight; the STEP was exact throughout. Check the mesh, do not
assume the exporter.

## Sourcing a DOWNLOADED model (provenance gate)

When the want is a functional object someone else has already modelled
(not a code-generated part), the first job is judging provenance, not
finding a render that looks right. Download counts and star ratings say
nothing about whether the geometry works.

- Derive-from-authority beats hand-drawn. Prefer a model or generator
  whose numbers come from an authoritative measurement set (a standards
  body's certification page, a manufacturer drawing, a datasheet) over
  one a maker eyeballed from a photo. Ask where the dimensions came from
  before looking at the preview again.
- Read what a certification scheme actually certifies before repeating
  it. Most attach to a MANUFACTURER and a physical production run, not to
  a file: printing a due-approved design yourself is not the approved
  product. State that plainly instead of implying the file carries the
  approval, and verify the registry entry by model name on the body's own
  site rather than trusting a model title that says "approved".
- Rank by independent verification evidence, then recommend ONE pick
  with the runner-up named. A maker reporting a measured result (weighed
  grams, a side-by-side flight or function comparison, print photos)
  outranks a cleaner render; a title-block claim outranks nothing.
- Weigh maturity honestly: repo/model age, author history, whether the
  author has actually built the thing. A month-old generator with sound
  numbers is a good tool and an unproven product, and both facts belong
  in the same paragraph as the recommendation.
- Distinguish "cannot be edited" from "should not be edited". A design
  whose geometry must be untouched to keep a claim is still printable,
  but say which parameters are free (slicer walls, infill) and which are
  load-bearing.
- For soft materials, remember the material moves the flight/function
  more than the dials do: TPU is less stiff than production plastic and
  behaves more understable, and mass distribution (rim versus plate,
  walls versus infill) dominates behaviour at a fixed total weight. Tell
  the principal to calibrate the generator's mass factor by weighing one
  print rather than trusting the estimate.

Domain depth for disc golf discs, including the free generators, their
verification status, flight numbers and TPU print settings:
`references/disc-golf.md`.

## Booleans against IMPORTED STL meshes

`import("file.stl")` is a first-class solid: it passes straight into
`difference()`/`union()`/`intersection()` and exports consolidated with
the parametric geometry. Recipe: wrap the import in `scale([...])` for
sizing, cut/union in one script, export one binary STL. Gates differ
from template work - do not reuse template gates here:

- The output FACET COUNT never equals the sum of the inputs: the
  boolean engine re-tessellates the whole solid, so facet-count
  identity gates are meaningless here. Prove correctness from Status
  NoError plus the bbox plus the specific removed/added feature (a
  cross-section through the cut, the hole probe), never from counts.
- The DOWNLOADED mesh must be watertight before it can be booleaned:
  a non-manifold download booleans into garbage or silently vanishing
  geometry; the fix is a 30-second repair pass in a slicer/mesh
  fixer, not parameter fiddling.
- Wall-clock scales with MESH SIZE, not with OpenSCAD cleverness:
  prefer a modest-resolution source download and scale down rather
  than decimate. A 50 MB source is minutes of render per edit, so
  measure the real part from a photo with a known-size object beside
  it and compute socket/cradle offsets numerically, keeping trial
  renders few.

## Generation app (Gradio, in-skill)

`app/` is the principal's interactive builder: master `app.py` (port
7863) composes the STL Forge tab (template dropdown, controls parsed
from each template's own parameter block with the file's comments as
text; a 1/3 : 2/3 column split, parameters
plus Reset on the LEFT; on the RIGHT the binary-STL orbit view, a
full-width Download STL button beneath it bound to the latest
render, and an APPENDING session log stream below it: one timestamped
line per render with the full OpenSCAD stderr on failure, seeded with a
boot line, bounded at the last 200 entries; the page H1 is literally
`# ⚒ STL-forge` and the tab label is plain `STL-forge`) and the Geometry
Playground tab (live
star/petal sketch dials rendered face-on through the real OpenSCAD
functions - never re-implement those maths in Python). Run from the
skill root with `app/.venv/bin/python app/app.py`; when that venv\'s
python dies with `dyld ... Library not loaded libpython` (concurrent
dispatches re-break this venv), launch instead with the Hermes venv
python (`~/.hermes/hermes-agent/venv/bin/python app/app.py`, gradio
already installed) and repair the app venv in a quiet moment.
The orbit viewer's only colour knob is `clear_color`; it is set dark
violet `(0.10, 0.02, 0.16)` because the mesh material colour is NOT
exposed by gradio 6.30 and the ground tone is what gives the grey mesh
contrast. Iterate deliverables IN PLACE: while a shape is being designed
in steps, OVERWRITE the same `<name>.stl` in the delivery folder each
step (the principal-ordered overwrite rule) and never name new version
files unbidden.
Standing preferences baked in, and any UI change must keep them: NO
Render button (renders are change-driven; selecting a template
auto-renders its defaults so the view is never empty), a Reset button
below the parameters restoring the template's file defaults, native
Gradio components only (no custom HTML/CSS, no theming), renders ONLY
into gitignored `app/.render-scratch/`. Only literal-valued parameters
become controls: driving a derived one (`height = width / 2`) would
trip the template asserts, so defaults always round-trip. EVERY
declared control carries explicit `interactive=True`: Gradio 6.30
hydrates @gr.render-injected controls as DISABLED when interactivity
is left to defaults (server-side handlers keep working, the front end
locks, and the user sees sliders that read but do not move), so the
explicit flag is the fix at the cause.
For agent
coding in this directory, Gradio's own skill is installed
project-locally via `gradio skills add --opencode` (per
gradio.app/guides/Gradio-skills-for-ai-coding-assistants); follow
`.opencode/skills/gradio/SKILL.md` over training memory, since Gradio
6 has moved several APIs.

## Authoring for humans (MakerWorld-facing)

The template `.scad` files double as deliverables for non-coders
(MakerWorld upload planned): keep the parameter block at the TOP of each
template with unit-bearing inline comments, descriptive parameter names
and no magic numbers in the geometry, and let the project README carry the
plain-language parameter story (what width, roundness and points do to the
shape) - a non-coder must be able to open Customizer and drive the file
unaided. Keep the skill directory SELF-CONTAINED (own templates, presets,
scripts, tests, READMEs; no imports from other skills): the plan is to
extract it into a standalone repo with its own venv, leaving only a
lightweight skill shell behind, so nothing here may reference repo-level
plumbing.

## Extending the family library

A new template or a parameter-rule change ships through one opencode
dispatch (muse lineage) plus your own verification. The generic dispatch
mechanics (staging the brief in the dispatch cwd, fencing, verifying on
disk) live in the `coding-agent-dispatch` skill; what is specific here:

1. Stage the brief inside THIS skill directory and read it back before
dispatching - a brief left in a scratch dir elsewhere is invisible to the
   agent, which will correctly refuse to invent the work. Fence the
   dispatch to the exact files (the template, `presets.json`, `USAGE.md`)
   and have it delete the brief on completion. Completion criterion: the
   agent reports which files it touched. ARM THE DISPATCH AS A TRACKED
   BACKGROUND PROCESS (`terminal(background=true, notify=true)` with the
   output redirected to a scratch log) FROM THE FIRST ATTEMPT when any
   reading or rendering is expected: this session's terminal foreground
   cap kills an in-flight opencode run outright (twice seen: once with all
   work done and salvageable, once empty), and the salvage pass costs more
   than the background wait.
2. Verify on disk, never from the run's self-report: read the changed
   source line by line, then run `python3 forge.py` with NO `--only` flag -
   every shipped preset, old and new families alike, must exit 0.
   Completion criterion: summary table lists all presets, no FAILURES block.
   A dispatch may die on a session-lease failure a moment before its final
   report: exit 0 from the CLI certifies nothing, and a still-present brief
   file is the tell. Read the dispatch's log file directly for the final
   report, then run your own verification anyway - a one-shot killed near
   its end often leaves every edit and scratch artifact on disk, so salvage
   and verify rather than re-dispatching (a duplicate dispatch over an
   already-edited tree is worse than a lost report).
3. Probe dimensions and manifoldness per the Verification section, then
   re-render the affected presets into the designated project folder and
   vision-check the previews before reporting anything.
4. Treat every SKILL/USAGE sentence that describes current behavior as
   part of the change's blast radius: a doc line denying a mechanism
   becomes false the moment the dispatch adds that mechanism. Rewrite such
   lines in the SAME brief, then re-read both docs against the new source
   before committing.
5. The clone is shared with other working sessions: stage only this
   skill's paths, leave sibling strays unstaged, push in the same turn.
   The exception is a file that ALREADY carried another session's uncommitted
   edit when you opened it (`git status --short <path>` showing it dirty before
   you touched it, or its frontmatter `version:` moving under you mid-session):
   committing it would sweep that work into your commit and steal its version
   bump, so leave your edit beside it uncommitted, say plainly in the report
   that the file is shared and unlanded, and let the owning session land both.
   Re-read such a file before patching it - never patch from the copy you read
   before it changed. General mechanics: `sysone-skill-check`.
6. Bump the frontmatter `version:` in the SAME commit as the change,
   before committing - a stale version number on fresh geometry tells the
   mirror and the principal the folder is behind. If the commit lands
   without the bump, amend rather than stacking a bookkeeping commit.

## Pitfalls

- openscad dying with signal 6 and `libc++abi ... filesystem_error: call to getcwd failed` in the RENDER REPORT, or reported by the app's probe, means the PARENT process's working directory is dead (the server or shell that launched it had its dir renamed/removed underneath it), not an OpenSCAD defect. Verify cwd with `lsof -p <pid> | grep cwd` then `ls -d` that path; restart from a verified live path (see the gradio-subapp-composition skill's relaunch rule for the server pattern), and re-run the render before touching any template.
- Two entry points, two flag sets: the ROOT `forge.py` (library suite,
  `--out`/`--only`/`--word`, also called for `.3mf` composition) sits at
  the SKILL ROOT, while the finished project's builder is
  `projects/giant-beads/main.py` (`--save-to`/`--parts`/`--preset`/`--previews`,
  NO `--out`). Never assume the project directory contains forge.py or
  that main.py accepts --out; check the entry point's own help before the
  first run in a session.
- Do NOT judge a delivered STL stale from its mtime: re-render the
  template at the settings the delivery policy implies and `cmp` against
  the delivered file first. The binary writer is deterministic, so byte
  identity proves the file already IS the current recipe; rendering a
  'refresh' over an identical file wastes a turn and muddies the audit
  trail.
- OpenSCAD snapshot builds keep the app binary at
  `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD` and brew links it to
  `/opt/homebrew/bin/openscad`; if `forge.py` reports `openscad` not found
  or a render fails, re-run the version check (Prerequisites) before
  digging elsewhere.
- Measure, don't trust: prove a part's dimensions from the STL vertex
  stream, never from preview proportions or a dispatch's self-report. The
  probe must force `--export-format asciistl` - awk over a binary STL
  silently prints nothing (see Verification for the command). Derived
  parameters count as proven only when overriding the driver moves the
  measured box.
- Rounded corners: `corner_r` close to `depth/2` starts to undercut wall
  interior rounding; keeping corner_r at 5-10 mm for shoebox shapes avoids
  the diagnostics. Avoid pushing corner_r past roughly a third of the
  smallest footprint dimension.
- Binary vs. ASCII STL: this pipeline emits BINARY by design (forge.py
  passes `--export-format=binstl`; direct openscad renders meant for
  delivery must pass it too) - the same facets as ASCII at ~50 bytes
  each, float32, 5-6x smaller, and the switch was proven by facet-count
  and bbox identity against the ASCII baseline before it shipped.
  forge.py counts facets from whichever arrives - binary via the 4-byte
  little-endian count at offset 80, ASCII via 'facet normal' lines. File
  size / 50 vs / ~250 tells you which one you have; awk/vertex probes
  need `--export-format asciistl` forced, or use `core/stl_probe.py`
  (it lives in `core/`, not `scripts/`), which reads both flavours.
- Stacked-offset fillets fail by STEP SIZE, not slice count: ~0.2 mm
  steps show a visible staircase in a cross-section and print as a ledge
  even though the arc formula is correct; <=0.075 mm steps pass a zoomed
  cross-section. Budget slices as `ceil(radius / 0.05)` (cap ~120) and
  prove it by cross-sectioning the exported STL - only the artifact
  exposes the staircase.
- A slab-built union can count differently per RENDER BACKEND: nested
  merely-touching erosion slabs (equal heights, differing insets,
  coplanar faces) surface as dozens of small components under the
  Manifold default backend but as ONE closed shell with the correct
  genus under --backend=cgal. Arbitrate geometry questions with the
  CGAL render (single shell, chi giving the expected genus) before
  blaming the construction, and note an inter-slab overlap (a hair of
  extra extrusion height per slab) as the tidy fix if a slicer ever
  objects to the split - never shrink a fillet radius to chase it.
- Stacked slabs over a many-point 2D outline set the whole file's facet
  budget: offset() roughly doubles the outline points (an arc point per
  vertex) and each slab costs ~4 facets per point, so facets ~ slabs x 4
  x ~2N - N=960 with 240 slab rim = 1.1M facets / 279 MB, N=400 with 120
  slabs = ~480k on a 120 mm part. Choose outline point count and slab
  count together, and read the facet count off the summary table before
  delivery - never discover a bloated mesh at the slicer.
- Modelling a 2D offset in Python for planning: displace vertices by the normal lies at
  cusps - use the distance-transform identity instead
  (round inflation = dilation: interior clearance = distance-to-boundary +
  puff, then the rescale k); an OpenSCAD bbox self-check caught it.
- OpenSCAD dialect traps when porting template math: this build REJECTS
  `max()` over vector elements and has NO `normalize()` (only `norm()` and
  plain vector arithmetic). Write scalar two-pass argmin loops and hand-rolled
  unit vectors instead. The failure mode is silent: OpenSCAD emits warnings
  and returns undef, which then cascades through every derived value so
  geometry silently vanishes (a missing cutter) with zero errors at dispatch.
- Suite `--out` runs must never enter the commit: `.gitignore` covers
  `stl-forge-*/` and `regr*/`, but a suite dir created before that
  ignore (or a `git add -A` run without it) sweeps every binary render
  into history. Check `git show --stat --oneline HEAD` shows only
  source and docs before pushing, and amend out anything that is not.
- Merging diverged template lineages: when one branch restructured the
  layout (renamed/moved templates) while another evolved the templates,
  rename detection auto-merges the evolution into the moved path with no
  conflict - a clean merge proves nothing. Render through the PROJECT
  entry point (not the standalone template) and measure a discriminating
  geometric unit (a fillet change moves a rim radius by exactly
  2*(old-new) mm) to prove the newer geometry landed; and sync the
  destination docs' parameter tables against the merged source in the
  same commit, since restructured docs routinely still describe the
  lost geometry.

## Verification

Run this in a `terminal` call from the skill directory; exit 0 and a
table listing every shipped preset means the skill is live:

```bash
python3 forge.py --out <scratch-dir>/stl-check
```

A NEW template must additionally render STANDALONE: `openscad -o
/tmp/x.stl templates/<new>.scad` with no `-D` flags exits 0. Template
defaults are the always-valid configuration - presets override them, they
never rescue them; a template that only renders under preset flags ships
   wrong defaults.

After any pipeline or template change, run the fresh suite into scratch and
facet-count-compare every STL against the previous baseline suite (scratch
`stl-forge-regr*` dirs): an empty diff is the proof that untouched families
survived a change made elsewhere. Count binary STLs via the 4-byte count at
offset 80 and ASCII via `facet normal` lines, and compare only names present
in both directories.

For a pure REFACTOR of template code (no intended geometry change), the
strongest gate is BYTE IDENTITY, not facet counts: render each affected
template with `--export-format=binstl` at defaults BEFORE the edit into
a scratch baseline dir, re-render after, and `cmp` the pairs - the
OpenSCAD binary writer is deterministic, so byte-identical output proves
the refactor moved nothing geometry-wise (facet counts alone can hide
vertex-order drift). If the writer is ever non-reproducible, fall back
to sorted ASCII vertex streams.

Then confirm in `<scratch-dir>/previews/` that each preset has five PNGs
(iso, front, top, bottom, hole) and a nonzero facet count in the summary
table. Camera semantics: iso = three-quarter, front = side profile, top =
top face, bottom = underside, hole = straight down the bore. If two
different cameras produce near-identical PNG byte sizes, the camera table
or the labels are wrong - re-render both views and compare before trusting
any label. Sizes follow facet count and differ per family: box presets land
around 25-50 KB, bead-class body/assembly parts in the 10-25 MB range -
compare only within a family, never against a fixed number.
A through-hole is provable without a slicer: the render report's
`Genus` counts tunnels, so a subtractive bore through a simply connected
part must report Genus 1 (Genus 0 with a hole expected, or Genus 1
unexpectedly, both mean the difference() is wrong). Read Genus against the
SAME TEMPLATE'S prior render, never against a formal absolute: bodies built
from slabbed extrusions (erosion-slice fillets) can report a NEGATIVE Genus
with Status NoError and a truly manifold surface - that is a baseline
property of the construction lineage, not a defect. Correctness gates are
NoError + manifold; Genus answers only 'did the tunnel count change'. Pair it with the
outer-bbox invariance and a bore-clear probe: among vertices within 0.02
of the z=height/2 plane and inside the bore span, min abs(y) must equal
the throat radius exactly, and at the last hair before the flank the
flare must read exactly the opening radius.
Judge a hole's presence from the TOP/elevation previews, never the
front: a hole running left to right opens on the part's flank edges, so
a straight-on front view shows unbroken solid walls - absence there is
correct geometry, not a missing bore.

Dimensional probe (forces ASCII so awk can read vertices):

```bash
openscad --export-format asciistl -o <scratch>/probe.stl \
  templates/bead.scad -D 'width=100'
awk '/vertex/{for(i=2;i<=4;i++){if(!n||$i<m[i])m[i]=$i;if(!n||$i>M[i])M[i]=$i}n++} \
  END{printf "x %s..%s y %s..%s z %s..%s\n",m[2],M[2],m[3],M[3],m[4],M[4]}' \
  <scratch>/probe.stl
```

A derivation rule is only proven when the override moves the box (width 100
-> z 0..50 for `height = width/2`); at defaults expect the nominal bbox
plus manifold `Status: NoError` from the probe in `references/alt-cad-routes.md`.
Prove internal geometry from the ARTIFACT, not the source model: cut a
true cross-section of the exported STL -
`intersection() { import("<out>/<name>.stl"); translate([-70,-2,-5]) cube([140,4,70]); }`
rendered square-on (`--camera 0,0,0,90,0,0,350 --autocenter --viewall`) -
because well flares, groove depth, and insert seating exist in the file
that prints, not necessarily in what the source model suggests;
re-importing the delivered file itself and rendering that closes the loop
end-to-end.

Slicing an exported STL at a plane is the preferred internal probe, but
tessellation puts whole vertex RINGS exactly on the symmetry planes of
revolved geometry, and a strict sign-change crossing test on such a plane
finds nothing - reporting an internal feature ABSENT when it is there.
Nudge the slice plane a hair off the suspect height (+-0.01 mm), and when
a null result would matter, corroborate with a `projection(cut=true)`
render plus a raw-vertex scan before believing a feature is missing:
absence claims from a single slicing method are the one measurement
allowed no trust. `core/stl_probe.py <stl> [--slice-z Z]` prints
format, facet count and bbox for either STL flavour and does the
off-plane nudge itself - prefer it over the awk recipe for binary files.

Gate tolerances must clear the STORAGE floor. Binary STL stores float32, so a
vertex nominally on a circle of radius r can sit up to half an ulp away:
1.9e-6 at r=60, growing with r. A containment or contact gate written at 1e-6
against a real-valued outline FAILS on quantisation and reads exactly like a
geometry defect. Either set the bound from the ulp (`2^ceil(log2(r)) * 2^-23
/ 2`) or measure the excess and check it against that bound rather than
against zero.

Gate premises must match the shape's ACTUAL symmetry. An n-fold rotational
outline with one feature oriented up has x-span == y-span only when n is even:
an 8-point star is exactly square in its bbox, a 5-point star is not. Derive
the expectation from the symmetry group the parameters really produce, or
record the measured value as the reference instead of inventing a relation.
When a dispatch rejects one of YOUR gates, adjudicate the objection by
re-measuring yourself before accepting it - a gate written from intuition
about a shape is a hypothesis, not a specification.

For the delivery overlay run
`scripts/annotate_preview.py <preview.png> <out.png> <circle-diameter-mm>`:
it draws the spec circle, centre cross and letter bbox, prints the margin,
corner-in-circle and max-ink-radius measurements, and exits nonzero when the
letter is missing, its ink leaves the circle, or its bbox corner lands
outside the circle (bbox corner inside-or-touching, 0.05 mm allowance) -
ship its output to the project folder. For a scale-exact gate measurement,
render the preview with --projection=ortho --autocenter --viewall: the
tool calibrates px/mm from the mid-row silhouette edge, and a perspective
camera magnifies near-camera features (~4.5% for a bead's top face at the
standard distance) enough to flip a passing bbox corner to OUTSIDE. Use
the ORTHO TOP view (camera z-elevation, 55 deg iso tilts the fit circle
into an ellipse and poisons both gates), render the ASSEMBLY (a bare STL
raster has no pink ink to gate), and pass the LETTER-FIT circle diameter
(width * letter_space, 90 mm at width 120) - the bead's outer width is
not the circle the letter was fitted to, and passing it fails a true
corner-in-circle verdict by ~16 mm.

Vision-check hygiene: ask for an OPEN description FIRST and put no
expected dimensions or expected features in the question - a vision model
echoes whatever the question asserts, so a loaded question confirms the
assumption instead of the geometry. Judge the well's funnel flare only in
high-contrast previews (assembly paints the recess floor HotPink against a
white body): a black floor absorbs the shading that reveals the blend, and
STL carries no colour, so preview colours are inspection tooling alone.
When two vision reads of the same image disagree (faint grooves, subtle
fillets, comparison strips), stop re-asking - settle it with a numeric
probe of the PNG itself (ink-mask band widths, per-cell bbox) and let the
numbers decide. Comparison ladders are viewall-framed per cell, so they
evidence SHAPE differences only; any size claim needs a measurement.
For choosing between geometry variants, pose a COMPARATIVE question on
a stitched ref-vs-variants strip ('which right-hand variant matches the
left reference'): comparative reads stayed stable where descriptive
reads of the same silhouette flip-flopped, and the pixel metrics go
beside the verdict.

Verifying a MULTI-BODY merged file (a word/name STL of several beads):
an ISO or three-quarter render foreshortens a row of bodies along the
view axis, so correctly-gapped beads read as overlapped or touching in
the iso view. Never take a spacing or overlap claim from the iso - take
it from the straight-on FRONT render plus a numeric per-shell bbox probe
of the vertex stream. Assign each facet to the NEAREST expected body
centre (min |x - centre|), NOT to a fixed-width coordinate bucket: a
bucket boundary that lands inside a body splits it across two buckets and
manufactures a phantom negative gap between bodies that are in fact
cleanly separated - a false alarm that looks exactly like a real defect.
Word mode self-asserts its own gates (its `[word] assert` lines cover the
exact facet sum, size == 84 + 50n, symmetric x-span, and z-base 0); read
those lines rather than re-deriving the arithmetic.

Full loop closes with a real slicer import or a print.

Provenance probe for a delivered STL whose render parameters are unknown or
doubted (the principal asks 'what fillet/depth does THIS file have', or
gives a value you suspect is wrong): render the SAME template freshly at
two candidate parameter values and compare facet counts against the
delivered file - identical parameters produce an identical facet count
deterministically, so one exact match identifies the whole parameter set
at once. Corroborate a suspected parameter change by measuring a geometric
unit it moves (e.g. a rim-fillet change shifts a top-face rim radius by
exactly 2*(old - new) mm); a measured delta matching the predicted value
proves the change landed in the geometry, not just in the arguments.
Never answer from the template's CURRENT values or accept the principal's
belief about a delivered file's parameters - the file records what was
rendered when it was rendered, and template defaults drift between render
time and the question.
