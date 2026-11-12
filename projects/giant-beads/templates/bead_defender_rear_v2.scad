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
                   recessed by height / 20.  A tyre seen from behind is a curved
                   rectangle, not a circle; it is round in profile, so each one
                   is a column crowned across the tread: back at the shoulders,
                   swelling out to just under the face on the centre line
*/

include <bead_defender_rear_data.scad>
use <bead_common.scad>       // the family mouth: bead_string_hole_well()

// ---- family parameters ------------------------------------------------
width = 120;
height = width / 2;                // family rule (60 mm at width 120)
hole_diameter = 20;
bore_fillet_radius = width / 8;    // retained family name; plain bore
fillet_radius = 1;                 // deliberately tight: keep the boxy read
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
pad_fillet = min(fillet_radius, seam_height / 2);  // roundover on a pad's top edge
pad_cove = min(fillet_radius, seam_height / 2);    // concave cove at its foot
tread_low = height / 20;           // how far the road wheels sit below the face

// ---- derived ----------------------------------------------------------
R_throat = hole_diameter / 2;
// Family mouth: same dial as bead.scad, so the six beads share one well.
r_mouth_max = (height / 2.25) - (fillet_radius + R_throat);
r_mouth = max(0.5, min(0.5 * hole_diameter, r_mouth_max));
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
assert(0 < tread_low && tread_low < H / 2);
assert(len(TREAD_CROWN) == len(TYRE_TREAD),
       "every road wheel needs a crown centre line");
assert(seam_height > 0 && lights_height > 0);
assert(len(SILHOUETTE) >= 3, "no silhouette in the data file");

// ---- face plane -------------------------------------------------------
function sc(pts) = [for (p = pts) [p[0] * S, p[1] * S]];

module sil_2d() polygon(points = sc(SILHOUETTE));

module tread_2d() {
    for (t = TYRE_TREAD) polygon(points = sc(t));
}

module tread_one_2d(k) polygon(points = sc(TYRE_TREAD[k]));

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

// The face etch as it would be seen from the other side: the spare wheel hides
// the door and window behind it, so those grooves stop at its rim.
module plate_etch_2d() {
    difference() {
        etch_face_2d();
        for (t = RAISED_TYRE)
            translate([t[0] * S, t[1] * S]) circle(r = t[2] * S);
    }
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
// Widest on the face and vanishing at the pad's top: the arc is a quarter
// round tangent to the face at its foot.  The old form had it the other way up,
// which built a saucer standing off the face round every lamp and pad.
function cove_out(i) = pad_cove - sqrt(max(0.0001, pad_cove * pad_cove
                                           - (pad_cove - cove_h(i))
                                             * (pad_cove - cove_h(i))));

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

// ---- road wheels ------------------------------------------------------
// The chassis line is the bottom of the body.  The two road wheels hang below
// it, so each is a form of its own: the body is cut back over the wheel
// footprint, and the wheel is what fills it.
//
// Straight on the wheel is a curved rectangle - a tyre seen from behind is a
// tread band, not a circle.  Its surface leaves the leg's side wall *vertically*
// and rounds over into the body, which is the contour the principal drew, and
// it keeps rounding all the way to its own centre: a quarter-ellipse in the
// distance from the wheel's edge, never a flat pad and never a step.
//
// Everything here is a stack of the footprint's own inward offsets, so there is
// no horizontal face anywhere except the shoulder's shallow terraces, and in
// particular none sitting against the leg's wall - that flat ledge is what the
// principal crossed out, twice.
wheel_top = H - tread_low;         // where the surface leaves the side wall
wheel_rise = tread_low - 0.2;      // how far it swells back out, under the face
n_wheel = 6 * n_fillet;         // fine enough that the steps never read as terraces

// Removes the body over the wheel footprint, so the wheel is what is left.
// The cut flares out as it reaches the face, rounding the edge between the
// body's face and the wheel's recess: nothing on this bead is allowed a hard
// line, and the bottom of the cross member was the last one.
module wheel_cutout() {
    h0 = wheel_top - 0.05;
    translate([0, 0, h0])
        linear_extrude(height = H - fillet_radius - h0)
            offset(r = 0.25) tread_2d();
    for (i = [0 : n_fillet - 1])
        translate([0, 0, H - fillet_radius + tread_h(i)])
            linear_extrude(height = tread_h(i + 1) - tread_h(i) + 0.005)
                offset(r = rim_inset(i)) tread_2d();
}

// Quarter round from the vertical pocket wall (0.25 mm proud of the footprint,
// so the wall is never subtracted from itself) out to the face.
function tread_h(i) = fillet_radius * i / n_fillet;
function rim_inset(i) = 0.25 + fillet_radius
                        - sqrt(max(0.0001, fillet_radius * fillet_radius
                                     - tread_h(i) * tread_h(i)));

// The surface, sampled by angle so the slices near the wall - where the curve
// is steepest - stay thin.  d is the inward offset, z the height reached there.
module wheel_solid() {
    for (k = [0 : len(TYRE_TREAD) - 1]) {
        dmax = TREAD_CROWN[k][1] * S;
        for (i = [0 : n_wheel - 1]) {
            th = 90 * i / n_wheel;
            d = dmax * (1 - cos(th));
            z = wheel_top + wheel_rise * sin(th);
            linear_extrude(height = z) offset(r = -d) tread_one_2d(k);
        }
    }
}

// ---- cuts -------------------------------------------------------------
module etch_cuts() {
    // top face: down from the face
    translate([0, 0, H - etch_depth])
        linear_extrude(height = etch_depth + 0.1) etch_face_2d();
    // build plate: up from the bottom, flat face plus the raised outlines.
    // Mirrored in x: turn the bead over and you are looking at the car from the
    // other side, so the number plate must stay on the same hand as the raised
    // face, and the offset spare must offset the other way.
    translate([0, 0, -0.1])
        linear_extrude(height = etch_depth + 0.1)
            mirror([1, 0, 0])
                union() {
                    plate_etch_2d();
                    outline_raised_2d();
                }
    // the wheel detail sits on the raised steel wheel, so it is cut from the
    // wheel's own top rather than from the body face
    translate([0, 0, H + wheel_height - etch_depth])
        linear_extrude(height = etch_depth + 0.1) etch_wheel_2d();
}

module bead() {
    difference() {
        union() {
            difference() {
                body_solid();
                wheel_cutout();
            }
            wheel_solid();
            raised_detail();
        }
        etch_cuts();
        // String hole: through the width at mid-thickness, with the family's
        // quarter-round fillet well at both mouths - the gravitational well the
        // rope sits in - rather than a plain bore with sharp rims.
        translate([0, 0, H / 2])
            bead_string_hole_well(hole_entry_x = width / 2, R_throat = R_throat,
                                  r_mouth = r_mouth, extra = extra);
    }
}

bead();
