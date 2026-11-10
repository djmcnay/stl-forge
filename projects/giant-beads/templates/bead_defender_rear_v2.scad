/*
    DEFENDER 90 REAR BEAD - built from the approved trace
    =====================================================

    The geometry is not drawn here.  It comes from
    `references/defender/rear-bead-sketch.json` - the clean sketch derived from
    the principal's trace - baked into `bead_defender_rear_data.scad` by
    `tools/bead_scad.py`.  Re-run that tool after any change to the sketch and
    commit the regenerated data file with it.

    Faces
      top        the face that shows the car.  Carries the etches and the
                 raised detail.
      bottom     the build plate (z = 0).  NOTHING protrudes: flat apart from
                 etched grooves, so the bead sits on the plate and prints
                 without supports.  Every raised part is repeated there as an
                 etch outline - the faces mirror each other in line, not relief.

    Levels (as agreed on the part map)
      silhouette   the profile, extruded with a quarter-round edge fillet on the
                   top face only
      etch         one depth: door, rear window, alpine lights, number plate,
                   roof gutter, bumper top edge, wheel detail (holes, nuts,
                   hub, cut at the raised wheel's own height)
      raised       lights (domes), spare tyre, steel wheel, waist seam - each
                   its own height, rounded over at the top and filleted where
                   it meets the face
      treads       the road wheels sit behind the rear, so their tread bands are
                   recessed by height / 20 with a quarter-round back up to the
                   face: lower than the body, rounded like a wheel
*/

include <bead_defender_rear_data.scad>

// ---- family parameters ------------------------------------------------
width = 120;
height = width / 2;                // family rule (60 mm at width 120)
hole_diameter = 20;
bore_fillet_radius = width / 8;    // retained family name; plain bore
fillet_radius = 2;                 // deliberately tight: keep the boxy read
detail_relief = 1.0;
$fn = 128;

// ---- etching ----------------------------------------------------------
etch_depth = 0.6 * detail_relief;  // family value for the Defender pair
etch_w = 1.0;                      // groove width (mm), not scaled by width

// ---- raised heights, as fractions of the bead thickness ---------------
lights_height = height / 30;
tyre_height = height / 10;
wheel_height = height / 15;
seam_height = height / 30;

// ---- edge treatment ---------------------------------------------------
pad_fillet = min(1.0, seam_height / 2);   // roundover on a pad's top edge
pad_cove = min(1.0, seam_height / 2);     // concave fillet where it meets the face
tread_low = height / 20;           // how far the road wheels sit below the face
tread_fillet = tread_low;          // quarter-round from the recess floor to the
                                   // face: tangent at both ends

// ---- derived ----------------------------------------------------------
R_throat = hole_diameter / 2;
extra = 5;
H = height;
c = fillet_radius;
S = width / DATA_WIDTH;            // face-plane scale from the sketch frame
n_fillet = 16;                     // slices used by every rounded surface
n_round = 2 * n_fillet;

assert(width > 0 && height > 0);
assert(hole_diameter > 0 && hole_diameter < width, "string hole must fit");
assert(fillet_radius > 0 && fillet_radius < H / 2,
       "edge fillet must be under half the thickness");
assert(etch_depth > 0 && etch_depth < c,
       "etch must be shallower than the edge fillet");
assert(tyre_height > wheel_height && wheel_height > 0,
       "the tyre must stand proud of the steel wheel");
assert(0 < pad_fillet && pad_fillet < lights_height,
       "pad roundover must fit inside the shallowest raised level");
assert(0 < tread_low && tread_low < H / 2 && tread_fillet > 0);
assert(seam_height > 0 && lights_height > 0);
assert(len(SILHOUETTE) >= 3, "no silhouette in the data file");

// ---- face plane -------------------------------------------------------
function sc(pts) = [for (p = pts) [p[0] * S, p[1] * S]];

module sil_2d() polygon(points = sc(SILHOUETTE));

module tread_2d() {
    for (t = TYRE_TREAD) polygon(points = sc(t));
}

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

