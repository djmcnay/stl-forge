/*
    BEAD SPACER (SMALL / DOUGHNUT) - hole vertical
    ==============================================
    The small spacer is the doughnut of the family: a squat ring printed with
    the bore vertical. Looking down the hole it is a circle with a circular
    hole; the overall doughnut width is the letter bead's height, the throat is
    the same 20 mm as the letter bead, and the height is half the letter-bead
    height. All by default at width 120:

      - outer diameter = letter bead height = width/2 = 60 mm
      - hole throat    = 20 mm (straight plain bore, no mouth fillet yet)
      - overall height = letter bead height / 2 = width/4 = 30 mm
      - outer edge     = quarter-round fillet controlled by `curvature`

    Curvature dial (0..1):
      0.0 = nearly flat washer: a small outer fillet (H/8)
      1.0 = fully rounded doughnut: the two outer fillets meet at mid-height
            and the outer profile is a semicircle (fillet radius H/2)
      The default 0.75 leaves a short vertical outer band, so it reads as a
      doughnut but still has a printable/grippable side.

    The bore is a plain vertical cylinder; the "narrowest" hole is exactly the
    letter bead throat. A mouth fillet can be added later without changing the
    doughnut body.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
// Letter-bead width reference (mm). The doughnut width = width/2 and its
// height = width/4.
width = 120;
// String-hole throat diameter (mm)
hole_diameter = 20;
// Outer-edge curvature dial, 0..1: flat washer -> full doughnut.
curvature = 0.75;
// Family parameters retained for symmetry with the other bead templates.
bore_fillet_radius = width / 8;   // unused by the plain bore
fillet_radius = width / 12;       // unused by the doughnut body

// ---- derived dimensions ----------------------------------------------
letter_height = width / 2;             // 60 at width 120
outer_diameter = letter_height;        // doughnut width = 60
H = letter_height / 2;                 // doughnut height = 30
R_out = outer_diameter / 2;            // 30
R_in = hole_diameter / 2;              // 10
// Outer edge fillet: H/8 at curvature 0, H/2 (semicircular rim) at 1.
outer_fillet = (H / 2) * (0.25 + 0.75 * curvature);
side_len = H - 2 * outer_fillet;
n_edge = 24;

assert(width > 0, "width must be positive");
assert(hole_diameter > 0, "hole_diameter must be positive");
assert(R_in < R_out, "hole throat must fit inside the doughnut");
assert(curvature >= 0 && curvature <= 1, "curvature must be in 0..1");
assert(outer_fillet > 0 && outer_fillet <= H / 2 + 1e-9,
       "outer_fillet must be > 0 and <= H/2");
assert(R_out - outer_fillet > R_in,
       "outer fillet leaves no flat top/bottom face around the bore");

// Smooth revolved surfaces.
$fn = 128;

// ---- cross-section: rounded outer rectangle, plain bore ----------------
// Ring profile in the (r, z) half-plane. The inner boundary is the vertical
// bore; the outer boundary is a flat bottom face, a bottom quarter-round, a
// short vertical outer band (when side_len > 0), a top quarter-round, and a
// flat top face.
bottom_arc = [
    for (i = [1 : n_edge])
        let(a = -90 + 90 * i / n_edge)
        [R_out - outer_fillet + outer_fillet * cos(a),
         outer_fillet + outer_fillet * sin(a)]
];
top_start = side_len > 1e-6 ? 0 : 1;
top_arc = [
    for (i = [top_start : n_edge])
        let(a = 90 * i / n_edge)
        [R_out - outer_fillet + outer_fillet * cos(a),
         H - outer_fillet + outer_fillet * sin(a)]
];
profile = concat(
    [[R_in, 0], [R_out - outer_fillet, 0]],
    bottom_arc,
    top_arc,
    [[R_in, H]]
);

module spacer_solid() {
    rotate_extrude(angle = 360)
        polygon(profile);
}

echo(bead_spacer_small_outer_dia = outer_diameter,
     bead_spacer_small_height = H,
     bead_spacer_small_hole_dia = hole_diameter,
     bead_spacer_small_curvature = curvature,
     bead_spacer_small_outer_fillet = outer_fillet);

spacer_solid();
