---
title: bead_flower.scad step 3 — salvage-completed
date: 2026-10-22
tags: [bead, flower, giant-beads, openscad]
---

# FINDINGS: bead flower step 3 (salvage-completed)

Run note: the dispatch completed its template edits and its verification
sweep through the dial matrix, then its session died after the sweep and
before it wrote this file, committed, or refreshed the deliverable. Executed
by the implementer up to 15:47 (log at
`~/.hermes/profiles/araminta/cache/scratch/bead-flower-step3-dispatch.log`,
evidence dir `regr-flower-step3/`); FINDINGS, commit, deliverable and merge
completed by the orchestrator. Executor-run rows are labelled; the
orchestrator re-measured the headline rows.

## What was built (EXECUTOR)

`templates/bead_flower.scad` on `feat/bead-flower-step3`:

- `fillet_radius = width / 6` (20 mm at 120: the petal fillet doubling,
  principal-ordered 22 Oct 2026, flower-only; family default stays
  width / 12 in bead.scad / bead_heart.scad / bead_star.scad).
- New `stigma_fillet_radius = width / 12` (10 mm), decoupled parameter,
  asserts `<= width_stigma / 2` and `<= height / 2`.
- Erosion-slab construction, n_fillet = 32, applied to petals BEFORE the
  union and now to the stigma disc too; union order unchanged;
  `hole_entry_x` still computed from the union outline.

## Measured gates

| gate | result | who |
|---|---|---|
| template asserts / renders at defaults | exit 0 | EXECUTOR |
| defaults (Manifold backend, binstl) | 176,158 facets, 8,807,984 bytes, bbox 109.074 x 120.0 x 60.0 exactly | MEASURED by orchestrator (fresh re-render, flower3-verify) |
| defaults (CGAL backend) | 174,224 facets, single shell, every edge 2 facets, chi = 0 -> Genus 1, bbox identical | EXECUTOR |
| petals-only solid (CGAL) | facets 147,068, all edges 2, chi = 2 (closed, genus 0), z 0.861..59.139 | EXECUTOR |
| Manifold-backend comps on defaults | 53 shells (171,410 + 6x716 + 32) vs CGAL's 1: engine artefact on nested-touching slabs, geometry itself proven single-shell by CGAL + genus 1 | EXECUTOR, flagged for a later slab-overlap fix if the slicer import ever objects |
| stigma rim: z of the top edge at the r=20 wall | 50.000000 (= 60 - 10, fillet present and tangent) | EXECUTOR |
| hole gate | min abs(y) at midplane = 10.000000000 exactly (throat 20/2) | EXECUTOR |
| hole mouth crossing at defaults | union outline crossing y=0 at x=20 (stigma wall, normal [1,0]); star valley crosses at 14.28, inside the stigma: disc stands proud, union bonded | EXECUTOR |
| dial sweep pd{1,10} x r{1,12} | all 4 rendered, exit 0; pd=1 configs report 2 components: at that extreme the petal wall (52.8 at y=0) lies entirely outside the stigma (radius 20): petals detached from disc at pd=1 is that dial's real geometry, not a defect | EXECUTOR + orchestrator read-back |
| regression | 34 passed | EXECUTOR |
| dash scan | 0 | EXECUTOR |

## Deliverable

Refreshed by the ORCHESTRATOR: defaults render from the salvaged tree
overwrote `/Users/djmcnay/Downloads/beads-camilla-v1/bead_flower.stl` in
place (this FINDINGS completes after the overwrite; compare the file's
size to the 8,807,984 defaults row). The folder gained nothing else.

## Deviations

- The dispatch died before its final sweep-summary, findings, commit and
  deliverable refresh; all four completed by the orchestrator from the
  executor's own on-disk measurements plus fresh re-renders.
- The 53-vs-1 shell split between render backends is recorded as an open
  engineering note, not fixed: the next slab-stacking change (a small
  inter-slab overlap) would likely resolve it. Nothing was silently
  tuned.
