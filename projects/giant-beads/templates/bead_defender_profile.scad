/*
    DEFENDER 90 PROFILE BEAD - first pass.
    =====================================
    Side silhouette of a Land Rover Defender 90, extruded with the family's
    quarter-round face/bottom fillet (gently reduced radius).  Windows,
    doors, wheel arches, steel wheels, spare wheel, grille and trim are
    shallow etch grooves on both flat faces.

    width        vehicle length (mm)
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

S = width / 120;                   // silhouette scale
H = height;
c = fillet_radius;
etch_depth = 0.6 * detail_relief;
etch_w = 0.8;

// ---- side silhouette (120 x 60 master coordinates) -------------------
body_pts = [
    [-60, -22], [-60, -14], [-57, -12], [-57, 2],
    [-44, 7], [-36, 24], [-35, 27], [40, 27],
    [47, 29], [47, -15], [44, -16], [-54, -16], [-57, -15]
];
front_wheel = [-36, -18.5, 11.5];
rear_wheel  = [ 36, -18.5, 11.5];
spare       = [ 50,  -2.0, 9.5];

function sc(pts) = [for (p = pts) [p[0] * S, p[1] * S]];
function pxy(x, y) = [x * S, y * S];

module outer_2d() {
    union() {
        polygon(points = sc(body_pts));
        translate(pxy(front_wheel[0], front_wheel[1]))
            circle(r = front_wheel[2] * S);
        translate(pxy(rear_wheel[0], rear_wheel[1]))
            circle(r = rear_wheel[2] * S);
        translate(pxy(spare[0], spare[1]))
            circle(r = spare[2] * S);
    }
}

// ---- etched side details ------------------------------------------------
module wheel_details(cx, cy, rr) {
    ctr = pxy(cx, cy);
    rrim = 7.2 * S;
    etch_ring(ctr, 10.4 * S, etch_w);
    etch_ring(ctr, rrim, etch_w);
    etch_ring(ctr, 4.8 * S, etch_w);
    etch_ring(ctr, 1.5 * S, etch_w);
    etch_spokes(ctr, 1.5 * S, rrim, 5, 18, etch_w);
    for (i = [0 : 4])
        etch_ring(ctr + [5.8 * S * cos(18 + 72 * i),
                         5.8 * S * sin(18 + 72 * i)], 0.55 * S, 0.5);
}

module etch_2d() {
    // window openings
    etch_loop([pxy(-43, 9), pxy(-35, 23), pxy(-33, 23), pxy(-41, 9)], etch_w);
    etch_loop([pxy(-32, 11), pxy(-9, 11), pxy(-9, 22), pxy(-30, 22)], etch_w);
    etch_loop([pxy(-5, 12), pxy(30, 12), pxy(30, 23), pxy(-5, 23)], etch_w);
    etch_line(pxy(12, 12), pxy(12, 23), etch_w);
    // alpine roof windows
    etch_rect(2 * S, 23.4 * S, 10 * S, 24.7 * S, 0.65);
    etch_rect(14 * S, 23.4 * S, 22 * S, 24.7 * S, 0.65);
    // doors / body seams / handles
    etch_line(pxy(-33, -10), pxy(-33, 13), etch_w);
    etch_line(pxy(-9, -10), pxy(-9, 12), etch_w);
    etch_line(pxy(-33, -10), pxy(-9, -10), etch_w);
    etch_line(pxy(-9, -10), pxy(38, -10), etch_w);
    etch_line(pxy(38, -10), pxy(38, 4), etch_w);
    etch_line(pxy(-54, -3), pxy(45, -3), etch_w);
    etch_rect(-24 * S, 12 * S, -19 * S, 14 * S, etch_w);
    etch_rect(0, 12 * S, 5 * S, 14 * S, etch_w);
    etch_ring(pxy(40, 1), 1.4 * S, etch_w);
    // wheel arches and wheels
    etch_arc(pxy(front_wheel[0], front_wheel[1]), 13.0 * S, 10, 170, etch_w);
    etch_arc(pxy(rear_wheel[0], rear_wheel[1]), 13.0 * S, 10, 170, etch_w);
    wheel_details(front_wheel[0], front_wheel[1], front_wheel[2]);
    wheel_details(rear_wheel[0], rear_wheel[1], rear_wheel[2]);
    // spare wheel
    sctr = pxy(spare[0], spare[1]);
    etch_ring(sctr, 8.4 * S, etch_w);
    etch_ring(sctr, 6.2 * S, etch_w);
    etch_ring(sctr, 1.3 * S, etch_w);
    etch_spokes(sctr, 1.3 * S, 6.2 * S, 5, 18, etch_w);
    // grille, lamps, vents, bumpers, roof gutter
    etch_line(pxy(-55, -11), pxy(-55, 1), etch_w);
    for (y = [-9 : 2.5 : -1])
        etch_line(pxy(-55, y), pxy(-52, y), etch_w);
    etch_ring(pxy(-52.5, 2.5), 1.8 * S, etch_w);
    for (x = [-24 : 2 : -20])
        etch_line(pxy(x, -2), pxy(x, 2), etch_w);
    etch_line(pxy(-58, -18), pxy(45, -18), etch_w);
    etch_line(pxy(-58, 24.8), pxy(43, 24.8), etch_w);
    etch_line(pxy(43, 24.8), pxy(43, 20), etch_w);
    etch_line(pxy(-57, -14), pxy(-57, 3), etch_w);
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
