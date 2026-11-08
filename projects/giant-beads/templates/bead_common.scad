// bead_common.scad - shared string-hole mouths for the bead template family.
//
// Plain hole (bead_string_hole_plain): star/flower use this.
// Fillet-well (bead_string_hole_well): letter bead (bead.scad) and
// heart (bead_heart.scad) — the smooth G1 mouth from the letter bead
// example, ported verbatim. Star keeps the plain bore: the well revolve
// grazes its oblique flank and fins.
//
// Coordinate frame: the hole axis is X, the bead centre sits at the origin
// and the bore is centred on x = 0. The caller supplies the z lift (each
// template centres the hole on its own face plane, e.g. z = height / 2).
// The caller also supplies every local value (hole_entry_x, hole_len, ...)
// exactly as that template derives it; the per-template derivation rules
// stay in the templates - only the geometry cut is shared here.

// ---- bead_string_hole_plain(): just a hole ---------------------------------
//
// A straight throat bore along X and nothing else — no scoop, no ball,
// no fillet, no well. The caller passes the bore radius and a
// half-length that clears both walls; everything else about the mouth
// belongs to templates that opt into a fancier cut.
module bead_string_hole_plain(
    R_throat,      // throat bore radius = hole_diameter / 2
    hole_len       // straight-bore half-length: clears both walls
) {
    rotate([0, 90, 0])
        cylinder(h = 2 * hole_len, r = R_throat, center = true);
}

// ---- bead_string_hole_well(): the fillet-well mouth (shared) ----------------
//
// PROVENANCE - SolidCraft rebuild (6 Nov 2026): David settled the definition
// of a correct mouth there - the wall should run tangentially into the bore
// like a QUARTER-ROUND FILLET, not a sphere bowl - and this module ports that
// construction to OpenSCAD. Target of record for the call from bead.scad at
// family defaults: volume 610,079.46 mm3 / 243 faces (SolidCraft rebuild,
// replicated by the steady-state OpenSCAD render up to tessellation). Dial
// rule that fixed the well radius (empirical, family-wide):
//     r_mouth_max = (H / 2.25) - (r_fillet + R_throat)  (safe ceiling)
//     r_mouth     = min(0.5 * d_throat, r_mouth_max)     (softness floor)
// giving 6.667 at H=60, r_fillet=W/12=10, d_throat=20.
//
// Wall-normal constraint (read before calling from a new template):
// 1. This cut is only valid where the local wall normal at the mouth is
//    exactly the hole axis direction, i.e. [1, 0] in the template frame.
// 2. The plain cylinder bead (bead.scad) is that case: its wall at
//    x = +/- width/2, y = 0 is a plane perpendicular to the hole axis, so the
//    revolved crater meets it in a full circle of radius R_throat + r_mouth.
// 3. On an oblique or curved wall (star/heart/flower flanks) the revolved
//    crater would touch the wall at a grazing point and wedge a fin - those
//    templates use the plain bore and must NOT switch to this one
//    (tried 6 Nov 2026: the revolved well leaves a vertical fin on the star
//    flank, exactly as predicted).
// 4. The caller also passes hole_entry_x as the exact axial position of the
//    wall plane itself, not of a slanted crossing halfway up the flank.
//
// Geometry contract (the union of, in the caller's frame):
//   1. a quarter-round well crater at the +x mouth, revolved about the hole
//      axis: profile arc of radius r_mouth centred at (R_throat + r_mouth,
//      hole_entry_x - r_mouth) in the (radial r, axial t) half-plane, sampled
//      from -90 deg to 0 deg inclusive so it runs from the bore wall
//      (R_throat, hole_entry_x - r_mouth) with slope 0 (G1 into the bore) to
//      the flat wall plane (R_throat + r_mouth, hole_entry_x) with vertical
//      slope (G1 into the wall), then closed outward through the wall plane
//      (hole_entry_x + extra) and down the axis to r = 0, so the subtraction
//      passes cleanly through the face; extra (default 2 mm) only overshoots,
//      it adds nothing inside the bead, exactly like the old bore overshoot,
//   2. the mirrored crater at the -x mouth: one call cuts both entrances
//      (same convention as bead_string_hole, whose -x mouth was the y-mirror
//      of its +x one),
//   3. the straight throat bore along X, radius R_throat, centred on the
//      caller's hole axis and longer than 2 * hole_entry_x (hole_entry_x +
//      extra each way) so it overshoots both walls as before.
module bead_string_hole_well(hole_entry_x, R_throat, r_mouth, extra = 2) {
    assert(r_mouth > 0, "fillet-well radius must be positive (dial r_mouth_max = (H / 2.25) - (r_fillet + R_throat) collapsed)");
    assert(hole_entry_x > r_mouth, "hole_entry_x must exceed r_mouth so the crater arc fits inside the wall");

    // Arc centre in the (r, t) profile half-plane: r radial from the hole
    // axis, t axial (polygon y; it lands on the +X axis after the rotate).
    ac_r = R_throat + r_mouth;    // radial component
    ac_t = hole_entry_x - r_mouth; // axial component

    // Crater profile polygon (CCW, non-self-intersecting). The arc is
    // sampled BY ANGLE with the sin/cos swapped parametrisation
    //     r = ac_r + r_mouth * sin(a), t = ac_t + r_mouth * cos(a),
    // walking a = -90 .. 0 inclusive so the points run monotonically from
    // (R_throat, ac_t) to (ac_r, hole_entry_x) with no wrap-around kink;
    // the closing legs then punch out through the wall plane (hole_entry_x +
    // extra) and drop down the axis (r = 0) and back across to the arc start,
    // so the loop closes cleanly with the two bracket legs.
    crater_profile = concat(
        [for (a = [-90 : 2 : 0])
            [ac_r + r_mouth * sin(a), ac_t + r_mouth * cos(a)]],
        [
            [R_throat + r_mouth, hole_entry_x + extra],
            [0, hole_entry_x + extra],
            [0, hole_entry_x - r_mouth]
        ]
    );

    union() {
        // straight throat bore along X through both walls (the old call's
        // hole_len folded into hole_entry_x + extra)
        rotate([0, 90, 0])
            cylinder(h = 2 * (hole_entry_x + extra), r = R_throat, center = true);
        // quarter-round well crater at the +x mouth, revolved about the hole axis
        rotate([0, 90, 0])
            rotate_extrude(angle = 360)
                polygon(crater_profile);
        // mirrored well crater at the -x mouth (axial mirror, t -> -t)
        rotate([0, 90, 0])
            mirror([0, 0, 1])
                rotate_extrude(angle = 360)
                    polygon(crater_profile);
    }
}
