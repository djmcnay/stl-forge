/*
    DEFENDER 90 REAR BEAD - built from the approved trace
    =====================================================

    The geometry is not drawn here.  It comes from
    `references/defender/rear-bead-sketch.json` - the clean sketch derived from
    the principal's trace - baked into `bead_defender_rear_data.scad` by
    `tools/bead_scad.py`.  Re-run that tool after any change to the sketch and
    commit the regenerated data file with it.

    Structure (levels, as agreed on the part map):

      silhouette   the profile, extruded with a quarter-round edge fillet
      etch         one depth on both faces: door, rear window, alpine lights,
                   number plate, roof gutter, bumper top edge, and the wheel
                   detail (holes, nuts, hub) which is cut at the raised wheel's
                   own height
      raised       each on its own height, both faces: lights (domes), spare
                   tyre, steel wheel, waist seam.  The bumper cross member is
                   flush with the car, so it is not raised.

    Parameters
      width                 vehicle width, family default 120
      height                bead thickness, family default 30
      hole_diameter         string hole, family default 20
      fillet_radius         edge fillet, 2 mm - deliberately tight so the
                            boxy Defender shape survives
      etch_depth            engraved depth, family value 0.6 * detail_relief
      lights_height         height / 20
      tyre_height           height / 10
      wheel_height          height / 15
      seam_height           height / 20
*/

include <bead_defender_rear_data.scad>

// ---- family parameters ------------------------------------------------
width = 120;
height = 30;
hole_diameter = 20;
bore_fillet_radius = width / 8;    // retained family name; plain bore
fillet_radius = 2;
detail_relief = 1.0;
$fn = 128;

// ---- etching ----------------------------------------------------------
etch_depth = 0.6 * detail_relief;  // family value for the Defender pair
etch_w = 1.0;                      // groove width (mm), not scaled by width

// ---- raised heights, as fractions of the bead thickness ---------------
lights_height = height / 20;
tyre_height = height / 10;
wheel_height = height / 15;
seam_height = height / 20;

// ---- derived ----------------------------------------------------------
R_throat = hole_diameter / 2;
extra = 5;
H = height;
c = fillet_radius;
S = width / DATA_WIDTH;            // face-plane scale from the sketch frame

assert(width > 0);
assert(hole_diameter > 0 && hole_diameter < width, "string hole must fit");
assert(fillet_radius > 0 && fillet_radius < H / 2,
       "edge fillet must be under half the thickness");
assert(etch_depth > 0 && etch_depth < c,
       "etch must be shallower than the edge fillet");
assert(tyre_height > wheel_height && wheel_height > 0,
       "the tyre must stand proud of the steel wheel");
assert(lights_height > 0 && seam_height > 0);
assert(len(SILHOUETTE) >= 3, "no silhouette in the data file");

// ---- face plane -------------------------------------------------------
function sc(pts) = [for (p = pts) [p[0] * S, p[1] * S]];

module sil_2d() polygon(points = sc(SILHOUETTE));

// A stroked polyline: a capsule per segment, which keeps the ends round.
module stroke(pts, w = etch_w) {
    for (i = [0 : len(pts) - 2]) {
        p0 = [pts[i][0] * S, pts[i][1] * S];
        p1 = [pts[i + 1][0] * S, pts[i + 1][1] * S];
        hull() {
            translate(p0) circle(r = w / 2);
            translate(p1) circle(r = w / 2);
        }
    }
}

module stroke_loop(pts, w = etch_w) {
    stroke(concat(pts, [pts[0]]), w);
}

// t = [cx, cy, r] in sketch millimetres
module ring_2d(t, w = etch_w) {
    translate([t[0] * S, t[1] * S]) difference() {
        circle(r = t[2] * S + w / 2);
        circle(r = max(t[2] * S - w / 2, 0.1));
    }
}

module etch_face_2d() {
    union() {
        for (pts = ETCH_STROKES) stroke_loop(pts);
        for (t = ETCH_RINGS) ring_2d(t);
    }
}

