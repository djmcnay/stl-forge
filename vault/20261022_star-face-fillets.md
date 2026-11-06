---
title: Star face fillets
date: 2026-10-22
tags: [bead, star, fillets, openscad, giant-beads]
---

# FINDINGS: star face fillets (feat/star-face-fillets)

Executed per `BRIEF_star_face_fillets.md`. Branch `feat/star-face-fillets`
cut from main `38f3da6`; two labelled commits, never merged, never pushed:

1. `252ff84` — bead_star: add `fillet_radius = width/12` param (+
   positivity / height-half asserts)
2. `b0f76a3` — bead_star: rebuild `star_body()` as erosion-slab face
   fillets (n_fillet=32, mirrored from bead_heart)

## Files touched

- `templates/bead_star.scad` — ONLY code file touched (explicit-path
  `git add`; nothing else staged, other sessions' dirty files untouched).
- `README.md` — NOT touched: its bead_star paragraph (lines 175-183) makes
  no "no fillets" claim, so the optional one-sentence fix was not needed.
- In-file comment updates, inside the touched file only: header line "no
  face fillets" -> "quarter-round face fillets (width/12)"; deliverable
  comment "Flat faces, z = 0 base." -> "Quarter-round face fillets at both
  faces (width/12), z = 0 base."

## Per-construction summary (copied from bead_heart, not reinvented)

- `fillet_radius = width / 12;` (10 mm at width 120), section comment
  mirroring bead_heart's phrasing verbatim ("bead.scad default:
  fillet_radius = width / 12 -> 10 mm at width 120").
- Asserts copied verbatim: `fillet_radius > 0` and
  `fillet_radius <= height / 2 so fillets never overlap`.
- Arc tables identical in form to heart's: `n_fillet = 32`,
  `c = fillet_radius`, `side_len = height - 2*c`,
  `fillet_u[i] = c - c*cos(-90 + 90*i/32)` (inset from wall),
  `fillet_z[i] = c + c*sin(-90 + 90*i/32)` (z of arc point).
- `star_body()` = union of: 32 bottom slabs — `translate(z=fillet_z[i])`
  + `linear_extrude(z[i+1]-z[i])` + `offset(r = -fillet_u[i])` of
  `star_2d(width, points, roundness, petal_depth)` (each slab takes its
  BASE point's inset, chords inscribed); straight mid band `[c, height-c]`
  guarded by `side_len > 0.001`; 32 mirrored top slabs
  `[height - z[k+1], height - z[k]]` with inset `u[k]`.
- Inset primitive is `offset(r=-u)` erosion only — the star outline has
  CUSPS at the tips; no `hull()`, no hand-displaced vertices.
- `string_hole()` and the `difference()` structure untouched (byte-form
  equivalence preserved by construction). `hole_entry_x` still derives
  from the UNFILLETED `star_vertices` outline; echo verified IDENTICAL
  pre/post: `star_hole_entry_x = 49.7114, star_wall_normal =
  [0.659298, -0.751882], star_hole_len = 62.7676`.

## Acceptance gates (measured)

| Gate | Baseline (pre-edit) | Post-edit | Verdict |
|---|---|---|---|
| Star binary vs `bead_star_base.stl` (1237284 B / 24744 facets, verified == `regr-suite/bead_star.stl` by `cmp`) | 1237284 B / 24744 facets | 12750084 B / 255000 facets, `cmp` exit 1 (differs) | PASS (must differ) |
| Star plan bbox must not GROW | x-span 115.535294, y-span 111.149990 | x-span 115.535294, y-span 111.149990 (identical to 6 dp) | PASS |
| Star z-span == height exactly | 60.000000 | 60.000000 (flag True within 1e-6) | PASS |
| Material removed (volume) | 427343.358 mm³ | 410078.446 mm³ (−17264.912) | PASS (fillets remove material) |
| Hole probe: min abs(y) among verts with abs(z−height/2)≤0.02, abs(x)≤hole_entry_x | 10.0 == throat (R_throat=10); z-band vertex count 24 | 10.0 == throat; z-band vertex count 24 | PASS (mouths intact) |
| Slab staircase: n_fillet=32, c=10 arc z-steps | (fillet_z steps) min 0.012045, max 0.490677, avg 0.312500 mm ("about 0.3" ✓) | STL bottom band holds exactly 33 distinct z levels == fillet_z set; top band == 60−fillet_z set | PASS — slab count KEPT at 32, no change made |
| Staircase visual character vs heart | heart bottom preview (rendered fresh at `regr-heart-pre/bead_heart_bottom.png`, same straight-orthographic camera) | star bottom preview identical style: eroded-outline silhouette; slab-band staircase visible on the rim in iso view, same character as heart | PASS, count unchanged |
| Suite `--parts heart,star,flower --save-to regr-starfillet --previews` | — | exit 0; 3 artefacts valid binstl + 15 preview PNGs | PASS |
| Heart cross-effect | regr-suite & fresh pre-render: 14645284 B / 292904 facets | post suite: 14645284 B / 292904 facets; `cmp` vs pre-edit render: byte-IDENTICAL | PASS (unchanged template, no cross-effect) |
| Flower (uses bead_star.scad, WILL change) | 1161684 B / 23232 facets, volume 471371.567, x 117.600868, y 113.555889, z 60.000000, throat 10.0 | 12613284 B / 252264 facets, volume 452902.537 (−18469.030 removed), x-span 117.600868, y-span 113.555889, z 60.000000, throat 10.0 | PASS (only-fillets-changed) |
| Standalone `openscad -o /tmp/x.stl templates/bead_star.scad` | — | exit 0, ascii 255000 facets (72800209 B), Status NoError | PASS |
| `python3 -m pytest tests/ -q` | — | **34 passed in 9.58s**; no xfail, no fail lines | PASS |
| Mesh integrity | 1 shell, χ=0, genus 1 (all edges 2-manifold) | OpenSCAD log "Genus: -3", Status NoError; independent check: 5 closed shells (main χ=0 genus 1 + 4 genus-0 shells z∈[50.98,60]), every edge exactly 2 faces | Reported, see deviations |

## Deviations / notes (exact numbers, no silent alterations)

1. **stl_probe.py path correction**: the brief's
   `skills/stl-forge/scripts/stl_probe.py` does not exist; the script is
   at `skills/stl-forge/core/stl_probe.py`. The real path was used.
2. **OpenSCAD "Genus: -3" log line + 5-shell STL** on the post star is
   FAMILY-CONSISTENT: the shipped, unmodified `bead_heart.scad` renders
   the identical figure (log Genus -3, Status NoError; 5 shells: main
   genus 1 + 4 genus-0 closed shells confined to its top fillet band,
   z 46.496-54.545). Both meshes are edge-2-manifold closed surfaces;
   the extra shells are contiguous nested slabs of the top fillet band
   produced by the CGAL union of the coplanar-abutting erosion slabs —
   exactly the construction the brief ordered copied. Baseline star (no
   fillets) is 1 shell / genus 1. Not altered; no gate covers it.
3. **x-span/y-span are NOT width (120)** — as the brief anticipated for a
   5-point tip-up star. Reference values establishing the new baseline:
   x-span 115.535294, y-span 111.149990 (identical pre/post to 6 dp);
   z-span exactly 60.000000.
4. **Small-width characteristic (unexercised by gates)**: at very small
   widths the scoop sphere can graze the fillet band (e.g. width 60:
   R_ball 13 > height/2 − c = 10); at width 120 defaults
   R_ball 15.8114 sits inside the straight band [10, 50]. Same
   characteristic exists in bead_heart's construction; no code change.
5. Extra regr dir created: `regr-heart-pre/` (pre-edit heart render +
   comparison PNGs); both `regr-heart-pre` and `regr-starfillet` left on
   disk, never staged, per Fences.
6. Baseline renders/probes used the pre-edit tree on the branch (identical
   content to main `38f3da6`; `templates/bead_star.scad` was clean).

## Artefact locations

- Post suite: `regr-starfillet/{bead_heart,bead_star,bead_flower}.stl`
  + `regr-starfillet/previews/*.png` (15).
- Pre-edit heart comparison: `regr-heart-pre/bead_heart.stl` and
  `bead_heart_{bottom,iso,hole}.png`.
- Baseline star: unchanged at
  `/Users/djmcnay/.hermes/profiles/araminta/cache/scratch/mouth-baseline/bead_star_base.stl`.

No gate could not be passed confidently; no xfail was needed and the code
was kept exactly on the heart's construction.
