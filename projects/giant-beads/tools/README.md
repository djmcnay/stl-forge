# giant-beads tools — the trace → bead pipeline

One path, repeated per elevation. The rear is done; the side and the front are
the same walk with a new view module.

```
photo ──▶ traced overlay ──▶ part map ──▶ (principal signs off) ──▶ bead sketch ──▶ bead-sketch.json ──▶ SCAD
             pink ink        recoloured ink      the spec              one stroke per feature      the build input
```

## The rule that governs everything

**The principal's trace is the geometry. Nothing here redraws it.**

The first attempt at this pipeline hand-measured the trace and drew a
replacement outline. It was rejected outright ("completely different shapes …
zero creative licence"), and rightly: a redraw is an approximation dressed up as
a decision. So the engines work in two modes only:

* **recolour** — decide which part each *existing* pink pixel belongs to and
  repaint it (`part_map.py`);
* **derive** — take the silhouette out of the ink by closing, filling and
  re-contouring it, so the profile is the traced pixels themselves
  (`bead_sketch.py`).

Never add a stroke, never smooth a line away, never "improve" a curve. The only
changes to the ink are the ones the principal asked for, and they are declared
as data in the view module (`REMOVE_*`, `ADDED`) and printed on every sheet, so
they can be checked against the trace at a glance.

## The artifacts

All of them land in `references/<view>/` (here `references/defender/`).

| file | what it is | role |
|---|---|---|
| `rear-trace-overlay.png` | the principal's pink ink over the photo | **source of truth** |
| `rear-parts-by-colour.png` | that ink, recoloured by part | decision record — the sign-off sheet |
| `rear-parts.json` | per-part ink loops (closed, even-odd) | ink-exact reference, **not** a build input |
| `rear-bead-sketch.png` | clean base: one stroke per feature | what gets built |
| `rear-bead-sketch-overlay.png` | the same lines over the photo | how you check it still looks like a Defender |
| `rear-bead-sketch.json` | silhouette polygon + parts + levels | **the build input the SCAD reads** |

The two JSONs are deliberately different things. `rear-parts.json` is the ink as
drawn, doubling and all; `rear-bead-sketch.json` is the resolved geometry. When
they disagree, the sketch wins — it is the later decision.

## Levels, not colours

Colours mean *how high a thing stands*, never *which thing it is*, so two parts
cut at the same height share a colour. The vocabulary lives in `levels.py` and
both sheets read it from there:

| level | meaning |
|---|---|
| `silhouette` | the bead profile |
| `etch` | engraved, one depth, both faces |
| `lights` | raised domes |
| `raised_tyre` | spare tyre, its own height |
| `raised_wheel` | steel wheel, its own height |
| `raised_seam` | waist capping seam, its own height |
| `delete` | proposed removal (grey, dashed) |
| `omit` | agreed omission, wasted at bead size (grey, dashed) |

## Running it

From anywhere; paths resolve from `__file__`.

```bash
python3 projects/giant-beads/tools/part_map.py            # part map + parts.json
python3 projects/giant-beads/tools/part_map.py --check -v # per-part pixel counts, no render
python3 projects/giant-beads/tools/bead_sketch.py         # sketch + photo overlay + build json
python3 projects/giant-beads/tools/bead_sketch.py --check # fit of sketch to trace ink, no render
python3 -m pytest projects/giant-beads/tests/test_views.py -q
```

`part_map.py` prints what it did to the ink — pixels kept, removed by request,
added by request — and refuses to finish if a removal does not match the size it
expects. `bead_sketch.py` prints the distance from the sketch to the trace ink;
on the rear that is 2.7 px mean (0.25 mm on a 120 mm bead).

## Adding a view (side, front)

1. **Trace it.** Generate/trace the elevation onto the photo and save the pink
   overlay as `references/defender/<view>-trace-overlay.png`. Check the frame
   first: if the overlay is the photo at 2× with no offset, sketch coordinates
   land on the photo with no fitting (that is how the rear was built — see
   `overlay_trace.py` for the chamfer fit when it does not).
2. **Copy the shape of `views/rear.py`** to `views/<view>.py`. Fill in the
   frame (`OVERLAY`, `PHOTO`, `STEM`, `ART_W/H`, `PHOTO_H`, `CX`,
   `BEAD_WIDTH_MM`, `BODY_LEFT/RIGHT`), the probe outline (`BODY_EDGE`,
   `BODY_SIDE`), `FLARE_WEDGES`, the ink edits, `PARTS` and `build_parts()`.
3. **Measure the ink, do not guess.** Read positions off the trace: run the
   pixel queries you need on the pink mask, take radii by ray-casting rather
   than fitting bounding boxes, and probe each stroke separately — most panel
   edges are drawn twice and the two lines are 1–1.5 mm apart on the bead.
4. **Run `--check -v` and read the orphans.** Ink further than ~14 px from any
   probe means a part is missing or mis-positioned. `no ink claimed by:` names
   parts whose probes never landed on a stroke.
5. **Diff the sheets against the trace** by eye before showing anyone: open
   `*-parts-by-colour.png` next to the overlay. If a stroke changed colour
   across its length, the probes are competing and a `bias` needs adjusting.
6. **Add the view to the tests** by doing nothing — `test_views.py`
   parametrises over `viewdata.available()` and will pick it up. It checks the
   contract, that every role is a known level, and that the silhouette closes.

`views/__init__.py` explains the package; `viewdata.REQUIRED` is the exact
contract, and a view missing a key fails on load with the key named.

## What still lives in the engines

Only mechanism: the `Canvas` rasteriser, the probe/distance assignment, the
contour extraction and simplification, the sheet layout. If you find yourself
typing a coordinate, a radius or a filename into `part_map.py` or
`bead_sketch.py`, it belongs in `views/<view>.py` — `test_views.py` fails the
build if a data block reappears in an engine.

## Other tools in this folder

* `trace_sketch.py` — bitmap → 1-bit PNG + even-odd SVG (pixel-crack contours,
  Douglas-Peucker). Used for the Fusion 360 route and reused by the engines for
  contour extraction.
* `overlay_trace.py` — chamfer-fit a sketch onto its photo and report the
  alignment error. CPU only, reproducible.
* `stl_volume.py` — signed volume of a binary STL (`python3 stl_volume.py x.stl`).
* `levels.py` — the level vocabulary.
* `viewdata.py` — view loader, contract check, output paths.
* `views/` — one module per elevation.