module etch_wheel_2d() {
    for (t = ETCH_WHEEL_RINGS) ring_2d(t);
}

module raised_tyre_2d() {
    for (t = RAISED_TYRE)
        translate([t[0] * S, t[1] * S]) difference() {
            circle(r = t[2] * S);
            circle(r = t[3] * S);
        }
}

module raised_wheel_2d() {
    for (t = RAISED_WHEEL)
        translate([t[0] * S, t[1] * S]) circle(r = t[2] * S);
}

module raised_seam_2d() {
    for (pad = RAISED_SEAM) polygon(points = sc(pad));
}

// ---- body -------------------------------------------------------------
// Quarter-round edge fillet both faces: stacked erosion slices, the method the
// rest of the family uses (offset() of the profile, never minkowski).
n_fillet = 16;   // 16 slices for a 2 mm fillet: smooth in print, no visible stepping
function fillet_u(i) = c - c * cos(-90 + 90 * i / n_fillet);
function fillet_z(i) = c + c * sin(-90 + 90 * i / n_fillet);

module body_solid() {
    union() {
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z(i)])
                linear_extrude(height = fillet_z(i + 1) - fillet_z(i) + 0.005)
                    offset(r = -fillet_u(i)) sil_2d();
        if (H - 2 * c > 0.001)
            translate([0, 0, c])
                linear_extrude(height = H - 2 * c) sil_2d();
        for (i = [0 : n_fillet - 1])
            translate([0, 0, H - fillet_z(i + 1)])
                linear_extrude(height = fillet_z(i + 1) - fillet_z(i) + 0.005)
                    offset(r = -fillet_u(i)) sil_2d();
    }
}

// ---- raised detail ----------------------------------------------------
// Pads start below the fillet zone so they merge into the body instead of
// floating over a rounded edge, and they are cut on both faces.
// h stands proud of the face; the pad reaches a little past the fillet so it
// grows out of the body instead of floating over a rounded edge.
module pad(h) {
    translate([0, 0, H - c - 0.5])            // +Z face
        linear_extrude(height = h + c + 0.5) children();
    translate([0, 0, -h])                     // -Z face
        linear_extrude(height = h + c + 0.5) children();
}

// A lamp is a half-ellipsoid: in-plane radius as sketched, height as specified.
module lamps() {
    for (l = LIGHTS) {
        translate([l[0] * S, l[1] * S, H])        // dome above the face
            scale([S, S, lights_height / l[2]]) sphere(r = l[2]);
        translate([l[0] * S, l[1] * S, 0])        // dome below it
            scale([S, S, lights_height / l[2]]) sphere(r = l[2]);
    }
}

module raised_detail() {
    pad(tyre_height) raised_tyre_2d();
    pad(wheel_height) raised_wheel_2d();
    pad(seam_height) raised_seam_2d();
    lamps();
}

// ---- etch cuts --------------------------------------------------------
module etch_cuts() {
    // both faces of the body: down from the top face, up from the bottom face
    translate([0, 0, H - etch_depth])
        linear_extrude(height = etch_depth + 0.5) etch_face_2d();
    translate([0, 0, -0.5])
        linear_extrude(height = etch_depth + 0.5) etch_face_2d();
    // the wheel detail sits on the raised steel wheel, so it is cut from the
    // wheel's own top rather than from the body face
    translate([0, 0, H + wheel_height - etch_depth])
        linear_extrude(height = etch_depth + 0.5) etch_wheel_2d();
    translate([0, 0, -(wheel_height + etch_depth)])
        linear_extrude(height = etch_depth + 0.5) etch_wheel_2d();
}

module bead() {
    difference() {
        union() {
            body_solid();
            raised_detail();
        }
        etch_cuts();
        // string hole: through the width, at mid-thickness (family convention)
        translate([0, 0, H / 2])
            rotate([0, 90, 0])
                cylinder(h = width + 2 * extra, r = R_throat, center = true);
    }
}

bead();
