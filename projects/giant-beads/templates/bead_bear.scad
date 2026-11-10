/*
    BEAD BEAR - filleted face bead.
    ==============================

    The approved face sketch is extruded between the family's quarter-round
    face fillets.  The front and build-plate faces stay flat inside those
    fillets, so all raised/recessed detail is supported and cannot overhang
    the chin.  The muzzle is pulled just inside the top flat so its bottom
    edge remains on the supported face.

    The string hole is a plain 20 mm bore along X through the side walls.

    Width       widest part of the cheeks (mm)
    height      body thickness = width / 2 (mm)
    ear_size    scales the ear lobes and inner-ear pockets
    eye_spacing moves the eyes apart
    muzzle_size scales the muzzle, nose and mouth
    detail_relief scales the raised/recessed face detail heights
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width = 120;
height = width / 2;

hole_diameter = 20;
bore_fillet_radius = width / 8;   // retained family name; plain bore here
fillet_radius = width / 12;       // family face fillet
R_throat = hole_diameter / 2;
extra = 5;

ear_size = 1.0;
eye_spacing = 1.0;
muzzle_size = 1.0;
detail_relief = 1.0;

$fn = 128;

// ---- sanity checks -----------------------------------------------------
assert(width > 0, "width must be positive");
assert(hole_diameter < width, "hole throat must fit within the face");
assert(ear_size > 0, "ear_size must be positive");
assert(eye_spacing > 0, "eye_spacing must be positive");
assert(muzzle_size > 0, "muzzle_size must be positive");
assert(detail_relief > 0, "detail_relief must be positive");

R = width / 2;
H = height;
c = fillet_radius;

// ---- approved face-sketch proportions ---------------------------------
// Traced from the supplied reference and normalised to width = 2R.
face_rx = 1.000 * R;
face_widest_y = -0.1893 * R;
face_top = 0.8895 * R;
face_bottom = -0.9172 * R;
upper_h = face_top - face_widest_y;
lower_h = face_widest_y - face_bottom;

ear_r = 0.4137 * R * ear_size;
ear_x = 0.7610 * R;
ear_y = 0.6967 * R;

inner_dx = 0.0322 * R;
inner_dy = 0.0322 * R;
inner_r = min(
    0.2102 * R * ear_size,
    ear_r - c - sqrt(inner_dx * inner_dx + inner_dy * inner_dy) - 0.5);

eye_x = 0.4373 * R * eye_spacing;
eye_y = -0.0128 * R;
eye_rx = 0.1458 * R;
eye_ry = 0.1707 * R;

pupil_rx = 0.0375 * R;
pupil_ry = 0.0537 * R;
pupil_dx = 0.0322 * R;
pupil_dy = 0.0803 * R;

muzzle_cy = -0.3627 * R;   // pulled up 3 mm to clear the face fillet
muzzle_rx = 0.4855 * R * muzzle_size;
muzzle_ry = 0.3698 * R * muzzle_size;

nose_cy = muzzle_cy + 0.1640 * R * muzzle_size;
nose_rx = 0.1832 * R * muzzle_size;
nose_ry = 0.1275 * R * muzzle_size;

// Mouth: one vertical stem into TWO U-shaped smiles, both meeting at
// the centre.  All y values are local to the muzzle centre.
mouth_top = 0.0365 * R;
mouth_mid = -0.1233 * R;
mouth_ctrl_y = -0.1983 * R;
mouth_tip_y = -0.1115 * R;
mouth_tip_x = 0.1833 * R;
mouth_ctrl_x = 0.0912 * R;
mouth_w = 0.025 * R;

// Feature heights
eye_raise = 0.025 * H * detail_relief;
muzzle_raise = 0.025 * H * detail_relief;
muzzle_fillet = min(0.8 * detail_relief, 0.55 * muzzle_raise);
inner_recess = 1.2 * detail_relief;
pupil_recess = inner_recess;
nose_etch = 0.6 * detail_relief;
mouth_etch = 0.6 * detail_relief;
etch_depth = 1.0;
etch_width = 0.8;

// ---- face outline: upper and lower half-ellipse (egg) -----------------
function face_pts(n = 160) = concat(
    [for (i = [0:n])
        let(a = 180 - 180 * i / n)
            [face_rx * cos(a), face_widest_y + upper_h * sin(a)]],
    [for (i = [1:n])
        let(a = -180 * i / n)
            [face_rx * cos(a), face_widest_y + lower_h * sin(a)]]
);

module face_2d() {
    polygon(points = face_pts());
}

module outer_2d() {
    union() {
        face_2d();
        translate([ ear_x, ear_y]) circle(r = ear_r);
        translate([-ear_x, ear_y]) circle(r = ear_r);
    }
}

// Inner ears are full circles cut back by the head, so they read as
// shapes disappearing behind the face rather than ovals on the cheek.
module inner_ears_2d(r = inner_r) {
    difference() {
        union() {
            translate([ ear_x - inner_dx, ear_y - inner_dy]) circle(r = r);
            translate([-ear_x + inner_dx, ear_y - inner_dy]) circle(r = r);
        }
        face_2d();
    }
}

module eyes_2d() {
    for (s = [-1, 1])
        translate([s * eye_x, eye_y])
            scale([1, eye_ry / eye_rx])
                circle(r = eye_rx);
}

module pupils_2d() {
    for (s = [-1, 1])
        translate([s * eye_x + pupil_dx, eye_y + pupil_dy])
            scale([1, pupil_ry / pupil_rx])
                circle(r = pupil_rx);
}

module muzzle_2d() {
    translate([0, muzzle_cy])
        scale([1, muzzle_ry / muzzle_rx])
            circle(r = muzzle_rx);
}

module nose_2d() {
    translate([0, nose_cy])
        scale([1, nose_ry / nose_rx])
            circle(r = nose_rx);
}

function _qbez(p0, p1, p2, t) =
    let(u = 1 - t)
    [u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
     u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]];

module _mouth_capsule(p0, p1) {
    hull() {
        translate(p0) circle(r = mouth_w / 2);
        translate(p1) circle(r = mouth_w / 2);
    }
}

module mouth_2d() {
    translate([0, muzzle_cy])
        scale([muzzle_size, muzzle_size]) {
            // central stem
            _mouth_capsule([0, mouth_top], [0, mouth_mid]);
            // two separate U-shaped smiles meeting at the centre
            for (side = [-1, 1]) {
                n = 24;
                for (i = [0 : n - 1])
                    _mouth_capsule(
                        _qbez([0, mouth_mid],
                              [side * mouth_ctrl_x, mouth_ctrl_y],
                              [side * mouth_tip_x, mouth_tip_y],
                              i / n),
                        _qbez([0, mouth_mid],
                              [side * mouth_ctrl_x, mouth_ctrl_y],
                              [side * mouth_tip_x, mouth_tip_y],
                              (i + 1) / n));
            }
        }
}

// ---- filleted body -----------------------------------------------------
n_fillet = 128;
fillet_u = [for (i = [0 : n_fillet])
                c - c * cos(-90 + 90 * i / n_fillet)];
fillet_z = [for (i = [0 : n_fillet])
                c + c * sin(-90 + 90 * i / n_fillet)];

module bear_solid() {
    union() {
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z[i]])
                linear_extrude(height = fillet_z[i + 1] - fillet_z[i] + 0.005)
                    offset(r = -fillet_u[i])
                        outer_2d();
        if (H - 2 * c > 0.001)
            translate([0, 0, c])
                linear_extrude(height = H - 2 * c)
                    outer_2d();
        for (k = [0 : n_fillet - 1])
            translate([0, 0, H - fillet_z[k + 1]])
                linear_extrude(height = fillet_z[k + 1] - fillet_z[k] + 0.005)
                    offset(r = -fillet_u[k])
                        outer_2d();
    }
}

module raised_fillet(h, fr, n = 16) {
    base = max(0.01, h - fr);
    linear_extrude(height = base) children();
    for (i = [0 : n - 1]) {
        z0 = base + fr * i / n;
        z1 = base + fr * (i + 1) / n;
        t = (i + 1) / n;
        inset = fr * (1 - sqrt(max(0, 1 - t * t)));
        translate([0, 0, z0])
            linear_extrude(height = z1 - z0 + 0.002)
                offset(r = -inset) children();
    }
}

// ---- bottom-face etch -------------------------------------------------
module _etch_ring(w) {
    difference() {
        children();
        offset(r = -w) children();
    }
}

module bottom_etch_2d() {
    _etch_ring(min(etch_width, inner_r * 0.35)) inner_ears_2d();
    _etch_ring(etch_width) eyes_2d();
    _etch_ring(min(etch_width, pupil_rx * 0.30)) pupils_2d();
    _etch_ring(etch_width) muzzle_2d();
    _etch_ring(etch_width) nose_2d();
    // The mouth is a line feature: a shallow groove follows the line.
    mouth_2d();
}

// ---- solid -------------------------------------------------------------
module bear_body() {
    difference() {
        bear_solid();
        // plain string-hole bore along X, centred at mid-thickness
        translate([0, 0, H / 2])
            rotate([0, 90, 0])
                cylinder(h = 2 * (R + extra), r = R_throat, center = true);
        // inner-ear pockets on the front face
        translate([0, 0, H - inner_recess])
            linear_extrude(height = inner_recess + 0.5)
                inner_ears_2d();
        // shallow build-plate etch
        translate([0, 0, -0.5])
            linear_extrude(height = etch_depth + 0.5)
                bottom_etch_2d();
    }
}

module bear_details() {
    difference() {
        union() {
            translate([0, 0, H])
                linear_extrude(height = eye_raise) eyes_2d();
            translate([0, 0, H])
                raised_fillet(muzzle_raise, muzzle_fillet) muzzle_2d();
        }
        // pupil holes, like the inner-ear pockets
        translate([0, 0, H + eye_raise - pupil_recess])
            linear_extrude(height = pupil_recess + 0.5) pupils_2d();
        // etched nose and mouth in the muzzle top
        translate([0, 0, H + muzzle_raise - nose_etch])
            linear_extrude(height = nose_etch + 0.5) nose_2d();
        translate([0, 0, H + muzzle_raise - mouth_etch])
            linear_extrude(height = mouth_etch + 0.5) mouth_2d();
    }
}

union() {
    bear_body();
    bear_details();
}
