# projects/giant-beads — the giant-bead family

A finished stl-forge project that generates parameterised, print-ready
bead artefacts. Owned templates: `templates/bead.scad` (cylinder letter
bead, two-colour two-body model), `templates/bead_heart.scad` (heart
bead), `templates/bead_star.scad` (star/flower bead),
`templates/bead_spacer_wide.scad` (wide tapered spacer, hole vertical),
`templates/bead_spacer_small.scad` (small doughnut spacer, hole vertical).
The two provenance copies sit beside them verbatim:
`templates/parametric_heart_reference.scad` and
`templates/parametric_star_flower.scad` (see "Provenance" below).

## Interactive family app

`app/` is a single-page Gradio workbench for the same six beads:

```bash
projects/giant-beads/app/.venv/bin/python projects/giant-beads/app/app.py
```

It keeps width and string hole global, offers a per-bead size override,
renders the selected bead live in an orbit viewer, downloads the current
STL, and can build a family zip containing all six STLs plus a settings
note. See `app/README.md` for the layout and behaviour contract.

## One command, all artefacts

Run these from the skill directory `` (the paths below
are skill-root-relative):

```bash
# The one-liner: word row + heart + star + flower
python3 projects/giant-beads/main.py \
    --width 120 --letters "C A M I L A" \
    --parts heart,star,flower,spacer_wide,spacer_small

# One bead preset (body + letter + assembly STLs plus the Bambu .3mf)
python3 projects/giant-beads/main.py --preset bead_D

# Alternate dict input; spec fields first, explicit flags override
python3 projects/giant-beads/main.py \
    --spec '{"letters":"CAMILA","parts":"heart","width":100,"save_to":"/tmp/out","preset":"bead_D"}'
```

Flags:

- `--width MM` — bead width in mm, passed straight through to the
  templates (default 120). Must be a positive INTEGRAL number of mm:
  the CLI flag is integer-typed (argparse rejects e.g. `120.9` with
  exit 2) and a fractional `--spec` width is rejected with exit 2
  rather than silently truncated (`{"width":120.9}` is an error, not
  `120`); booleans/strings are rejected with named-field messages.
- `--letters WORD` — unique uppercase letters, deduped preserving order:
  `"C A M I L A"` renders C,A,M,I,L as ONE row-layout STL named
  `beads_CAMILA.stl` with a clear 10 mm gap between neighbouring beads.
  A non-blank value with no A-Z letter (e.g. `--letters 123`) fails the
  run with exit 2 — an explicitly requested letter job either runs or
  fails, it is never silently dropped (absent/empty stays valid).
- `--parts LIST` — comma list, harmless if empty. `heart` -> bead_heart.scad
  at default roundness; `star` -> bead_star.scad at template defaults;
  `flower` -> bead_star.scad with `roundness=20` and `petal_depth=3`;
  `spacer_wide` -> bead_spacer_wide.scad (tapered barrel, hole vertical);
  `spacer_small` -> bead_spacer_small.scad (doughnut, hole vertical).
- `--preset NAME` — render one bead preset from `presets.json`
  (`bead_D`, `bead_default`, `bead_smooth`), exactly as the old forge.py
  preset suite did, including the Bambu-native `.3mf`.
- `--save-to PATH` — output directory. Default: `$HOME/Downloads`,
  created if missing.
- `--previews` — also write PNG previews into `<save-to>/previews/`.
- `--presets PATH` — alternate presets file (default: this project's
  `presets.json`).
- `--word-gap MM` — clear gap in mm between neighbouring beads in
  `--letters` mode (default 10). Must be a finite number >= 0; a
  negative or non-finite gap exits 2. Zero is allowed (touching beads).

Exit semantics: exit 0 ONLY when every requested artefact exists and is a
valid binary STL — an 80-byte header (not an ASCII `facet normal`
document), a facet count `n` > 0 at offset 80, and a file size of exactly
`84 + 50*n` bytes. Any failed job prints a precise stderr message and the
run exits nonzero. Letter rows additionally self-assert from the binary
(facet sum == sum of sources, symmetric x-span, z base == 0).

