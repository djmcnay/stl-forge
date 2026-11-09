/*
    BEAD SPACER (WIDE) - tapered barrel, hole vertical
    ==================================================
    A wide spacer bead for the giant-bead family. Unlike the letter/heart/star
    beads, it is printed with the string hole VERTICAL (the hole axis is Z and
    the bottom face sits on the build plate), so the bore runs straight through
    the top and bottom faces.

    Form (defaults, width 120):
      - overall height = width = 120 mm (the letter bead's width)
      - widest point at mid-height: diameter = letter bead height = width/2
        = 60 mm (z = 60, which is also the letter bead's height). The spacer
        is the letter bead's 120 x 60 proportions turned upright.
      - top/bottom face diameter = letter bead height - 2 * letter face fillet
        = (width/2) - 2*(width/12) = width/3 = 40 mm
      - hole throat = 20 mm, straight bore, NO mouth fillet yet
      - the side is a smooth barrel, not a straight bicone. `curvature` is the
        exponent in r(z) = R_face + (R_max - R_face)*sin(pi*z/H)^curvature:
        1.0 = sine barrel, 1.5 = fuller barrel with vertical ends (default),
        2.0 = more rounded. The widest point is smooth for every value >= 1.

    Print orientation: hole vertical, bottom face on the plate. The equatorial
    bulge is only 10 mm over a 60 mm half-height (roughly 14 deg maximum
    overhang), so the whole body prints support-free. The plain bore also
    removes the top-mouth countersink overhang.

    The face formula deliberately uses the LETTER bead's height (width/2) and
    face fillet (width/12), not the spacer's taller height.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
// Letter-bead width reference (mm). The spacer height = width and its
// equatorial diameter = width/2 (the letter bead's height).
width = 120;
// Overall height along the hole axis (mm): the wide spacer is as tall as the
// letter bead is wide.
height = width;
// String-hole throat diameter (mm)
hole_diameter = 20;
// Flare arc radius (mm): family rule width / 8; retained, unused by the plain
// bore.
bore_fillet_radius = width / 8;
// Face fillet radius (mm): family rule width / 12. Here it is used as the
// letter bead's face-fillet value in the face-diameter formula below.
fillet_radius = width / 12;
// Barrel curvature exponent: 1 = sine barrel, 1.5 = fuller barrel with
// vertical ends, 2 = more rounded. Must be >= 1 so the widest point is smooth
// and the ends do not cusp.
curvature = 1.5;

// ---- derived body dimensions ------------------------------------------
H = height;
letter_height = width / 2;     // the letter bead's height
R_max = letter_height / 2;     // equator radius = half the letter bead height
face_diameter = letter_height - 2 * fillet_radius;
R_face = face_diameter / 2;    // top/bottom face radius
R_throat = hole_diameter / 2;
extra = 5;                     // mm bore overshoot past both faces

assert(width > 0, "width must be positive");
assert(height > 0, "height must be positive");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(curvature >= 1, "curvature must be >= 1 (below 1 the ends cusp)");
assert(R_face >= R_throat, "face diameter must be at least the hole diameter");
assert(R_face <= R_max, "face radius must not exceed the equator radius");

// Smooth revolved surfaces.
$fn = 128;

// ---- body: smooth barrel with flat ends -------------------------------
// Radius as a function of height. sin(180*z/H) is 0 at the faces, 1 at the
// equator; the exponent controls how full the barrel is. At curvature > 1 the
// side is vertical at both the faces and the equator, and the widest point is
// smooth (dr/dz = 0).
function barrel_r(z) =
    R_face + (R_max - R_face) * pow(sin(180 * z / H), curvature);

n_profile = 96;                // profile samples over the full height
profile = concat(
    [[0, 0]],
    [for (i = [0 : n_profile]) let(z = H * i / n_profile) [barrel_r(z), z]],
    [[0, H]]
);

module spacer_solid() {
    rotate_extrude(angle = 360)
        polygon(profile);
}

// ---- string hole: straight vertical bore ------------------------------
// bead_string_hole_plain() is authored along X with the cylinder centred at
// the origin; rotate it 90 deg about Y to put the bore on Z, then lift to the
// barrel mid-height. hole_len = H/2 + extra clears both faces.
module string_hole() {
    translate([0, 0, H / 2])
        rotate([0, 90, 0])
            bead_string_hole_plain(
                R_throat = R_throat,
                hole_len = H / 2 + extra);
}

echo(bead_spacer_wide_face_dia = face_diameter,
     bead_spacer_wide_face_r = R_face,
     bead_spacer_wide_curvature = curvature,
     bead_spacer_wide_width = width,
     bead_spacer_wide_height = height);

difference() {
    spacer_solid();
    string_hole();
}
