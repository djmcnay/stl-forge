---
title: bead_flower.scad step 2 — petal fillets before union
date: 2026-10-22
tags: [bead, flower, giant-beads, openscad]
---

# FINDINGS: bead_flower.scad step 2 (petal fillets before union, stigma width/3)

Branch: `feat/bead-flower-step2` (cut from the current checkout at main
`e709143`; never merged, never pushed). Working directory:
`/Users/djmcnay/GitHub/araminta-skills/skills/stl-forge/projects/giant-beads`.

## Files touched

| Commit | File |
|---|---|
| 9fb6ae4 | `templates/bead_flower.scad` |
| (second commit) | `FINDINGS_bead_flower_step2.md` (this file) |

Only those paths were staged/committed (explicit-path `git add`; the dirty
files from other sessions and the untracked brief were left unstaged and
untouched). No changes at all to `bead.scad` / `bead_heart.scad` /
`bead_star.scad` / `bead_common.scad` / `main.py` / `presets.json`. No
`.3mf`. `bead_star.scad` is still reused UNMODIFIED via `use`; the only new
parameter is the family's `fillet_radius = width / 12` (plus its two
bead_star-style asserts). Scratch renders live in `regr-flower-step2/`
(gitignored via `regr*/`), left untracked, never staged.

## Construction (two sentences)

`width_stigma` moved to `width / 3` (40 mm at 120, asserts kept in the
same positive / `< width` style) and `petal_body()` was rebuilt as the
erosion-slab stack over the star outline, mirroring `bead_star.scad`'s
current construction exactly (same `fillet_radius = width / 12` = 10 mm,
`n_fillet = 32` arc tables `fillet_u`/`fillet_z`, bottom fillet slabs with
per-slab `offset(r = -fillet_u[i])` inscribed chords, straight mid band
guarded by `side_len > 0.001`, mirrored top slabs; `offset(r=-u)` erosion
stays the inset primitive for the tip cusps). `flower_body()` then unions
that whole filleted petal solid with the plain, UN-filleted stigma
cylinder (sharp rim where its face meets its wall) and the shared v2
string hole is subtracted as before, with `hole_entry_x` / `n_out`
recomputed from the unfilleted union OUTLINE at y = 0 by the same
outermost-of-two interpolated crossing scan (now `cross_star = 14.28`,
`cross_circ = 20`).

## Gate rows (measured numbers)

Baseline (pre-edit) default render of the step-1 template, rendered fresh
on this branch: 30,794 facets / 1,539,784 bytes, Status NoError, Genus 1;
`cmp` against `/Users/djmcnay/Downloads/beads-camilla-v1/bead_flower.stl`
was byte-IDENTICAL before the overwrite (the delivered file was still the
step-1 recipe).