Run the tests: `python3 -m pytest projects/giant-beads/tests -q`
(processing tests always run; renders are skipif-gated on
`/Applications/OpenSCAD.app` and use a 60 mm width for speed).

## Naming rules

| artefact | name | when |
|---|---|---|
| word row | `beads_<WORD>.stl` | `--letters` (word as normalised, e.g. `beads_CAMILA.stl`) |
| heart shape | `bead_heart.stl` | `--parts heart` |
| star shape | `bead_star.stl` | `--parts star` |
| flower shape | `bead_flower.stl` (bead_star.scad, roundness 20) | `--parts flower` |
| wide spacer | `bead_spacer_wide.stl` | `--parts spacer_wide` |
| small spacer | `bead_spacer_small.stl` | `--parts spacer_small` |
| preset | `bead_<name>.stl` + `_body` / `_letter` splits + `.3mf` | `--preset` |

## Bead-family parameters

`param-defaults.json` is the canonical defaults contract. `main.py` reads
its `main_defaults.width` and `main_defaults.word_gap` from that file, and
`tests/test_spec_and_naming.py` checks that every owned template is listed,
declares the common parameter names, and matches the JSON's spacer and
common keys. Change a template default and the JSON in the same commit.

| param | meaning | default / rule |
|---|---|---|
| `width` | enclosing-circle / cylinder outer diameter of the face (mm) | 120 — positive INTEGRAL mm only (fractional/bad values exit 2, never silently truncated) |
| `roundness` | shape dial | heart 1..10 (default 5; 10 = full bubble); star 1..20 (default 12) |
| `points` | star tip count | 5 |
| `petal_depth` | star valley-depth dial 1..10 | 3 |
| `height` | extrusion / overall height, derived | letter/heart/star/flower `width/2` (=60); wide spacer `width` (=120); small spacer `width/4` (=30) |
| `hole_diameter` | string-hole throat diameter at the centre plane (mm) | 20 |
| `outer_diameter` | widest/outer diameter of a spacer (mm) | both spacers: letter bead height = `width/2` (=60 at width 120) |
| `bore_fillet_radius` | flare arc (mm) | `width/8` — retained, unused by the current mouths |
| `fillet_radius` | face quarter-round (mm) | `width/12` (=10 at width 120); flower petals use `width/4` |
| `R_throat` | throat radius (mm) | `hole_diameter/2` |
| `r_mouth_max` | mouth-radius ceiling (mm) | letter/heart/star: `(height/2.25) - (fillet_radius + R_throat)`; small spacer: `min(H/2, R_out - R_throat - outer_fillet)` |
| `r_mouth` | mouth radius (mm) | letter/heart/star: `max(0.5, min(0.5*hole_diameter, r_mouth_max))`; star adds `r_wall_max = width/120`; small spacer: `-1` = auto-match the outer fillet, effective value in `r_mouth_eff` |
| `face_diameter` | wide spacer top/bottom face diameter (mm) | `(width/2) - 2*(width/12)` = `width/3` (40 at width 120) |
| `curvature` | spacer shape dial | wide: 2.0 = parabola / banana shallot (1 = straight bicone, >2 fuller); small: 0.5 = medium doughnut (0 = flat washer, 1 = full doughnut) |
| `$fn` | render resolution | 128 |

`--parts flower` drives `bead_star.scad` with `roundness=20,
petal_depth=3`; the separate `bead_flower.scad` template uses
`points=6`, `petal_depth=8` and the tripled petal fillet
`fillet_radius=width/4`.

### The v2 spherical-countersink mouth (43db29b + 97da1b1) — historical

**Superseded for the heart and star by the swept ball fillet** (see
"Approved mouth recipe" below); the flower keeps the plain bore. The v2
construction used the now-retired opening dial
(`hole_opening_diameter` / `R_open`): a sphere of radius
`sqrt(R_open^2 + k^2)` sunk
`k` mm along the LOCAL wall normal at the hole-axis outline crossing,
with a straight `R_throat` bore along X; rim radius = R_open exactly. A
sphere meets any smooth wall in smooth curves, so no fin/wedge can form
on oblique or overhanging flanks — that was the bead_star v1 defect
(bore-axis revolve countersink). Portability notes: `max()` over vectors
is unsupported in this OpenSCAD build (use a two-pass scalar argmin) and
the build has no `normalize()` (only `norm()`/vector arithmetic).

