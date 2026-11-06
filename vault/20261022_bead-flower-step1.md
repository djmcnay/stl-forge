---
title: bead_flower.scad step 1 — stigma cylinder + petal union
date: 2026-10-22
tags: [bead, flower, giant-beads, openscad]
---

# FINDINGS: bead_flower.scad step 1 (stigma cylinder + petal union)

Branch: `feat/bead-flower-step1` (cut from the current `main` checkout;
never merged, never pushed). Working directory:
`/Users/djmcnay/GitHub/araminta-skills/skills/stl-forge/projects/giant-beads`.

## Files touched

| Commit | File |
|---|---|
| 1bcd63e | `templates/bead_flower.scad` (NEW) |

Only that path was staged/committed. The dirty files from other sessions
(minty-sync, pi-media-server, `FINDINGS_star_face_fillets.md`) and the
untracked brief were left unstaged and untouched. No changes at all to
`bead.scad` / `bead_heart.scad` / `bead_star.scad` / `bead_common.scad` /
`main.py` / `presets.json`. No `.3mf`. No face fillets (step 1 is form
only). No tests added (the 34-test suite still passes).

## Union construction (two sentences)

`flower_body()` is a 3D `union()` of two solids sharing the z band
0..height: the petal outline (`star_2d` reused verbatim from
`bead_star.scad` via `use <bead_star.scad>`, extruded with the SAME
extrusion as star: plain `linear_extrude(height)`) and the central stigma
cylinder (`cylinder(h=height, d=width_stigma)`), both concentric on the z
axis with one tip pointing up as the generator orients it. The shared v2
mouth (`use <bead_common.scad>` / `bead_string_hole(...)`, forwarded
EXACTLY as bead_star does) is then subtracted, and `hole_entry_x` and
`n_out` come from THIS template's own union outline: an interpolated
y=0 (+x) crossing scan over BOTH the star polygon and the $fn-matched
stigma circle points, with the outermost crossing winning, so any pinned
number is impossible.

At the defaults the petal valley on the +x axis (x=14.28) dips inside the
stigma (R=30), so the union crossing is `cross_stigma = 30` exactly (the
circle vertex sitting at (30, 0)) and the countersink lands on the
cylinder wall with normal exactly `[1, 0]`. The star-flank branch is
exercised the moment the valley moves outside the stigma: at
`petal_depth=1` the crossing becomes `cross_star = 52.8` (the star's own
wall, normal also `[1, 0]` by the bead_star tangent recompute, whose
valley flank is locally vertical by symmetry), and both branches rendered
NoError below.

## Gate rows (measured numbers)

```
openscad --export-format=binstl -o regr-flower-step1/bead_flower.stl
templates/bead_flower.scad
```

| Gate | Measured | Verdict |
|---|---|---|
| 1. Default render exit / Status | exit 0, Status NoError, Genus 1, Vertices 15397, Facets 30794 (binary, 1539784 bytes) | PASS |
| 2. Manifold / genus sanity | probe: `format binary \| facets 30794 \| bytes 1539784`; openscad reports "3D object (manifold)", Genus 1 | PASS |
| 3. Hole gate (throat at z=height/2) | asciistl render + awk over vertices in `29.98 < z < 30.02`: min abs(y) = 10.000000000 (throat 20/2) exactly, 68 band vertices, reported at x=-42.682875; same 10.000000000 with the narrower window `\|x\| < 30` (20 vertices) | PASS |
| 4. Union gate: material across the stigma | slice z=2 (below the bore band) via stl_probe + ray cast from the origin: 1 boundary crossing each way on +-x at +-30.000000 (stigma wall) and on +-y at 60.000000 (up tip), i.e. material spans x=-30..+30 at y=0: the stigma is PART of the solid (no subtractive cut) | PASS |
| 4b. Outer bbox plan spans | x-span 109.074, y-span 120.000 (z-span 60.000). x-span is NOT 120: max-x outline points are interior petal points (e.g. radius ~59.4 at angle ~24.4 deg, x=54.07) still inside the enclosing circle; tips sit at angles 90/30/-30... so x reaches only 54.537 at those points. Reported, not tuned (brief: "if the measure differs, report the numbers, do not tune") | REPORTED |
| 5. Petal dial sanity | default Facets 30794; `-D roundness=1` -> Facets 23666 (NoError, Genus 1); `-D petal_depth=1` -> Facets 28928 (NoError, Genus 1): both overrides reach the geometry, counts differ from defaults | PASS |
| 6. Regression suite | `/bin/zsh -lc 'PYTHONPATH= python3 -m pytest tests/ -q'`: 34 passed in 9.16s | PASS |
| 7. Dash scan (em U+2014 / en U+2013) | python scan over `templates/bead_flower.scad`, `FINDINGS_bead_flower_step1.md` (this file): em=0 en=0 both | PASS (count 0) |

## Deliverable

`/Users/djmcnay/Downloads/beads-camilla-v1/bead_flower.stl` (binary,
1539784 bytes, Facets 30794, bbox x 109.074 / y 120.000 / z 60.000),
rendered at template defaults, nothing else created in that folder.
`cmp` against the scratch default render: BYTE-IDENTICAL.

Scratch dir `regr-flower-step1/` inside the project holds the probe
renders (`bead_flower.stl`, `bead_flower_ascii.stl`, `flower_r1.stl`,
`flower_pd1.stl`); left untracked, never staged or committed.

## Caveats and echoes

```
ECHO defaults:        flower_hole_entry_x = 30,     flower_cross_star = 14.28,
                      flower_cross_stigma = 30,     flower_wall_normal = [1, 0],
                      flower_hole_len = 54.574
ECHO roundness=1:     flower_hole_entry_x = 30,     flower_cross_star = 14.28,
                      flower_cross_stigma = 30,     flower_wall_normal = [1, 0],
                      flower_hole_len = 37.218
ECHO petal_depth=1:   flower_hole_entry_x = 52.8,   flower_cross_star = 52.8,
                      flower_cross_stigma = 30,     flower_wall_normal = [1, 0],
                      flower_hole_len = 61.163
```

- `use <bead_star.scad>` imports the generator (functions + `star_2d`)
  without executing bead_star's top-level geometry/asserts (no
  star_hole_entry_x echo in the transcript above, single Genus-1 solid),
  so bead_star.scad stayed untouched.
- The stigma is a 128-gon prism and the countersink rim hangs on that
  faceted wall, same $fn as the shared-mouth sphere/cylinder in the
  family; the hole gate still measures the exact throat radius.
- No deviations in behaviour other than gate 4b's x-span note above:
  the brief's "expect x-span == y-span == 120" does not hold for a
  6-petal outline whose tips are at 0/+-30/+-150 deg; reported untouched
  per the brief's own instruction.
