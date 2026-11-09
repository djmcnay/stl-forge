// UNO Junior deck box — OpenSCAD replica of the SolidCraft model.
//
// Cards stand on their long edge; the top is open (card short side x deck
// thickness). A semicircular thumb arch runs through the front, back and
// bottom. The Artemis badge is engraved into the front face.
//
// Render with the repo pipeline:
//   python3 utilities/forge.py \
//       --presets projects/cards/presets.json \
//       --only uno-junior-box --out /tmp/cards-check
//
// All dimensions in millimetres.

/* [Cards] */
card_w = 56;          // UNO Junior short side
card_h = 87;          // UNO Junior long side
deck_t = 15;          // deck thickness

/* [Box] */
wall = 2;             // wall and floor thickness
fit = 0.6;            // total card clearance
entry_chamfer = 1;    // top-opening lead-in chamfer
thumb_arch_d = 17.5;  // thumb arch diameter (through front, back, bottom)

/* [Logo] */
logo_w = 45;          // visible Artemis artwork width
logo_depth = 0.8;     // engraving depth into the 2 mm front wall

/* [Render] */
$fn = 128;

include <artemis_logo.scad>

// Derived box dimensions.
inner_w = card_w + fit;
inner_d = deck_t + fit;
inner_h = card_h + fit;
outer_w = inner_w + 2 * wall;
outer_d = inner_d + 2 * wall;
outer_h = inner_h + wall;
thumb_arch_r = thumb_arch_d / 2;

// SolidCraft's SVG import scales the drawing's artwork to the requested
// width, not the SVG file's 45 mm viewBox. Match that here.
logo_scale = logo_w / ARTEMIS_LOGO_ARTWORK_W;

module chamfer_ring() {
    z0 = outer_h - entry_chamfer;
    difference() {
        hull() {
            translate([0, 0, z0])
                linear_extrude(height = 0.001)
                square([inner_w, inner_d], center = true);
            translate([0, 0, z0 + entry_chamfer])
                linear_extrude(height = 0.001)
                square([inner_w + 2 * entry_chamfer,
                        inner_d + 2 * entry_chamfer], center = true);
        }
        // Keep only the tapered ring around the opening.
        translate([0, 0, z0 - 1])
            linear_extrude(height = entry_chamfer + 2)
            square([inner_w, inner_d], center = true);
    }
}

module uno_junior_box() {
    difference() {
        // Outer block.
        translate([-outer_w / 2, -outer_d / 2, 0])
            cube([outer_w, outer_d, outer_h]);

        // Inner cavity, open at the top.
        translate([-inner_w / 2, -inner_d / 2, wall])
            cube([inner_w, inner_d, inner_h + 1]);

        // 1 mm entry chamfer around the inner top rim.
        chamfer_ring();

        // Semicircular thumb arch through the front, back and bottom.
        translate([0, -outer_d / 2 - 1, 0])
            rotate([-90, 0, 0])
            cylinder(h = outer_d + 2, r = thumb_arch_r);

        // Artemis badge engraved into the front face (-Y).
        // The 2D +Y maps to world +Z; the extrusion goes into the wall.
        translate([0, -outer_d / 2 + logo_depth, outer_h / 2])
            rotate([90, 0, 0])
            linear_extrude(height = logo_depth, convexity = 10)
            scale([logo_scale, logo_scale, 1])
            artemis_logo_2d();
    }
}

uno_junior_box();