## bead.scad — cylinder letter bead

Derived values may be overridden per preset by supplying the key
explicitly (e.g. `"height": 45`); omitting uses the formula. Additional
derived rules: `fillet_radius = width/12` (quarter-round face fillet) and
`letter_recess_top = width/30` (4 mm at width 120). The well-mouth funnel
defaults ON with a fixed 0.2 mm rim fillet (18/19 Oct 2026 user default;
was 2 mm) - see `letter_fillet` / `letter_recess_fillet` below.

Letter parameters (two-colour lettering):

| param | meaning | default |
|---|---|---|
| `letter_top` / `letter_bottom` | letter on the top / bottom face | `"M"` / same as top |
| `letter_top_rotate` / `letter_bottom_rotate` | in-plane rotation, deg | 0 / 0 (90 was wrong: the 18 Oct 2026 user correction fixed stringing orientation at 0) |
| `letter_space` | letter fits a circle of diameter `width * letter_space` | 0.75 (`bead_smooth` 0.45) |
| `letter_bold` | faux-bold `offset(r)`, mm/side, outside the scale | 1 |
| `letter_font` | fontconfig name for `text()`; MUST be the full name | `"Arial Rounded MT Bold"` (options: `"Arial"`, `"Times New Roman"`, `"Courier"`) |
| `letter_recess_top` | top letter sinks this far below the top face | `width/30` (4 mm at width 120) |
| `letter_insert_t` | top insert thickness (floor of the well) | 1 |
| `letter_fillet` | concave funnel rim at the well mouth | `true` |
| `letter_recess_fillet` | funnel flare radius at the well rim (mouth opens to letter + 2x radius); USED only when `letter_fillet` is true | 0.2 mm fixed (not a width ratio); must stay <= `letter_recess_top` |
| `letter_outline_width` | bottom outline-groove width (~2 x 0.4 mm lines) | 0.8 |
| `letter_bite_bottom` | bottom outline-groove depth | 1 |

The `part` parameter selects the solid: `part="body"` (white body with
the top well + bottom outline groove cut), `part="letter"` (black top
insert only), `part="assembly"` (body + insert, two-tone preview). The
letter circle-fit rule scales via `s = (target - 2*bold)/diag_ref` so the
bbox corners touch the circle, bold inflation sits outside the scale, and
and (with the funnel default ON) the top-recess rim meets the flat face
through a smooth concave flare 0.2 mm tall - tangent to the straight
well wall at the flare base and tangent to the face at the rim, so the
rim is never sharp. Bottom is an outline groove (letter paints by slicer
flood-fill inside the closed ring, colour is a slicer job). The bottom
outline is mirrored so it reads correctly from below. Print orientation:
letter-face down; z=0 on the build plate, hole bridged without supports.

