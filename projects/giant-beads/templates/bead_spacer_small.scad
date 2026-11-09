/*
    BEAD SPACER (SMALL / DOUGHNUT) - hole vertical
    ==============================================
    The small spacer is the doughnut of the family: a squat ring printed with
    the bore vertical. Looking down the hole it is a circle with a circular
    hole; the overall doughnut width is the letter bead's height, the throat is
    the same 20 mm as the letter bead, and the height is half the letter-bead
    height. All by default at width 120:

      - outer diameter = letter bead height = width/2 = 60 mm
      - hole throat    = 20 mm at its narrowest
      - overall height = letter bead height / 2 = width/4 = 30 mm
      - the hole mouth and the outer edge are both quarter-round fillets

    Curvature dial (0..1): controls the OUTER edge, and by default the hole
    fillet follows it exactly:
      0.0 = nearly flat washer: small inner and outer fillets
      0.5 = medium rounded doughnut (default)
      1.0 = very curvy: outer fillets meet at mid-height, semicircular rim

    `r_mouth` (mm) controls the hole mouth independently. The default
    -1 means "match the outer fillet", clamped only when the radial wall or
    half-height cannot fit it. With OD 60 and a 20 mm throat the radial wall
    is 20 mm, so at the default 0.5 both fillets are 9.375 mm and a 1.25 mm
    flat land remains between them. At curvature 1.0 the outer fillet is
    15 mm, leaving room for at most a 5 mm hole fillet; the auto value clamps
    to 5 mm. Set `r_mouth` to a positive mm value for independent control.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
// Letter-bead width reference (mm). The doughnut width = width/2 and its
// height = width/4.
width = 120;
// String-hole throat diameter (mm)
hole_diameter = 20;
// Outer-edge curvature dial, 0..1: flat washer -> full doughnut.
curvature = 0.5;
// Hole-mouth fillet radius (mm). -1 = match the outer fillet automatically.
r_mouth = -1;
// Family parameters retained for symmetry with the other bead templates.
bore_fillet_radius = width / 8;   // unused by the doughnut body
fillet_radius = width / 12;       // unused by the doughnut body

// ---- derived dimensions ----------------------------------------------
letter_height = width / 2;             // 60 at width 120
outer_diameter = letter_height;        // doughnut width = 60
height = letter_height / 2;            // doughnut height = 30
H = height;
R_out = outer_diameter / 2;            // 30
R_throat = hole_diameter / 2;          // 10
// Outer edge fillet: H/8 at curvature 0, H/2 at curvature 1.
outer_fillet = (H / 2) * (0.25 + 0.75 * curvature);
// Largest mouth fillet that still fits between the bore and outer fillet.
r_mouth_max = max(0, min(H / 2, R_out - R_throat - outer_fillet));
r_mouth_eff = min(r_mouth < 0 ? outer_fillet : r_mouth, r_mouth_max);
flat_land = R_out - R_throat - outer_fillet - r_mouth_eff;
side_len = H - 2 * outer_fillet;
n_edge = 24;

assert(width > 0, "width must be positive");
assert(hole_diameter > 0, "hole_diameter must be positive");
assert(R_throat < R_out, "hole throat must fit inside the doughnut");
assert(curvature >= 0 && curvature <= 1, "curvature must be in 0..1");
assert(outer_fillet > 0 && outer_fillet <= H / 2 + 1e-9,
       "outer_fillet must be > 0 and <= H/2");
assert(r_mouth_eff > 0,
       "r_mouth collapsed: no room for an inner fillet");
assert(flat_land >= -1e-6,
       "inner and outer fillets overlap: reduce r_mouth or curvature");

echo(bead_spacer_small_outer_dia = outer_diameter,
     bead_spacer_small_height = H,
     bead_spacer_small_hole_dia = hole_diameter,
     bead_spacer_small_curvature = curvature,
     bead_spacer_small_outer_fillet = outer_fillet,
     bead_spacer_small_r_mouth_max = r_mouth_max,
     bead_spacer_small_r_mouth_eff = r_mouth_eff,
     bead_spacer_small_flat_land = flat_land);

// Smooth revolved surfaces.
$fn = 128;

// ---- cross-section: rounded ring with filleted mouths ------------------
// Ring profile in the (r, z) half-plane. The inner boundary is the vertical
// bore between two concave hole-mouth fillets; the outer boundary is the
// flat bottom/top land, two convex outer fillets, and a vertical outer band.
inner_bottom_arc = [
    for (i = [1 : n_edge])
        let(a = 180 + 90 * i / n_edge)
        [R_throat + r_mouth_eff + r_mouth_eff * cos(a),
         r_mouth_eff + r_mouth_eff * sin(a)]
];
outer_bottom_arc = [
    for (i = [1 : n_edge])
        let(a = 270 + 90 * i / n_edge)
        [R_out - outer_fillet + outer_fillet * cos(a),
         outer_fillet + outer_fillet * sin(a)]
];
outer_top_arc = [
    for (i = [1 : n_edge])
        let(a = 90 * i / n_edge)
        [R_out - outer_fillet + outer_fillet * cos(a),
         H - outer_fillet + outer_fillet * sin(a)]
];
inner_top_arc = [
    for (i = [1 : n_edge])
        let(a = 90 + 90 * i / n_edge)
        [R_throat + r_mouth_eff + r_mouth_eff * cos(a),
         H - r_mouth_eff + r_mouth_eff * sin(a)]
];
profile = concat(
    [[R_throat, r_mouth_eff]],
    inner_bottom_arc,
    (flat_land > 1e-6 ? [[R_out - outer_fillet, 0]] : []),
    outer_bottom_arc,
    (side_len > 1e-6 ? [[R_out, H - outer_fillet]] : []),
    outer_top_arc,
    (flat_land > 1e-6 ? [[R_throat + r_mouth_eff, H]] : []),
    inner_top_arc
);

module spacer_solid() {
    rotate_extrude(angle = 360)
        polygon(profile);
}

spacer_solid();
