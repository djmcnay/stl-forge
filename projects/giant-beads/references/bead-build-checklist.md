---
title: "Bead from a traced view — checklist and error catalogue"
date: 2026-11-13
tags: [bead, defender, pipeline, checklist, mistakes]
---

# Bead from a traced view — checklist and error catalogue

Written after the rear bead took six review rounds. Every round was a fault that
a measurement would have caught before the file was handed over, and four of the
six were the *same* fault wearing different clothes. The front and the profile
are built the same way, so this is the order to work in and the list to check
against. It is generalised on purpose: nothing here is specific to the rear
view.

Companion tool: `tools/stl_check.py` — shells, degenerate facets and horizontal
faces by height. Run it on every hand-over file.

---

## The contract (breaking these is what cost the rounds)

1. **The principal's trace is the geometry.** The generator may only *derive* —
   clean the wobble, rescale to the family width, offset. Anything that changes
   the drawn outline needs an explicit instruction, must be confined to the part
   named, must be reported on every run, and must be pinned by a test that
   compares the result back to the trace. The semicircular wheel tips were this
   mistake: the trace already had the right bottom, and reworking it made the
   wheel read as a mud flap.
2. **The bead is a squashed 3D model of the car.** Every part is a 3D form
   squashed into the face, not a decoration: lamps are domes, the spare tyre a
   squashed torus, the steel wheel a disc, the seams ridges, the road wheels
   tyres. When a part looks wrong, ask what solid it represents and where that
   solid's surface goes.
3. **The bottom is the build plate.** Flat, etches only, no relief, nothing
   protruding, nothing cut below z = 0.
4. **Nothing on the visible model has a hard edge**, except the plate face and
   the intentional shut lines. Family edge fillet on the face; recessed rims get
   a quarter round; the rope hole gets the family's fillet well.
5. **Family parameters scale.** Anything that should follow the family is a
   fraction of `width` or `height`. A literal in millimetres is a bug waiting to
   be found twice.
6. **The hand-over file is the only evidence that counts.** Not a render of the
   template, not a build with different `-D` values.

---

## Order of work

0. **Approve the trace and the part map first** — the silhouette plus one level
   per part (`silhouette` / `etch` / `raised` / recessed), and the heights as
   fractions. Do not start cutting metal before this is agreed.
1. **Data.** Frame (mm per px), silhouette clean-up, span normalised to the
   family width. Report how far the clean-up moved the outline.
2. **Levels.** One etch depth on both faces. Raised heights as fractions of
   `height`. Every recess depth named.
3. **Build-plate etch.** Mirrored, and masked by whatever covers it on the face.
4. **Raised detail.** Pad = prism + top roundover + a *small* foot fillet.
5. **Recessed and round forms.** Built from inward offsets of the part's own
   footprint, sampled by angle.
6. **Edges.** Recess rims and the bore.
7. **Measure** (below). Then and only then hand it over.
8. **Deliver** to the designated folder with renders from at least three angles
   plus a cross-section, and record facets and md5.

---

## Error catalogue

Symptom → cause → the check that catches it.

| # | Symptom the principal sees | Cause | Check |
|---|---------------------------|-------|-------|
| 1 | A ledge or shelf running along a recessed part | The relief was built from an independent ellipsoid or cylinder which dips *inside* the footprint, so the recess floor is left exposed beside it as a horizontal face | `stl_check.py --band <recess z>±0.1`: any horizontal face at that height whose distance to the part's footprint boundary is ~0 is the shelf. It sat at 0.00 mm for four versions |
| 2 | A saucer / flat disc round a raised part | The foot fillet is comparable to the feature's own radius — 1 mm round a 2.5 mm lamp spreads it to 3.5 mm, 40% of its radius | Radial height profile of the pad: expect it to reach the face plane ~0.2 mm outside the pad's radius. Family figure is 0.2 mm, and the letter beads were dialled from 2.0 to 0.2 for this exact reason |
| 3 | A conical skirt standing off the face | The blend arc is inscribed the wrong way up, so it is widest at the top instead of on the face | Evaluate the blend at both ends: value at h = 0 must be the full reach, value at h = max must be 0 |
| 4 | A thin fin or sliver along an outer wall | Subtracting a prism whose wall is *coincident* with the body's own wall | Offset the cut outward ~0.25 mm so no two walls are coplanar |
| 5 | A knife edge / razor line | A round surface tangent to a wall, or two surfaces tangent along a line | Oversize or undersize the cut by 0.05–0.3 mm so it lands on a steep surface, not a tangent one |
| 6 | Terraces / banding / moiré | Stacked slices too coarse, worst where the surface is nearly vertical | Sample by *angle*, not by distance, so slices stay thin where the curve is steep. Then report the largest remaining flat face |
| 7 | A 10 µm ring or hairline groove | An epsilon in an offset ring bigger than the smallest feature | Keep epsilons ≤ 0.001 mm; check the shell count after changing one |
| 8 | "Something floating" | Any of 1, 4, 5, 7 accumulated into a detached shell | `stl_check.py`: shells must be 1 |
| 9 | The bottom shows things that cannot be seen from the bottom | The plate etch repeated the face etch without masking what covers it | Mask the plate etch with the raised part's own footprint — the spare wheel hides the door and the window behind it |
| 10 | Sharp rims on the rope hole | A plain bore where the family has an approved mouth | Check `templates/bead_common.scad` *before* inventing anything; `bead_string_hole_well()` is shared by the family |
| 11 | A parameter that does not take effect | A literal in millimetres instead of a fraction of `height`, or a stale `param-defaults.json` | Grep the project for the literal after every default change; the snapshot ships in the same commit |
| 12 | The delivered file does not match the pictures | `forge.py` turns **every** preset key into `-D`, which overrides the template's own value | Keep preset keys to the family parameters only. Then render and measure the hand-over file, not the template |
| 13 | "You haven't changed anything" | The last hand-over was never re-checked, so a fault survived a round of fixes | Record facets and md5 per hand-over; measure before claiming a fix |

---

## Measurement protocol

Run `python3 projects/giant-beads/tools/stl_check.py <file> --band a:b ...`.

- **Shells must be 1.** Anything else is a floating piece.
- **Horizontal faces by height.** A flat face at a recess height near a part's
  boundary is a shelf; a flat face far inside is usually the part's own face.
- **Pad profile.** Height against distance from the pad's centre: monotone, and
  reaching the face ~0.2 mm outside the pad's radius.
- **Recessed forms.** Cut the solid with a slab through the part and look at the
  section — that is the only view that shows a profile honestly.
- **Renders are not proof.** Flat shading hides a flat face at a grazing angle
  and exaggerates a shallow one. Use renders to *communicate*, measurements to
  *decide*.

Known and harmless: OpenSCAD emits a few thousand zero-area facets (revolve
axes, offset joints). They are reported but a slicer drops them.

---

## Before starting a new view, answer these

Ask if the answer is not already in the sketch or the part map — each of these
cost at least one round on the rear.

1. **Which plane is "the profile" for this view?** The rear had three candidate
   planes and five rounds went on arguing about it.
2. **What is raised, what is etched, what is recessed, and by how much?**
3. **What is hidden behind what?** On the rear the spare hides the door and the
   window; on the front the spare may hide the grille or the plate; on the
   profile the wheels hide the sill.
4. **Which parts touch the silhouette?** Anything that reaches the bead's outer
   wall cannot carry a step, or it becomes a notch in the side of the bead.
5. **What must stay flat for the plate?**
6. **Which edges are intentionally sharp?** Shut lines, yes; everything else no.

---

## The one-line version

Measure the delivered file; never claim a fix from a picture.
