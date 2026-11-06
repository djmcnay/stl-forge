// Parametric open-top storage box.
// Printer-ready orientation: z=0 is the bottom face.
// Outer walls have vertical rounded corners via 2D offset + extrude (fast on CGAL).

// Outer dimension in X (mm)
width = 120;
// Outer dimension in Y (mm)
depth = 80;
// Outer dimension in Z (mm)
height = 30;
// Vertical wall thickness (mm)
wall = 2.4;
// Base/floor thickness (mm)
floor = 2.4;
// Outer vertical corner radius (mm)
corner_r = 5;
// Number of cells in X (divider grid)
div_n = 3;
// Number of cells in Y (divider grid)
div_m = 2;

// Derived interior dimensions.
inner_w = width - 2 * wall;
inner_d = depth - 2 * wall;
inner_h = height - floor;
// Cavity corner radius keeps wall thickness ~uniform at corners.
cav_r = max(corner_r - wall, 0.5);
// Clamp helper: inner 2D base sizes must stay positive for offset().
outer_base_x = max(width - 2 * corner_r, 0.1);
outer_base_y = max(depth - 2 * corner_r, 0.1);
cavity_base_x = max(inner_w - 2 * cav_r, 0.1);
cavity_base_y = max(inner_d - 2 * cav_r, 0.1);

// 2D rounded rectangle centred on origin, built with offset (no minkowski/hull).
module rounded_rect_2d(w, d, r, base_x, base_y) {
    offset(r = r)
        square([base_x, base_y], center = true);
}

// Outer solid: extruded rounded rectangle from z=0 to z=height.
module outer_solid() {
    linear_extrude(height = height)
        rounded_rect_2d(width, depth, corner_r, outer_base_x, outer_base_y);
}

// Cavity solid to subtract: leaves `wall` side walls and `floor` base.
// Extended 1mm above the top so the box is guaranteed open.
module cavity_solid() {
    translate([0, 0, floor])
        linear_extrude(height = inner_h + 1)
            rounded_rect_2d(inner_w, inner_d, cav_r, cavity_base_x, cavity_base_y);
}

// Divider positions: evenly spaced so the cavity splits into div_n x div_m cells.
module dividers() {
    // Walls perpendicular to X (span full inner depth). Count: div_n - 1.
    for (i = [1 : div_n - 1]) {
        x = -inner_w / 2 + i * inner_w / div_n;
        translate([x, 0, floor + inner_h / 2])
            cube([wall, inner_d, inner_h], center = true);
    }
    // Walls perpendicular to Y (span full inner width). Count: div_m - 1.
    for (j = [1 : div_m - 1]) {
        y = -inner_d / 2 + j * inner_d / div_m;
        translate([0, y, floor + inner_h / 2])
            cube([inner_w, wall, inner_h], center = true);
    }
}

// Final part: outer minus cavity, plus internal divider grid.
difference() {
    outer_solid();
    cavity_solid();
}
dividers();
