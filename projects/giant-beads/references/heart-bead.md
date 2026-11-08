# Heart-bead family (templates/bead_heart.scad)

Provenance: built from the principal's supplied parametric heart
generator - two cubic-Bezier silhouettes (sharp, bubble) interpolated by
control-point lerp, fitted inside an enclosing circle that the outline
touches at three points (bottom tip + both upper-lobe shoulders). The
generator is committed verbatim as `templates/parametric_heart_reference.scad`
in this project; keep it in sync if the outline maths ever changes.
The template is parameter-complete but carries no preset in
`presets.json` (reach it with `main.py --parts heart`, which renders the
template defaults — roundness 5 — or drive it directly with `openscad -D`;
add a preset with `"template": "bead_heart.scad"`
when letters or a second deliverable arrive).

## Parameters (defaults)

| Key | Meaning | Default / rule |
|---|---|---|
| `width` | enclosing-circle diameter of the face (mm); the heart is the largest similar fit inside, so heart width ~= 0.93-0.95 x width | 120 |
| `roundness` | puffiness dial, continuous, domain 1..10 | 5 |
| `height` | extrusion, derived | `width / 2` (=60 at width 120) |
| `hole_diameter` | string-hole throat (mm) | 20 |
| `bore_fillet_radius` | hole flare arc (mm) | `width / 8` |
| `fillet_radius` | face quarter-round (mm) | `width / 12` (=10 at width 120); asserts `>0` and `<= height/2` |
| `R_throat` | throat radius (mm) | `hole_diameter / 2` |
| `r_mouth_max` | mouth-radius ceiling (mm) | `(height / 2.25) - (fillet_radius + R_throat)` |
| `r_mouth` | mouth radius (mm) | `max(0.5, min(0.5 * hole_diameter, r_mouth_max))` (=6.667 at width 120) |

Dial mapping: the generator interpolates on an internal 0..1 `roundness`;
`roundness01 = clamp01((roundness - 1) / 9)`, so roundness 1 = sharp
profile, roundness 10 = full bubble, roundness 5 = 0.444 (just shy of
halfway, leaning sharp). The roundness dial does not move the hole axis.

## Construction decisions (do not casually undo)

- Hole runs along X at `y=0, z=height/2` (centred on the cylinder,
  left-to-right viewed top-down on the face) - bead.scad orientation.
- The mouth is the v2 spherical countersink sunk along the LOCAL wall
  normal at the heart's own flank (97da1b1): the entry point is the
  scale-invariant INTERPOLATED `y=0` outline crossing
  (`hole_entry_x`), recomputed per roundness - NOT the old band-style
  `max outline x with |y| < 0.5` measurement, which was scale
  dependent and would drift the rim. bead.scad lands its bell at
  `width/2`, which is out in empty air for the heart; without the
  flank crossing the mouths arrive sharp-lipped at the wall.
  The straight wall band is `z: fillet..height-fillet`; the mouths
  must sit fully inside it - the same
  property bead.scad's own comment requires.
- Face fillets are the bead.scad quarter-arc CARRIED AS EROSION
  Z-SLICES: `n_fillet = 32`, same angles, uniform `offset(r=-u)` of the
  heart outline per slab, each slab taking its BASE point's inset
  (inscribed-chord convention, matching bead.scad's polyline arcs).
  A revolve cannot express this for a non-circular outline, and hull()
  would fill the cleft.
- At sharp plan corners (the bottom tip) the face pulls back by
  `c / sin(half-angle)` - correct behaviour for a real round, NOT a bug:
  the WALL keeps the full sharp tip (global bbox unchanged); only the
  inset face retreats. Expect face Y < width - 2c at the tip.

## Verification bands (measured, width 120)

- Wall bbox, all roundness settings: X 112.734 (b1 111.717 / b10 113.961),
  Y 103.841, Z 60 - fillets and hole never move the outer bbox.
- Face at z=0 (roundness 5): X 92.734 (exactly -10 per side).
- Generator self-test echoes: radial_error and bottom_error at float
  noise (<=1e-14), both lobe touch flags true at roundness
  0/0.25/0.5/0.75/1 - the acceptance gate from the original brief.
- All renders exit 0 with no WARNING/ERROR lines; CGAL `Status: NoError`.
- Any regression here means the outline maths moved: re-run the dial
  ends (roundness 1 and 10) plus default before touching anything else.
