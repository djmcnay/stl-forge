/*
    BEAD SPACER (WIDE) - tapered barrel, hole vertical
    ==================================================
    A wide spacer bead for the giant-bead family. Unlike the letter/heart/star
    beads, it is printed with the string hole VERTICAL (the hole axis is Z and
    the bottom face sits on the build plate), so the two mouths are the top and
    bottom ends of the barrel rather than through the side.

    Form (defaults, width 120):
      - overall height = width = 120 mm (the letter bead's width)
      - widest point at mid-height: diameter = width = 120 mm (z = 60, which
        is also the letter bead's height)
      - straight taper from the face/base at each end out to the equator
      - top/bottom face width = the letter bead's mouth opening where the
        fillet starts: diameter = 2 * (R_throat + r_mouth) = 33.33 mm
      - hole throat = 20 mm, same as the letter bead, with the same revolved
        fillet-well mouth at both ends (valid here because each end wall is a
        flat plane perpendicular to the hole axis)

    The mouth dial deliberately uses the letter bead's reference height
    (width / 2), not this barrel's taller height: "the hole should be the
    same size by default" means the same throat and same r_mouth as the
    letter bead. The face/base radius is then exactly the outer edge of that
    mouth well, per the letter-bead hole protocol.

    Print orientation: hole vertical, bottom face on the plate. The taper is
    ~34 deg from vertical at defaults, inside the usual 45 deg support-free
    overhang limit.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
// Enclosing diameter of the barrel at its widest point (mm)
width = 120;
// Overall height along the hole axis (mm): the wide spacer is as tall as the
// letter bead is wide.
height = width;
// String-hole throat diameter at the centre plane (mm)
hole_diameter = 20;
// Flare arc radius (mm): family rule width / 8; retained, unused by the mouth.
bore_fillet_radius = width / 8;
// Face fillet radius (mm): family rule width / 12. Retained for family
// parameter symmetry; the spacer's tapered face meets the cone directly.
fillet_radius = width / 12;
// Derived hole values
R_throat = hole_diameter / 2;
extra = 5;                     // mm bore overshoot past both faces

// ---- mouth dial: same hole as the letter bead --------------------------
// The letter bead's dial is evaluated at its own height (width / 2). Keeping
// that reference height here means r_mouth is unchanged by the spacer's
// taller body, so the hole really is the same size by default.
letter_height = width / 2;
r_mouth_max = (letter_height / 2.25) - (fillet_radius + R_throat);
r_mouth = max(0.5, min(0.5 * hole_diameter, r_mouth_max));

// ---- derived body dimensions ------------------------------------------
R_max = width / 2;             // equator radius (widest point)
R_face = R_throat + r_mouth;   // face/base radius = mouth well outer edge
H = height;

assert(width > 0, "width must be positive");
assert(height > 0, "height must be positive");
assert(hole_diameter < 2 * R_face, "hole throat must fit inside the face");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(r_mouth > 0, "mouth fillet collapsed: height too small for this dial set");
assert(R_face <= R_max, "face radius must not exceed the equator radius");

// Smooth bore surfaces; the tapered body is a revolved polygon and follows
// $fn as well.
$fn = 128;

// ---- body: double cone with flat ends ---------------------------------
// Profile in the (r, z) half-plane. The widest point is a deliberate sharp
// equator at z = H/2; the top/bottom faces are flat disks out to R_face.
profile = [
    [0, 0],
    [R_face, 0],
    [R_max, H / 2],
    [R_face, H],
    [0, H]
];

module spacer_solid() {
    rotate_extrude(angle = 360)
        polygon(profile);
}

// ---- string hole: same revolved fillet-well as the letter bead ---------
// bead_string_hole_well() is authored along X with the hole centre at the
// origin; rotate it 90 deg about Y to put the hole on Z, then lift to the
// barrel mid-height. hole_entry_x = H/2 places the two wall planes exactly
// at z = 0 and z = H.
module string_hole() {
    translate([0, 0, H / 2])
        rotate([0, 90, 0])
            bead_string_hole_well(
                hole_entry_x = H / 2,
                R_throat = R_throat,
                r_mouth = r_mouth,
                extra = extra);
}

echo(bead_spacer_wide_r_mouth = r_mouth,
     bead_spacer_wide_face_r = R_face,
     bead_spacer_wide_width = width,
     bead_spacer_wide_height = height);

difference() {
    spacer_solid();
    string_hole();
}
