---
title: bead_flower.scad step 4 — consolidated petal fillet, stigma
date: 2026-10-22
tags: [bead, flower, giant-pony-beads, openscad]
---

# FINDINGS: bead flower step 4 (consolidated: petal fillet 3x, stigma width/2.2, normal stigma fillet)

Executed per `BRIEF_bead_flower_step4.md` on `feat/bead-flower-step4`
(cut from main at 7d628d9, whose tip merge message names step 3, the
required precondition). Evidence dir `regr-flower-step4/` (untracked by the
regr* rule). One template touched: `templates/bead_flower.scad`. No other
template, no main.py or presets.json, no .3mf, nothing added to the
delivery folder except the overwrite of `bead_flower.stl` in place.

## What was built

- `fillet_radius = width / 4` (30 mm at the 120 default): the petal fillet
  tripled. History in the comments: 2x (width / 6) at step 3, 3x
  (width / 4) at step 4, both principal-ordered 22 Oct 2026; the family
  default stays width / 12 in bead.scad / bead_heart.scad / bead_star.scad
  (untouched). Literal-derived parameter, as ordered.
- `n_fillet` KEPT at 32: petal slab z-step = 30 / 32 = 0.9375 mm,
  stigma z-step = 10 / 32 = 0.3125 mm (nothing silently changed).
- `width_stigma = width / 2.2` (54.545 mm at width 120, radius 27.2727;
  the step-3 width / 3 and the superseded width / 2.5 both replaced).
  `stigma_fillet_radius` STAYS `width / 12` (10 mm): the ordinary family
  fillet on the stigma top, no dome construction; the flat top face left
  is radius 54.545 / 2 - 10 = 17.27 mm.
- Assert domain check measured: 10 <= 27.2727 (stigma fillet <= wall),
  10 <= 30 (stigma fillet <= height/2), both hold; petal fillet 30 <=
  height / 2 exactly (the equality case renders, see below).
- Union and hole recomputed exactly as step 3 built them: petals
  eroded-slab filleted first, stigma filleted, union, shared v2 mouth from
  the union outline at y=0 (echo line unchanged: flower_hole_entry_x =
  27.2727, flower_cross_star = 14.28, flower_cross_stigma = 27.2727,
  flower_wall_normal = [1, 0], flower_hole_len = 54.574).

## Measured gates

| gate | result |
|---|---|
| template asserts / defaults render | exit 0, `Status: NoError` (OpenSCAD 2026.10.11, Manifold backend) |
| baseline difference | step-3 baseline 176,158 facets / 8,807,984 bytes; post-edit 137,512 facets / 6,875,684 bytes: differs, ordered trim only |
| defaults bbox (Manifold binstl) | x span 109.001404, y span 119.927726, z span 60.000000 exactly (z 0..60) |
| defaults comps (Manifold) | 4 shells: 128,298 (z 0..56.34) + 6,140 (z 58.31..60) + 3,068 (z 56.34..58.31) + a 6-facet fragment at z 50.98; the step-3 nested-touching-slab engine artefact family |
| CGAL arbiter on defaults | 136,592 facets, 6,829,684 bytes, comps = 1 (single shell), V 68,296 / E 204,888 with 0 unpaired edges (closed manifold), chi = 0 -> genus 1 (the string hole), `Simple: yes`: geometry sound, the Manifold split is an engine artefact; reported, radius untouched |
| z-step / silhouette | petal fillet 30 = height / 2 exactly: side band collapses, the two fillet bands abut at z = 30 and the petals are fully half-round in silhouette (petals-only render spans z 5.056..54.944) |
| hole gate (bounds |x| < 30) | min abs(y) in the z band [29.98, 30.02] = 10.000000000 exactly (throat 20 / 2), measured on both backends (4 band vertices each) |
| stigma wall rim | ring r = 27.2727 (tol 0.002): 440 vertices, max z = 50.000000 = 60 - 10: the ordinary top fillet present and tangent at the wall |
| petal wall at the y=0 valley | consumed, as the brief allows: the only union surface near the valley crossing (band |x| 13..16, |y| < 0.5) is the countersink sphere (60 vertices, distance to the scoop center 15.8068..15.8114, z 15.545..44.455): the petal wall no longer reaches the valley; the transit proves the union bonded, and the CGAL comps = 1 ruling makes it one solid |
| dial sweep pd{1,10} x r{1,12} | all 4 exit 0, NoError: pd1/r1 22,004 facets (comps 1); pd1/r12 242,082 (comps 1); pd10/r1 56,944 (Manifold comps 5, CGAL 58,256 comps 1 but chi -24 -> genus 13: thin inter-slab handles at the skinny-petal extreme, `Simple: yes`, single volume; engineering note, nothing tuned); pd10/r12 108,700 (Manifold comps 11, CGAL 108,608 comps 1, chi 0 -> genus 1, sound) |
| regression | `PYTHONPATH= python3 -m pytest tests/ -q`: 34 passed |
| dash scan | 0 (python scan of the touched template and this findings file: U+2014 / U+2013 absent) |
| deliverable overwrite | `/Users/djmcnay/Downloads/beads-camilla-v1/bead_flower.stl` overwritten in place from the defaults render; byte-identical to the verified `post_binstl.stl` (137,512 facets, 6,875,684 bytes); folder gained nothing else (pre-overwrite snapshot kept in profile scratch) |

## Deviations / notes

- The brief's two 24 mm figures ("wall axis at |x| ~ 24", "the 48mm
  stigma") are the superseded width / 2.5 geometry; the governing width /
  2.2 correction in the same brief puts the wall at 27.2727 and the
  findings row quotes the executed value.
- The pd10/r1 genus 13 is the one flaw measured anywhere in this step, and
  it is outside the defaults at a skinny-petal dial extreme: single volume
  and `Simple: yes` still hold, facet count 58,256 CGAL, exit 0, NoError,
  no assert fired, no vanish. Left for a later slab-overlap fix like the
  step-3 note; nothing was silently tuned.
- Method note for whoever re-measures: binary STL records are 12 floats
  (normal + 3 vertices) + 2 attribute bytes; reading the 12-float record
  as vertices promotes the normal into the vertex set and manufactures a
  phantom unit hemisphere at z = -1 (28k bottom faces carry normal exactly
  [0, 0, -1]). All numbers above come from the corrected 9-float vertex
  reader in `regr-flower-step4/analyze.py` and the shipped
  `core/stl_probe.py`.