// The raised levels drawn flat: their outlines as grooves.  Used on the build
// plate, where nothing may stand up.
module outline_raised_2d() {
    union() {
        for (t = RAISED_TYRE) ring_2d([t[0], t[1], t[2]]);
        for (t = RAISED_WHEEL) ring_2d(t);
        for (pad = RAISED_SEAM) stroke_loop(pad);
        for (l = LIGHTS) ring_2d(l);
    }
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
// Quarter-round edge fillet on the top face only; the bottom is the build
// plate and stays flat.  Stacked erosion slices, the family method.
function fillet_u(i) = c - c * cos(-90 + 90 * i / n_fillet);
function fillet_z(i) = c + c * sin(-90 + 90 * i / n_fillet);

module body_solid() {
    union() {
        linear_extrude(height = H - c) sil_2d();
        for (i = [0 : n_fillet - 1])
            translate([0, 0, H - fillet_z(i + 1)])
                linear_extrude(height = fillet_z(i + 1) - fillet_z(i) + 0.005)
                    offset(r = -fillet_u(i)) sil_2d();
    }
}

// ---- raised detail ----------------------------------------------------
// A pad runs from the plate straight up to pad_fillet below its top, rounds
// over there, and grows a concave cove where it meets the face.  The cove is
// added material: rings spread wider the lower they sit.
function round_h(i) = pad_fillet * i / n_round;
function round_inset(i) = pad_fillet - sqrt(max(0.0001, pad_fillet * pad_fillet
                                               - round_h(i) * round_h(i)));
function cove_h(i) = pad_cove * i / n_round;
function cove_out(i) = pad_cove - sqrt(max(0.0001, pad_cove * pad_cove
                                           - cove_h(i) * cove_h(i)));

module pad(h) {
    top = H + h;
    linear_extrude(height = top - pad_fillet) children();
    for (i = [0 : n_round - 1])
        translate([0, 0, top - pad_fillet + round_h(i)])
            linear_extrude(height = round_h(i + 1) - round_h(i) + 0.005)
                offset(r = -round_inset(i + 1)) children();
    for (i = [0 : n_round - 1])
        translate([0, 0, H + cove_h(i)])
            linear_extrude(height = cove_h(i + 1) - cove_h(i) + 0.005)
                difference() {
                    offset(r = cove_out(i) + 0.01) children();
                    children();
                }
}

// A lamp is a half-ellipsoid: in-plane radius as sketched, height as
// specified, with the same cove at its foot.
module lamps() {
    for (l = LIGHTS) {
        translate([l[0] * S, l[1] * S, H])
            scale([S, S, lights_height / l[2]]) sphere(r = l[2]);
        for (i = [0 : n_round - 1])
            translate([l[0] * S, l[1] * S, H + cove_h(i)])
                linear_extrude(height = cove_h(i + 1) - cove_h(i) + 0.005)
                    difference() {
                        circle(r = l[2] * S + cove_out(i));
                        circle(r = l[2] * S);
                    }
    }
}

module raised_detail() {
    pad(tyre_height) raised_tyre_2d();
    pad(wheel_height) raised_wheel_2d();
    pad(seam_height) raised_seam_2d();
    lamps();
}

// ---- road-wheel treads ------------------------------------------------
// The wheels sit behind the rear, so the tread band is cut down to the recess
// floor and a quarter-round climbs back out to the face.
function tread_z(i) = tread_low * i / n_round;
function tread_inset(i) = tread_fillet - sqrt(max(0.0001, tread_fillet *
                                                 tread_fillet -
                                                 tread_z(i) * tread_z(i)));

// The cut itself: at the recess floor the whole footprint comes out, and the
// removed area shrinks as it climbs, leaving a quarter-round of material along
// the edge up to the face.  Stacked insets, so the fillet is exact.
module tread_recess() {
    plateau = H - tread_low;
    for (i = [0 : n_round - 1])
        translate([0, 0, plateau + tread_z(i)])
            linear_extrude(height = tread_z(i + 1) - tread_z(i) + 0.005)
                offset(r = -tread_inset(i + 1)) tread_2d();
}

// ---- cuts -------------------------------------------------------------
module etch_cuts() {
    // top face: down from the face
    translate([0, 0, H - etch_depth])
        linear_extrude(height = etch_depth + 0.1) etch_face_2d();
    // build plate: up from the bottom, flat face plus the raised outlines
    translate([0, 0, -0.1])
        linear_extrude(height = etch_depth + 0.1)
            union() {
                etch_face_2d();
                outline_raised_2d();
            }
    // the wheel detail sits on the raised steel wheel, so it is cut from the
    // wheel's own top rather than from the body face
    translate([0, 0, H + wheel_height - etch_depth])
        linear_extrude(height = etch_depth + 0.1) etch_wheel_2d();
    // the silhouette runs through the tread plateau: etch it there too, so the
    // groove keeps the same depth on both levels
    translate([0, 0, H - tread_low - etch_depth])
        linear_extrude(height = etch_depth + 0.2)
            intersection() {
                etch_face_2d();
                tread_2d();
            }
}

module bead() {
    difference() {
        union() {
            body_solid();
            raised_detail();
        }
        etch_cuts();
        tread_recess();
        // string hole: through the width, at mid-thickness (family convention)
        translate([0, 0, H / 2])
            rotate([0, 90, 0])
                cylinder(h = width + 2 * extra, r = R_throat, center = true);
    }
}

bead();
