# Bambu .3mf output (stl-forge)

## Why native, never "colored 3MF"

An STL is triangles only - one mesh, zero colour, one filament slot.
Two 3MF flavours exist: **core-spec colour** (colorgroups / base
materials - what Fusion and most third-party tools export) and
**Bambu-native project** (`Metadata/model_settings.config` carrying
`extruder` tags). On Bambu Studio 2.5+ the core-spec route goes through
a colour-mapping import dialog that converts colours into per-surface
PAINT: the object tree shows a single filament, recolouring means
repainting, and paint spreads across layer boundaries so thin
surface-colour designs bleed over several layers - which breaks batch
printing (per-object painted layer maps differ, so objects only print
one at a time). Behaviour is version-dependent: read the installed
version with
`defaults read /Applications/BambuStudio.app/Contents/Info.plist CFBundleShortVersionString`
and re-confirm import behaviour after any slicer upgrade.

The native schema is assignment, not paint: each `<part>` in
`Metadata/model_settings.config` carries
`<metadata key="extruder" value="N"/>`, which is a filament SLOT. The
principal picks the real spool per part later; nothing is ever painted.

## Anatomy forge.py emits (8 entries)

- `[Content_Types].xml`, `_rels/.rels`
- `3D/3dmodel.model` - one object (id 3), two components, identity
  transforms; `3D/_rels/3dmodel.model.rels`
- `3D/Objects/object_1.model` (body mesh), `object_2.model` (letter
  mesh) - each its own millimeter-unit model
- `Metadata/model_settings.config` - ONE object, TWO `<part>` entries
  (`<name>_body` extruder 1, `<name>_letter` extruder 2), each part
  carrying name/matrix/source ids/face_count/mesh_stat plus the
  `extruder` metadata INSIDE the part; plus `plate` and `assemble`
  blocks
- `Metadata/project_settings.config` - template embedded in forge.py
  (zlib+base64, expanded at render time); it carries a reference print
  profile, so printer/profile selection stays the principal's to confirm
  on open - normal for any third-party 3MF

Both meshes keep their source coordinates (no transforms), so every
bead has colour boundaries at identical layer heights (bottom groove,
top insert) -> identical per-layer colour maps across a batch -> prime
tower and multi-object printing stay valid. Hand-painted files lose
exactly this property.

Reference files, if still present on this machine:
`~/Downloads/frog_tape_dispenser_256.3mf` (working multi-part template:
extruder inside parts) and `~/Downloads/Painted_Letter_Beads.3mf`
(paint-workflow counter-example: dozens of single-part objects, all
extruder 1, colour stored as paint).

## Headless verification after any change to the 3MF path

Structural validation (zip entries, XML parse, two parts with extruders
inside them, triangle counts equal to source STL facets, size > 10KB)
runs inside `forge.py` on every render via `validate_bead_3mf`. After a
change, ALSO round-trip through the real consumer - run `BambuStudio`
from python `subprocess` with a timeout and a
`pkill -x BambuStudio` cleanup in `finally` (probe flags can fall
through to a GUI launch; never leave a GUI process on the principal's
desktop, and check `pgrep -x BambuStudio` afterwards):

1. `BambuStudio <file>.3mf --info` -> rc 0 and `manifold = yes`, envelope
   = the template's width x width x height. Gate on rc and manifold only:
   `number_of_parts` prints unrelated counts on 2.7.x (15 for a two-part
   bead), so treat it as advisory. (`--help` itself answers headless, rc 0.)
   The same advisory applies to `number_of_facets`: the slicer RECOUNTS
   facets through its own loader/repair pass and its total can land a few
   hundred below the file header's count even on an unmodified single
   mesh. A small positive header-minus-slicer delta is normal and is not
   merge damage - take the authoritative facet count from the file
   header (or `core/stl_probe.py`), and treat the slicer's number as
   liveness evidence only. Corrupt or truncated geometry still fails
   loudly: it will not report `manifold = yes`.
2. `BambuStudio <file>.3mf --export-3mf <out>.3mf` -> load + re-export
   through Bambu's own loader; unzip `<out>.3mf` and require
   `Metadata/model_settings.config` to still list both part names with
   extruders 1 and 2. Surviving the real consumer's load/save cycle is
   the acceptance test - passing our own writer proves nothing.

Flag gotcha: `--export-3mf` TAKES the filename as its argument.
`--output`/`--outputdir` are not the export target; an unrecognised flag
becomes a second positional input and the run dies with
`No such file: <path>`. Get the real flags from `--help` first.

## Multi-object plate (two or more beads on ONE plate)

Compose the plate yourself from the single-bead 3MFs; do NOT let the
slicer CLI merge them. On 2.7.1.57 every CLI merge route fails: merging
two inputs with `--export-3mf` writes a file its own loader SIGSEGVs on,
`--assemble` collapses every per-part extruder to 1 (letters would print
in the body colour), and `--export-png` hangs on multi-object inputs.
Compose instead, in python `zipfile`:

1. Mesh files: copy each bead's `object_1.model` (body) and
   `object_2.model` (letter) as `object_3.model`... for the 2nd+ bead,
   and renumber their root `<object id="...">` to match.
2. `3D/3dmodel.model`: keep the first assembly `<object>` (id 3), clone
   one assembly object per extra bead (fresh `p:UUID`s, components
   pointing at the renamed paths), one identity-transform
   `<item printable="1">` per object; update Title/Description.
3. `Metadata/model_settings.config`: clone each bead's `<object>` block
   (rename its `id=` to its assembly), keep ONE `<plate>` holding a
   `<model_instance>` per object with a unique `identify_id`, and one
   `<assemble_item>` per object.
4. `3D/_rels/3dmodel.model.rels`: one Relationship per mesh file;
   `[Content_Types].xml` unchanged (`Default Extension="model"` already
   covers the new files).
5. Placement: the loader honours mesh coordinates, not build-item
   transforms - bake each bead's X/Y shift into the mesh `<vertex>`
   values with identity transforms, or every object renders stacked at
   the origin. Pitch 130 mm (120 mm bead + 10 mm gap) inside the bed
   (256x256: first-row centres y=68, x=63 and 193; next row +130 in y).

Acceptance: structural parse (exactly one `<plate>`, N objects, every
body part `extruder` 1 and every letter part `extruder` 2 - identical
slots on every object are what keep the per-layer colour maps identical
and the prime tower valid), then `--info` rc 0 with `manifold = yes` per
object and per-object min/max showing the baked separation. Skip the
`--export-3mf` round-trip for multi-object files (its writer mangles
them); the GUI is the final consumer and shares the `--info` loader.
