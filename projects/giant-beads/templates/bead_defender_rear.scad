/*
    DEFENDER 90 REAR BEAD - first pass.
    ==================================
    Rear silhouette of a Land Rover Defender 90 with the spare wheel,
    rear door, lights, bumper and wheel arches etched into both flat
    faces.  The body is extruded with a gentle quarter-round face/bottom
    fillet.

    width        vehicle width (mm)
    height       bead thickness (30 mm)
    fillet_radius  edge fillet (mm), deliberately gentle
    detail_relief  scales etch depth
*/
use <bead_defender_common.scad>

width = 120;
height = 30;
hole_diameter = 20;
bore_fillet_radius = width / 8;    // retained family name; plain bore
fillet_radius = 4;
detail_relief = 1.0;
R_throat = hole_diameter / 2;
extra = 5;
$fn = 128;

assert(width > 0);
assert(hole_diameter < width);
assert(fillet_radius > 0 && fillet_radius < height / 2);
assert(detail_relief > 0);

S = width / 120;
H = height;
c = fillet_radius;
etch_depth = 0.6 * detail_relief;
etch_w = 0.8;

// ---- rear silhouette (120 x 130 master coordinates) -------------------
body_pts = [
    [-60, -45], [-60, 50], [-54, 60], [-45, 64],
    [45, 64], [54, 60], [60, 50], [60, -45],
    [52, -52], [40, -52], [-40, -52], [-52, -52]
];
rear_tyres = [[-43, -52, 12], [43, -52, 12]];

function sc(pts) = [for (p = pts) [p[0] * S, p[1] * S]];
function pxy(x, y) = [x * S, y * S];

module outer_2d() {
    union() {
        polygon(points = sc(body_pts));
        for (t = rear_tyres)
            translate(pxy(t[0], t[1])) circle(r = t[2] * S);
    }
}

module wheel_arch(cx, cy) {
    etch_arc(pxy(cx, cy), 14.0 * S, 0, 180, etch_w);
    etch_arc(pxy(cx, cy), 10.5 * S, 15, 165, etch_w);
}

module spare_wheel() {
    ctr = pxy(0, -1);
    etch_ring(ctr, 24.0 * S, etch_w);
    etch_ring(ctr, 17.5 * S, etch_w);
    etch_ring(ctr, 4.5 * S, etch_w);
    etch_spokes(ctr, 4.5 * S, 17.5 * S, 6, 0, etch_w);
    for (i = [0 : 5])
        etch_ring(ctr + [13.0 * S * cos(30 + 60 * i),
                         13.0 * S * sin(30 + 60 * i)], 1.1 * S, 0.55);
    for (i = [0 : 11])
        etch_line(ctr + [21.0 * S * cos(15 + 30 * i),
                         21.0 * S * sin(15 + 30 * i)],
                  ctr + [23.5 * S * cos(15 + 30 * i),
                         23.5 * S * sin(15 + 30 * i)], etch_w);
}

module etch_2d() {
    // rear door, window and side windows
    etch_rect(-28 * S, -38 * S, 28 * S, 35 * S, etch_w);
    etch_rect(-21 * S, 8 * S, 21 * S, 30 * S, etch_w);
    etch_rect(-55 * S, 22 * S, -46 * S, 35 * S, etch_w);
    etch_rect(46 * S, 22 * S, 55 * S, 35 * S, etch_w);
    etch_line(pxy(-28, 8), pxy(28, 8), etch_w);
    etch_line(pxy(-28, -38), pxy(28, -38), etch_w);
    // hinges and handle
    for (y = [-20, 5, 25])
        etch_rect(-24 * S, y * S, -20 * S, (y + 4) * S, etch_w);
    etch_rect(-4 * S, 2 * S, 8 * S, 4 * S, etch_w);
    // wheel arches and tyre treads
    wheel_arch(-43, -52);
    wheel_arch(43, -52);
    for (t = rear_tyres)
        for (i = [0 : 9])
            etch_line(
                pxy(t[0] + 10.5 * cos(20 + 20 * i),
                    t[1] + 10.5 * sin(20 + 20 * i)),
                pxy(t[0] + 11.5 * cos(20 + 20 * i),
                    t[1] + 11.5 * sin(20 + 20 * i)), etch_w);
    spare_wheel();
    // tail lights, bumper, tow hitch, mudflaps
    etch_rect(-55 * S, -30 * S, -47 * S, -8 * S, etch_w);
    etch_rect(47 * S, -30 * S, 55 * S, -8 * S, etch_w);
    etch_line(pxy(-56, -43), pxy(56, -43), etch_w);
    etch_line(pxy(-56, -48), pxy(56, -48), etch_w);
    etch_line(pxy(-8, -48), pxy(-8, -54), etch_w);
    etch_line(pxy(8, -48), pxy(8, -54), etch_w);
    etch_arc(pxy(0, -54), 5 * S, 200, 340, etch_w);
    etch_rect(-50 * S, -48 * S, -42 * S, -40 * S, etch_w);
    etch_rect(42 * S, -48 * S, 50 * S, -40 * S, etch_w);
    // body crease (split around the spare) and roof gutter
    etch_line(pxy(-58, -5), pxy(-29, -5), etch_w);
    etch_line(pxy(29, -5), pxy(58, -5), etch_w);
    etch_line(pxy(-45, 59), pxy(45, 59), etch_w);
}

// ---- filleted body ------------------------------------------------------
n_fillet = 128;
fillet_u = [for (i = [0 : n_fillet])
                c - c * cos(-90 + 90 * i / n_fillet)];
fillet_z = [for (i = [0 : n_fillet])
                c + c * sin(-90 + 90 * i / n_fillet)];

module body_solid() {
    union() {
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z[i]])
                linear_extrude(height = fillet_z[i + 1] - fillet_z[i] + 0.005)
                    offset(r = -fillet_u[i]) outer_2d();
        if (H - 2 * c > 0.001)
            translate([0, 0, c])
                linear_extrude(height = H - 2 * c) outer_2d();
        for (k = [0 : n_fillet - 1])
            translate([0, 0, H - fillet_z[k + 1]])
                linear_extrude(height = fillet_z[k + 1] - fillet_z[k] + 0.005)
                    offset(r = -fillet_u[k]) outer_2d();
    }
}

module bead() {
    difference() {
        body_solid();
        translate([0, 0, H / 2])
            rotate([0, 90, 0])
                cylinder(h = width + 2 * extra, r = R_throat, center = true);
        translate([0, 0, H - etch_depth])
            linear_extrude(height = etch_depth + 0.5) etch_2d();
        translate([0, 0, -0.5])
            linear_extrude(height = etch_depth + 0.5) etch_2d();
    }
}

bead();
