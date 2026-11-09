/*
    BEAD BEAR - a broad, friendly bear face on the family's bead body.
    ================================================================

    The bear uses the letter bead's outer-family rules: the family width is
    the widest part of the cheeks, the bead thickness is width / 2, the
    string-hole throat and face fillets keep the same family defaults, and
    the bottom stays flat for the build plate.

    Face language (matching the supplied felt-bear illustration):
      - broad, near-round head with two large round ears overlapping the crown
      - pink inner-ear shape: shallow recess in the front face and a contour
        etch on the build-plate face
      - raised oval eye pads with a small raised white catchlight
      - raised round muzzle ("the round bit" is the muzzle / snout)
      - raised nose and a raised stitched-looking mouth line
      - bottom-face contour etches for the inner ears, eyes, pupils,
        muzzle, nose and mouth, in the same shallow-groove language as the
        letter bead's bottom letter

    The bottom etch keeps the same layout as the front face, so every
    groove sits directly under the feature it belongs to.  (The bear is
    left-right symmetric, so looking at the bottom from below reads the
    same way, just mirrored left-to-right.)

    width       widest part of the cheeks (mm)
    height      bead thickness = width / 2 (computed)
    fillet_radius  face fillet = width / 12 (family rule)
    ear_size    scales both ear lobes and their inner-ear pockets
    eye_spacing  moves the eyes apart without changing their size
    muzzle_size  scales the muzzle and its nose/mouth details
    detail_relief  scales the raised/recessed front-face relief
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width = 120;
height = width / 2;

// ---- string hole (common family block) ---------------------------------
hole_diameter = 20;
// Flare arc radius: family rule width / 8; retained, unused by the mouth.
bore_fillet_radius = width / 8;
// Quarter-round face fillet: family rule width / 12.
fillet_radius = width / 12;

// ---- bear shape dials --------------------------------------------------
ear_size = 1.0;                // 0.80..1.20, ear lobe + inner-ear scale
eye_spacing = 1.0;             // 0.80..1.20, eye centre spacing
muzzle_size = 1.0;             // 0.85..1.15, muzzle/nose/mouth scale
detail_relief = 1.0;           // 0.50..1.50, front-face relief scale

// Derived hole values
R_throat = hole_diameter / 2;
extra = 5;                     // mm bore overshoot past both walls
r_mouth_max = (height / 2.25) - (fillet_radius + R_throat);
r_mouth = max(0.5, min(0.5 * hole_diameter, r_mouth_max));

// Smooth surfaces, still fast.
$fn = 128;

// ---- sanity checks -----------------------------------------------------
assert(width > 0, "width must be positive");
assert(hole_diameter < width, "hole throat must fit within the face");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2");
assert(ear_size > 0, "ear_size must be positive");
assert(eye_spacing > 0, "eye_spacing must be positive");
assert(muzzle_size > 0, "muzzle_size must be positive");
assert(detail_relief > 0, "detail_relief must be positive");

// ---- primary face proportions -----------------------------------------
R = width / 2;
H = height;
c = fillet_radius;

// A broad face that is only slightly wider than tall, like the reference:
// the cheeks define the family width, while the ear lobes sit high on the
// crown and outboard of the cheeks (their outer edges may extend past it).
face_ry = 0.90 * R;
face_cy = 0.0;

// Large high ears.  The lobes overlap the crown; their outer edge may sit
// outside the cheek width, because the family width is defined by the
// cheeks, not by the ears.
ear_r = 0.35 * R * ear_size;
ear_x = 0.86 * R;
ear_y = 0.78 * R;
// The inner-ear recess is an upright oval, shifted slightly inward/down.
// The front recess may tuck a little into the ear's face fillet; the
// build-plate etch stays clamped to the flat cap so its groove never runs
// off the bottom edge.
inner_ear_r = min(
    0.19 * R * ear_size,
    (ear_r - fillet_radius + 1.8) / 1.15);
inner_ear_etch_r = min(
    inner_ear_r,
    (ear_r - fillet_radius - 1.2) / 1.15);
inner_ear_x_scale = 0.90;
inner_ear_y_scale = 1.15;
inner_ear_dx = 0.04 * R;
inner_ear_dy = -0.08 * R;

// Eyes are large raised oval pads set high and close to the muzzle.
eye_x = 0.44 * R * eye_spacing;
eye_y = 0.36 * R;
eye_r = 0.14 * R;
eye_y_scale = 1.25;
catchlight_r = 0.032 * R;
catchlight_dx = -0.045 * R;
catchlight_dy = 0.055 * R;

// The round bit around the nose and mouth is the muzzle.  It is the wide
// cream oval of the reference; the nose/mouth sit high in its upper half.
muzzle_cy = -0.32 * R;
muzzle_r = 0.38 * R * muzzle_size;
nose_raise = 0.55 * detail_relief;
mouth_raise = 0.45 * detail_relief;

// Front-face relief amounts.
inner_ear_recess = 1.20 * detail_relief;
eye_raise = 1.10 * detail_relief;
catchlight_raise = 0.45 * detail_relief;
muzzle_raise = 1.10 * detail_relief;

// Bottom etch mirrors the letter bead's shallow contour-groove language.
etch_depth = 1.0;
etch_width = 0.8;

// ---- 2D outline --------------------------------------------------------
module _face_2d() {
    translate([0, face_cy])
        scale([1, face_ry / R])
            circle(r = R);
}

module bear_outline_2d() {
    union() {
        _face_2d();
        translate([ ear_x, ear_y]) circle(r = ear_r);
        translate([-ear_x, ear_y]) circle(r = ear_r);
    }
}

// Inner ears: the pink felt shapes, also used for the bottom etch.
module inner_ears_2d(r = inner_ear_r) {
    for (s = [-1, 1])
        translate([s * (ear_x - inner_ear_dx), ear_y + inner_ear_dy])
            scale([inner_ear_x_scale, inner_ear_y_scale])
                circle(r = r);
}

// Eyes: oval black pads.  The catchlights are separate small raised dots.
module eye_pad_2d(side) {
    translate([side * eye_x, eye_y])
        scale([1, eye_y_scale])
            circle(r = eye_r);
}

module eyes_2d() {
    eye_pad_2d(-1);
    eye_pad_2d(1);
}

module catchlights_2d() {
    for (s = [-1, 1])
        translate([s * eye_x + catchlight_dx, eye_y + catchlight_dy])
            circle(r = catchlight_r);
}

// Muzzle / snout, nose and mouth are built in muzzle-local coordinates so
// the muzzle_size dial scales the whole expression coherently.
module muzzle_2d() {
    translate([0, muzzle_cy])
        scale([muzzle_size, muzzle_size])
            circle(r = 0.29 * R);
}

module nose_2d() {
    translate([0, muzzle_cy])
        scale([muzzle_size, muzzle_size])
            hull() {
                translate([-0.090 * R, 0.280 * R]) circle(r = 0.060 * R);
                translate([ 0.090 * R, 0.280 * R]) circle(r = 0.060 * R);
                translate([ 0.000 * R, 0.160 * R]) circle(r = 0.050 * R);
            }
}

function _qbez(p0, p1, p2, t) =
    let(u = 1 - t)
    [
        u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
    ];

module mouth_2d() {
    translate([0, muzzle_cy])
        scale([muzzle_size, muzzle_size]) {
            line_w = 0.023 * R;
            // Short stem down from the nose, then the two soft "w" arcs.
            hull() {
                translate([0, 0.120 * R]) circle(r = line_w / 2);
                translate([0, 0.040 * R]) circle(r = line_w / 2);
            }
            for (s = [-1, 1]) {
                n = 18;
                for (i = [0 : n - 1]) {
                    p0 = _qbez(
                        [0, 0.040 * R],
                        [s * 0.070 * R, -0.050 * R],
                        [s * 0.140 * R, -0.010 * R],
                        i / n);
                    p1 = _qbez(
                        [0, 0.040 * R],
                        [s * 0.070 * R, -0.050 * R],
                        [s * 0.140 * R, -0.010 * R],
                        (i + 1) / n);
                    hull() {
                        translate([p0[0], p0[1]]) circle(r = line_w / 2);
                        translate([p1[0], p1[1]]) circle(r = line_w / 2);
                    }
                }
            }
        }
}

// ---- raised/recessed 2D helper ----------------------------------------
// A shallow bevelled raise.  The top few slices shrink toward the centre,
// so the feature reads as a soft pad rather than a vertical-walled decal.
module raised_2d(h, bevel = 0.25) {
    base = max(0.01, h - bevel);
    linear_extrude(height = base)
        children();
    for (k = [0 : 2])
        translate([0, 0, base + bevel * k / 3])
            linear_extrude(height = bevel / 3 + 0.002)
                offset(r = -bevel * (k + 1) / 3)
                    children();
}

// ---- body: extruded outline + the family's face fillets ----------------
n_fillet = 32;
fillet_u = [for (i = [0 : n_fillet]) c - c * cos(-90 + 90 * i / n_fillet)];
fillet_z = [for (i = [0 : n_fillet]) c + c * sin(-90 + 90 * i / n_fillet)];

module bear_solid() {
    union() {
        // bottom fillet
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z[i]])
                linear_extrude(height = fillet_z[i + 1] - fillet_z[i])
                    offset(r = -fillet_u[i])
                        bear_outline_2d();
        // straight side wall
        if (H - 2 * c > 0.001)
            translate([0, 0, c])
                linear_extrude(height = H - 2 * c)
                    bear_outline_2d();
        // top fillet
        for (k = [0 : n_fillet - 1])
            translate([0, 0, H - fillet_z[k + 1]])
                linear_extrude(height = fillet_z[k + 1] - fillet_z[k])
                    offset(r = -fillet_u[k])
                        bear_outline_2d();
    }
}

// ---- string hole: straight bore + swept ball-fillet mouth --------------
// The bear's cheek wall is curved in plan, so the heart/star rolling-ball
// mouth is used rather than the letter's revolved well.
function face_x_at(y) =
    R * sqrt(max(0, 1 - pow((y - face_cy) / face_ry, 2)));

function wall_x_at(y) = face_x_at(y);

function wall_n_at(y) =
    let(e = 0.5,
        p0 = [wall_x_at(y - e), y - e],
        p1 = [wall_x_at(y + e), y + e],
        tx = p1[0] - p0[0],
        ty = p1[1] - p0[1],
        m = sqrt(tx * tx + ty * ty))
        [ty / m, -tx / m, 0];

function vsub(a, b) = [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
function vadd(a, b) = [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
function vmul(a, s) = [a[0] * s, a[1] * s, a[2] * s];
function vdot(a, b) = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

hole_entry_x = face_x_at(0);
assert(hole_entry_x > 0, "hole_entry_x must be positive");
assert(r_mouth > 0, "mouth fillet collapsed: height too small for this hole");

mf_r = r_mouth;
mf_n = 240;
mf_arc = 16;
mf_th = [for (i = [0 : mf_n - 1]) 360 * i / mf_n];
mf_E = [for (a = mf_th)
    [wall_x_at(R_throat * cos(a)), R_throat * cos(a),
     H / 2 + R_throat * sin(a)]];
mf_nb = [for (a = mf_th) [0, cos(a), sin(a)]];
mf_nw = [for (a = mf_th) wall_n_at(R_throat * cos(a))];
mf_c0 = [for (i = [0 : mf_n - 1]) vdot(mf_nb[i], mf_nw[i])];
mf_s0 = [for (i = [0 : mf_n - 1]) sqrt(max(1e-9, 1 - mf_c0[i] * mf_c0[i]))];
mf_e2 = [for (i = [0 : mf_n - 1])
    vmul(vsub(mf_nw[i], vmul(mf_nb[i], mf_c0[i])), 1 / mf_s0[i])];

function mf_sec(i) =
    let(c0 = mf_c0[i], s0 = mf_s0[i], e1 = mf_nb[i], e2 = mf_e2[i],
        th = acos(max(-1, min(1, c0))),
        b_c = -mf_r * (1 + c0) / s0)
    concat(
        [mf_E[i]],
        [for (k = [0 : mf_arc])
            let(phi = 180 - (180 - th) * k / mf_arc)
                vadd(mf_E[i],
                     vadd(vmul(e1, mf_r * (1 + cos(phi))),
                          vmul(e2, b_c + mf_r * sin(phi))))]
    );

mf_w = mf_arc + 2;
mf_pts = [for (i = [0 : mf_n - 1]) each mf_sec(i)];
mf_faces = [for (i = [0 : mf_n - 1])
    for (j = [0 : mf_w - 1])
        let(a = i * mf_w + j,
            b = i * mf_w + (j + 1) % mf_w,
            c = ((i + 1) % mf_n) * mf_w + (j + 1) % mf_w,
            d = ((i + 1) % mf_n) * mf_w + j)
        each [[a, b, c], [a, c, d]]];

module mf_cutter() {
    polyhedron(points = mf_pts, faces = mf_faces, convexity = 10);
}

module string_hole() {
    translate([0, 0, H / 2])
        rotate([0, 90, 0])
            cylinder(h = 2 * (hole_entry_x + extra), r = R_throat, center = true);
    mf_cutter();
    mirror([1, 0, 0]) mf_cutter();
}

// ---- bottom etch -------------------------------------------------------
// Contour grooves in the same layout as the front face, so each groove sits
// directly under the feature it belongs to.
module _etch_ring(w) {
    difference() {
        children();
        offset(r = -w)
            children();
    }
}

module bottom_etch_2d() {
    // inner ears
    _etch_ring(min(etch_width, inner_ear_etch_r * 0.35))
        inner_ears_2d(inner_ear_etch_r);
    // eyes
    _etch_ring(min(etch_width, eye_r * 0.35))
        eyes_2d();
    // pupils / catchlights
    _etch_ring(min(etch_width, catchlight_r * 0.35))
        catchlights_2d();
    // muzzle
    _etch_ring(min(etch_width, muzzle_r * 0.25))
        muzzle_2d();
    // nose
    _etch_ring(min(etch_width, 0.052 * R * muzzle_size * 0.55))
        nose_2d();
    // mouth: a line feature, so the groove follows the line itself rather
    // than trying to leave an impossibly thin island inside it.
    mouth_2d();
}

// ---- assembled bead ----------------------------------------------------
module _bear_body() {
    difference() {
        bear_solid();
        string_hole();
        // pink inner-ear recess on the front face
        translate([0, 0, H - inner_ear_recess])
            linear_extrude(height = inner_ear_recess + 0.5)
                inner_ears_2d();
        // shallow build-plate-face etch
        translate([0, 0, -0.5])
            linear_extrude(height = etch_depth + 0.5)
                bottom_etch_2d();
    }
}

module _bear_details() {
    // eyes
    translate([0, 0, H])
        raised_2d(eye_raise, 0.30)
            eyes_2d();
    // white catchlights sit on top of the eye pads
    translate([0, 0, H + eye_raise])
        raised_2d(catchlight_raise, 0.12)
            catchlights_2d();
    // muzzle
    translate([0, 0, H])
        raised_2d(muzzle_raise, 0.35)
            muzzle_2d();
    // nose and mouth sit on the raised muzzle
    translate([0, 0, H + muzzle_raise])
        raised_2d(nose_raise, 0.16)
            nose_2d();
    translate([0, 0, H + muzzle_raise])
        raised_2d(mouth_raise, 0.10)
            mouth_2d();
}

union() {
    _bear_body();
    _bear_details();
}
