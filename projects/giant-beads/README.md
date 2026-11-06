# projects/giant-beads — the giant-bead family

A finished stl-forge project that generates parameterised, print-ready
bead artefacts. Owned templates: `templates/bead.scad` (cylinder letter
bead, two-colour two-body model), `templates/bead_heart.scad` (heart
bead), `templates/bead_star.scad` (star/flower bead). The two provenance
copies sit beside them verbatim:
`templates/parametric_heart_reference.scad` and
`templates/parametric_star_flower.scad` (see "Provenance" below).

## One command, all artefacts

Run these from the skill directory `skills/stl-forge/` (the paths below
are skill-root-relative):

```bash
# The one-liner: word row + heart + star + flower
python3 projects/giant-beads/main.py \
    --width 120 --letters "C A M I L A" --parts heart,star,flower

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
  at default bubble; `star` -> bead_star.scad at template defaults;
  `flower` -> bead_star.scad with `roundness=20` and `petal_depth=3`.
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
| preset | `bead_<name>.stl` + `_body` / `_letter` splits + `.3mf` | `--preset` |

## Shared bead parameters (all templates in this project)

| param | meaning | default / rule |
|---|---|---|
| `width` | enclosing-circle / cylinder outer diameter of the face (mm) | 120 — positive INTEGRAL mm only (fractional/bad values exit 2, never silently truncated) |
| `height` | extrusion, derived | bead.scad `width/2`; bead_heart `width/2.2`; bead_star `width/2` |
| `hole_diameter` | string-hole throat diameter at the centre plane (mm) | 20 |
| `hole_opening_diameter` | diameter at the two entrances | `max(1.2 * hole_diameter, height/2)` |
| `bore_fillet_radius` | flare arc (mm) | `width/8` — retained vestigially; the bell-flare role is now played by the v2 spherical countersink |

### The v2 spherical-countersink mouth (43db29b + 97da1b1)

Every bead family shares ONE mouth construction (standing procedure),
cut by ONE shared subtractive module: `templates/bead_common.scad`'s
`bead_string_hole(...)` (each template forwards its own local values;
provenance for the construction lives in that module's comment block).
the string-hole mouth is a sphere of radius `sqrt(R_open^2 + k^2)` sunk
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

## bead_heart.scad — heart bead

Bubble dial `bubble` 1..10 (default 5): `roundness = clamp01((bubble-1)/9)`
feeds the generator (bubble 5 = 0.444, just shy of halfway, leaning
sharp). The hole runs along X at `y=0, z=height/2` (bead.scad
orientation) and the v2 spherical countersink (43db29b/97da1b1) is sunk
along the LOCAL wall normal at the heart's own flank: the entry point is
the scale-invariant INTERPOLATED `y=0` outline crossing
(`hole_entry_x`), recomputed per bubble — NOT the old band-style
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

## Approved mouth recipe (cylinder letter bead)

Approved by the principal, 6 November 2026: for the cylindrical
letter bead (`templates/bead.scad`) the hole entrance is the
FILLET-WELL mouth, not a sphere countersink. The template calls the
shared module `bead_string_hole_well` in `templates/bead_common.scad`
(revolved quarter-round crater: the arc leaves the bore wall with zero
slope and meets the flat wall tangentially - G1 at both ends, no rim
crease). The old sphere-crater module `bead_string_hole` is retained
untouched for the oblique-walled shapes (`bead_heart.scad`,
`bead_star.scad`, `bead_flower.scad`), where a revolved well cannot be
tangent to the wall; those keep the sphere countersink deliberately.

Dial (parameters, exact):

    r_mouth_max = H / 2.25 - r_fillet - R_throat   // face-fillet-safe ceiling
    r_mouth     = min(0.5 * d_throat, r_mouth_max) // softness floor

At defaults (width 120 => H 60, fillet_radius 10, hole 20):
r_mouth_max = 6.667, r_mouth = 6.667. Asserts in bead.scad fire rather
than collapse if the dial band goes non-positive.

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
- Root `skills/stl-forge/README.md` — pipeline, validation rules,
  delivery policy; `skills/stl-forge/SKILL.md` — agent contract.