Why a Bambu-native 3MF: core-spec colorgroups import as Color PAINT
instead of filament assignment (Bambu bug bambulab/BambuStudio#9666). The
project `.3mf` writes per-part `<metadata key="extruder" value="N"/>`
inside `Metadata/model_settings.config` instead: one object, two parts,
identical coordinates (no transforms) so every bead of a batch shares
per-layer colour maps. Presets carry `parts: ["body","letter"]` and
`preview: "assembly"` (HotPink is preview-only inspection contrast).

`bead_smooth` keeps `letter_space` 0.45 because its `fillet_radius=30`
leaves only a 60 mm flat face: `120*0.45 = 54 < 60` fits, while 0.75 ->
90 overflows the face assert. `bead_D` is the letter-D variant with
`letter_font "Courier"`.

## bead_bear.scad — bear bead

The bear uses the letter bead's outer-family rules: `width` is the
widest part of the cheeks, `height = width / 2` is the body thickness,
the bore is a plain 20 mm tunnel, and the bottom stays flat on the build
plate. The first pass is a straight extrusion with no face fillet, so
the approved detail field stays flat and supported. The face is a broad, gently elliptical shape with two large high ear
lobes; the ears sit outboard of the cheeks, so the overall ear span is
wider than the family width.  The face, ears,
inner ears, eyes and muzzle are traced as flat ellipses/arcs from the
supplied reference and extruded straight in this first pass. The inner-ear shapes are a
shallow recess on the front face, clipped where the head overlaps them; the eye pads and muzzle (the round
snout carrying the nose and mouth) are raised; catchlights, nose and
mouth are embossed on top. The build-plate face carries shallow
contour-groove etches for the inner ears, eyes, pupils, muzzle, nose
and mouth, in the same print-friendly language as the letter bead's
bottom groove. The mouth is a fillable line groove rather than a
contour ring so it stays printable at small widths. Dials: `ear_size`,
`eye_spacing`, `muzzle_size`, `detail_relief`.

## bead_heart.scad — heart bead

Roundness dial `roundness` 1..10 (default 5): mapped to the generator's
0..1 profile blend as `roundness01 = clamp01((roundness-1)/9)` (5 =
0.444, just shy of halfway, leaning sharp). The hole runs along X at
`y=0, z=height/2` (bead.scad orientation) and the swept ball fillet is
cut along the heart's own wall edge: the entry point is the
scale-invariant INTERPOLATED `y=0` outline crossing
(`hole_entry_x`), recomputed per roundness dial — NOT the old band-style
`max outline x with |y| < 0.5` measurement, which was scale dependent.
bead.scad's `width/2` landing is in empty air for the heart. Face fillets
are the bead.scad quarter-arc carried as erosion Z-slabs
(`n_fillet = 32`, uniform `offset(r=-u)` of the heart outline per slab;
a revolve cannot express this on a non-circular outline, and hull()
would fill the cleft). At sharp plan corners (bottom tip) the face pulls
back by `c/sin(half-angle)` — correct round behaviour, not a bug: the
wall keeps the full sharp tip. Measured verification bands (width 120)
and construction decisions: `references/heart-bead.md`. No letters yet —
template-only family wired in via `main.py --parts heart`.

## bead_star.scad — star/flower bead

Dial `roundness` 1..20 (default 12: 1 = sharp star, 10 = bulbous,
20 = flower), `points >= 3` (default 5), `petal_depth` 1..10 (default 3 —
the principal's rename of the generator's `depth`, mapped as
`depth = petal_depth` because OpenSCAD identifiers cannot contain a
hyphen). One tip points vertically up; the valley ratio is determined
automatically. `--parts star` renders template defaults (roundness 12),
`--parts flower` drives `roundness=20, petal_depth=3`.

## bead_spacer_wide.scad — wide tapered spacer

The wide spacer is the first bead in the family whose string hole is
**vertical** (axis Z, bottom face on the build plate), not through the
side. It is a double cone / barrel:

- `height = width` (120 mm at defaults), not the letter bead's
  `width/2`.
- Widest point at `z = height/2` (60 mm at defaults), with diameter
  equal to the letter bead's height = `width/2` = 60 mm. The spacer is
  the letter bead's 120 x 60 proportions turned upright.
- Top/bottom face diameter = letter bead height - 2 x letter face
  fillet = `(width/2) - 2*(width/12)` = `width/3` = 40 mm at defaults.
  The face is a flat annulus around the bore.
- Hole throat 20 mm, plain straight bore, **no mouth fillet yet** at
  either end.
- The side is a parabola by default — the banana-shallot profile:
  `r(z) = R_out - (R_out - R_face) * abs(1 - 2*z/H)^curvature`,
  with `curvature = 2`. The widest point at mid-height is smooth, and
  the ends taper into the flat faces. `curvature = 1` is a straight
  bicone; values above 2 keep the middle fuller and steepen the taper
  into the faces. The widest point is smooth for every value >= 1.
- The equatorial bulge is only 10 mm over a 60 mm half-height
  (roughly 18 deg maximum overhang at the faces), so the body prints
  support-free. The plain bore also removes the top-mouth countersink
  overhang that a filleted mouth would add.

## bead_spacer_small.scad — small doughnut spacer

The small spacer is the doughnut: a squat ring with the bore vertical.

- Outer diameter = letter bead height = `width/2` = 60 mm.
- Bore throat = 20 mm at its narrowest.
- Overall height = letter bead height / 2 = `width/4` = 30 mm.
- Looking down the hole: a Ø60 circle with a filleted mouth around the
  Ø20 throat.
- `curvature` (0..1) controls the outer edge:
  0 = nearly flat washer with a small outer fillet (`H/8`);
  1 = full doughnut, where the outer fillet reaches `H/2` (semicircular
  rim); the default **0.5** is the medium rounded doughnut.
- The **hole mouth is filleted too**. `r_mouth` (mm) controls it; the
  default `-1` means "match the outer fillet" automatically, and the
  effective value is `r_mouth_eff`. At the default 0.5 both fillets are
  9.375 mm and a 1.25 mm flat land remains between them. The auto value
  clamps when the radial wall or half-height cannot fit it (at
  curvature 1.0 the outer fillet is 15 mm, so `r_mouth_eff` auto-clamps
  to 5 mm). Set `r_mouth` to a positive mm value for a different inner
  radius.
- The throat is still exactly 20 mm; the fillets only flare the mouths.
- Printed hole-up, the bottom fillet is an overhang; lower curvature
  is flatter and more forgiving, 1.0 is the curviest.

## Approved mouth recipe (cylinder letter bead)

Approved by the principal, 6 November 2026: for the cylindrical
letter bead (`templates/bead.scad`) the hole entrance is the
FILLET-WELL mouth, not a sphere countersink. The template calls the
shared module `bead_string_hole_well` in `templates/bead_common.scad`
(revolved quarter-round crater: the arc leaves the bore wall with zero
slope and meets the flat wall tangentially - G1 at both ends, no rim
crease). The old sphere-crater module `bead_string_hole` is retired:
the heart and star now use a swept ball fillet local to each template
(tangent to both surfaces on their oblique walls), and the flower keeps
the plain bore (`bead_string_hole_plain`).

Dial (parameters, exact):

    r_mouth_max = (H / 2.25) - (r_fillet + R_throat)      // safe ceiling
    r_mouth     = max(0.5, min(0.5 * d_throat, r_mouth_max)) // floor

At defaults (width 120 => H 60, fillet_radius 10, hole 20):
r_mouth_max = 6.667, r_mouth = 6.667 for the letter bead. The heart
uses the same dial (H 60 => 6.667). The star adds
`r_wall_max = width/120` (1 mm at width 120) because its outline runs
close to a valley/tip; r_mouth = min(dial, r_wall_max). Asserts in
bead.scad fire rather than collapse if the dial band goes non-positive.

Verification (all measured, same session): SolidCraft reference
610,079.46 mm3 / 243 faces; the scad build `build/bead-well.scad.stl`
measures 608,548.222 mm3 (0.25 percent residual, tessellation scale);
the pre-swap contrast build `build/bead-before.stl` is 597,964.409 mm3
and shows the sphere mouth's wall crease in section
(`build/before-*.scad` are the pre-edit template copies).

## Provenance

The outline generators were supplied by the principal (ChatGPT
generators) and are committed VERBATIM as provenance copies:
`templates/parametric_heart_reference.scad` (cubic-Bezier sharp/bubble
heart profiles, linear control-point interpolation, touches its enclosing
circle at the bottom tip and both upper-lobe shoulders) and
`templates/parametric_star_flower.scad` (unified star/flower radial
profile with independent valley depth, touches the circle at every outward
tip). Keep them in sync if outline maths ever changes.

## References

- `references/heart-bead.md` — heart-bead verification bands.
- Root `README.md` — pipeline, validation rules,
  delivery policy; `SKILL.md` — agent contract.