| Gate | Measured | Verdict |
|---|---|---|
| 1. Post-edit defaults MUST differ from baseline | exit 0, Status NoError, Genus 1, Vertices 96264, Facets 192528, binary 9626484 bytes vs baseline 30794 / 1539784 | PASS |
| 2. Manifold sanity | openscad "3D object (manifold)", Genus 1; independent check: every edge exactly 2 faces (0 directionally unpaired edges of 577584), single shell chi=0 spanning z 0..60 | PASS |
| 3. Hole gate (asciistl, vertices z in [29.98, 30.02], abs(y) < 25, abs(x) < 30) | min abs(y) = 10.000000000 exactly (throat 20/2), 44 band vertices | PASS |
| 4. Stigma gate: material spans the stigma diameter at y=0 | union outline crossing (echo): crossing = 20 exactly (cross_star 14.28, cross_stigma 20, outermost wins, wall normal [1, 0]); artifact ray casts from the origin: slice z=2.011: 1 boundary crossing each way at +20.000000 / -20.000000 (stigma wall, below the countersink's z reach 14.19); slices z=10.011 and z=49.989 (band edges): +20.000000 / -20.000000 each way, plus/minus 60.000000 on the x=0 line | PASS |
| 4b. Midplane-band character (reported, not a gate) | at z=19.991 the y=0 line crosses the countersink dimple at +2.766034 / -2.766034 (the v2 scoop sphere at the wall crossing, same character as step 1); at the bore band z=29.981 the y=0 line is interior void (the throat) and the x=0 line reads +-60.000000 with the bore's faceted wall at 9.999534 | REPORTED |
| 5. bbox: fillets remove material only | x-span 109.073715, y-span 120.000000, z 0.000000..60.000000 (z-span 60.000000 exactly); step-1 values 109.074 / 120.000 / 60.000: plan spans equal (<= step-1 within storage rounding) | PASS |
| 5b. Material removed (info row) | baseline volume 389767.447 mm3, step-2 volume 344650.305 mm3, removed 45117.142 mm3 (combined share of the petal fillets, the stigma radius 30 to 20 shrink and the relocated countersink) | REPORTED |
| 6. Valley-collapse probe, all exit 0 + NoError | defaults: Facets 192528, Genus 1; `-D petal_depth=1`: Facets 277248, Genus 1; `-D roundness=1`: Facets 31040, Genus 5; `-D petal_depth=10`: Facets 171436, Genus 1 | PASS (see deviations for the Genus 5) |
| 7. Regression | `PYTHONPATH= python3 -m pytest tests/ -q`: 34 passed in 9.87s | PASS |
| 8. Dash scan (em U+2014 / en U+2013) | python scan over `templates/bead_flower.scad` and this file: em=0, en=0 both | PASS (count 0) |

## Deliverable

`/Users/djmcnay/Downloads/beads-camilla-v1/bead_flower.stl` OVERWRITTEN in
place (same name, new geometry: binary, 9626484 bytes, Facets 192528, bbox
x 109.073715 / y 120.000000 / z 60.000000), rendered at template defaults,
nothing else created or modified in that folder (same 8 files as before).
`cmp` delivered vs a fresh default render of the committed template: BYTE
IDENTICAL.

## Echoes (per dial setting)

```
defaults:        flower_hole_entry_x = 20,    flower_cross_star = 14.28,
                 flower_cross_stigma = 20,    flower_wall_normal = [1, 0],
                 flower_hole_len = 54.574
petal_depth=1:   flower_hole_entry_x = 52.8,  flower_cross_star = 52.8,
                 flower_cross_stigma = 20,    flower_wall_normal = [1, 0],
                 flower_hole_len = 61.163
roundness=1:     flower_hole_entry_x = 20,    flower_cross_star = 14.28,
                 flower_cross_stigma = 20,    flower_wall_normal = [1, 0],
                 flower_hole_len = 37.218
petal_depth=10:  flower_hole_entry_x = 20,    flower_cross_star = 4.8,
                 flower_cross_stigma = 20,    flower_wall_normal = [1, 0],
                 flower_hole_len = 53.8607
```

The default crossing is x = 20 exactly (the stigma wall): the brief's
conditional "if the petal valleys stay outside the stigma" is in fact
false at defaults (the petal valley at 14.28 stays INSIDE the diameter-40
stigma), so the outermost-of-two scan picks the stigma wall, mechanics
unchanged from step 1. At `petal_depth=1` the valleys move outside
(valley radius 52.8) and the star-flank branch carries the crossing, also
with normal [1, 0] by the bead_star tangent recompute.

## Deviations / notes

1. **`roundness=1` reports Genus 5** (vs Genus 1 elsewhere): the render is
   exit 0, Status NoError, and the independent check shows a SINGLE
   connected shell (all 31040 facets, V=15512, chi=-8, z 0..60, every
   edge exactly 2 faces). Per the SKILL.md genus rule (read Genus against
   the same template's lineage; slabbed extrusions are allowed extra
   genus/shells with Status NoError) this is the sharp-valley
   slab-union characteristic of the erosion-slab construction lineage,
   which the star face-fillet findings already documented as family
   behaviour (they saw Genus -3 with extra closed shells there). Not
   altered; no gate covers it; no tuning applied.
2. **Valley necks survive**: no assert failed and no geometry vanished in
   any probe render; every render is one connected shell spanning
   z 0..60 exactly. The bottom slabs' valley erosion near the +x/-x
   valleys sits inside the radius-20 stigma footprint, which the union
   masks; the artifact slices carry that evidence.
3. `flower_hole_len` is unchanged from step 1 (54.574 at defaults): the
   wall-span scan is driven by the petal outline, not the stigma.
4. Insight of the CUSP gate: `offset(r = -u)` was NOT hand-tuned; all
   insets are the family arc tables (`fillet_u`, `n_fillet = 32`,
   `fillet_radius = width / 12`), identical in form to
   `bead_heart.scad` / `bead_star.scad`.
