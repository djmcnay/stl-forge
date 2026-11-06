/*
    BEAD HEART - fresh parametric start (16 Oct 2026)
    =================================================
    Heart cross-section bead: plain extruded outline, no letters. The
    string hole (v2 spherical countersink, sunk along the local wall
    normal - see the "String hole" section below and the difference()
    at the bottom of the file) came later, so this file DOES carry a
    hole despite the original "no hole, no rim" plan.

    Geometry source: the supplied ChatGPT parametric heart generator (kept
    verbatim; provenance copy in parametric_heart_reference.scad): cubic Bezier
    profiles for a sharp and a bubble heart, linear control-point
    interpolation, fitted so the heart touches its enclosing circle at the
    bottom tip and at two symmetrical upper-lobe shoulder points.

    width    enclosing-circle diameter of the heart face (mm)
    bubble   dial 1..10 (default 5): 1 = sharp/elongated, 10 = full bubble.
             roundness = (bubble - 1) / 9, clamped, feeds the generator.
    height   extrusion height = width / 2.2 (computed)

    Shared mouth: the v2 countersink is one common subtractive module in
    bead_common.scad (see its provenance block); this file keeps only its
    local values (hole_entry_x, n_out, hole_len, ...) and forwards them to
    the call. The heart outline below stays per-template.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width  = 120;
bubble = 5;
height = width / 2.2;

// ---- string hole (ported from templates/bead.scad) -----------------------
// Throat diameter at the centre plane (mm)
hole_diameter = 20;
// Bell-mouth diameter at the two entrances (mm): greater of throat*1.2 or height/2
hole_opening_diameter = max(hole_diameter * 1.2, height / 2);
// Flare arc radius (mm), default width/8 (bead.scad rule)
bore_fillet_radius = width / 8;
// Smooth bore surfaces; the heart outline is polygonal and unaffected by $fn.
$fn = 128;

// ---- face fillets (mirrored from templates/bead.scad) --------------------
// Quarter-round where each flat face meets the side wall (NOT a chamfer).
// bead.scad default: fillet_radius = width / 12  ->  10 mm at width 120.
fillet_radius = width / 12;

// Mouth default for this template is the SPHERE countersink
// (bead_string_hole, sunk along the local wall normal) — the well revolve
// cannot be tangent to this oblique heart flank and wedges a fin into the
// rim (see bead_common.scad wall-normal constraint). The well remains the
// letter-bead (bead.scad) default where the wall is flat/perpendicular.

// ---- mathematical helpers (verbatim from reference) --------------------
function clamp01(x) = max(0, min(1, x));

function lerp(a, b, t) = a * (1-t) + b*t;

function bezier(c, t) =
    c[0] * pow(1-t, 3) +
    c[1] * (3 * pow(1-t, 2) * t) +
    c[2] * (3 * (1-t) * t*t) +
    c[3] * pow(t, 3);

// ---- reference control points (RIGHT half, Y increases DOWNWARDS) ------
function sharp_controls() = [
    [[0.000, 0.130],[0.045, 0.035],[0.120, 0.000],[0.235, 0.000]],
    [[0.235, 0.000],[0.385, 0.000],[0.500, 0.095],[0.500, 0.275]],
    [[0.500, 0.275],[0.500, 0.435],[0.440, 0.490],[0.345, 0.585]],
    [[0.345, 0.585],[0.210, 0.710],[0.075, 0.830],[0.000, 0.930]]
];

function bubble_controls() = [
    [[0.000, 0.075],[0.060, 0.075],[0.125, 0.000],[0.235, 0.000]],
    [[0.235, 0.000],[0.405, 0.000],[0.500, 0.130],[0.500, 0.295]],
    [[0.500, 0.295],[0.500, 0.440],[0.440, 0.540],[0.345, 0.635]],
    [[0.345, 0.635],[0.170, 0.825],[0.090, 0.910],[0.000, 0.910]]
];

// ---- interpolation ------------------------------------------------------
function heart_controls(roundness) =
    let(a = sharp_controls(), b = bubble_controls(), q = clamp01(roundness))
    [for (i = [0:3]) [for (j = [0:3]) lerp(a[i][j], b[i][j], q)]];

function heart_side(t, controls) =
    let(segment = min(3, floor(t*4)), local_t = t*4 - segment)
    bezier(controls[segment], local_t);

function heart_raw(roundness = 0, resolution = 512) =
    let(controls = heart_controls(roundness), n = max(256, floor(resolution)))
    concat(
        [for (i = [0:n]) heart_side(i/n, controls)],
        [for (i = [n-1:-1:1]) let(p = heart_side(i/n, controls)) [-p[0], p[1]]]
    );

// ---- enclosing-circle fit: bottom tip + both upper lobes touch ---------
function heart_circle_center_y(raw, bottom_y) =
    min([
        for (p = raw)
            if (p[1] < bottom_y - 1e-9)
                (bottom_y*bottom_y - p[0]*p[0] - p[1]*p[1]) / (2 * (bottom_y-p[1]))
    ]);

function heart_points(r = 25, roundness = 0, resolution = 512) =
    let(
        raw = heart_raw(roundness, resolution),
        bottom_y = max([for (p = raw) p[1]]),
        centre_y = heart_circle_center_y(raw, bottom_y),
        raw_radius = bottom_y - centre_y,
        scale_factor = r / raw_radius
    )
    [for (p = raw) [p[0] * scale_factor, (centre_y-p[1]) * scale_factor]];

// ---- user-facing modules -----------------------------------------------
module heart_2d(r = 25, roundness = 0, resolution = 512) {
    assert(r > 0, "Heart radius must be positive")
        polygon(points = heart_points(r, roundness, resolution));
}

module heart_in_circle(w = 50, roundness = 0, resolution = 512) {
    heart_2d(r = w/2, roundness = roundness, resolution = resolution);
}

// ---- bubble dial: 1..10 -> roundness 0..1 --------------------------------
roundness = clamp01((bubble - 1) / 9);

assert(width > 0, "width must be positive");
assert(hole_opening_diameter > hole_diameter, "hole_opening_diameter must exceed hole_diameter for a tapered (flared) hole");
assert(hole_opening_diameter < width, "hole opening must fit within the face");
assert(hole_diameter < width, "hole throat must fit within the face");
assert(hole_opening_diameter < height, "hole opening must fit vertically within the bead height");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2 so fillets never overlap");

// ---- String hole: spherical countersink on the LOCAL wall normal (v2) -------
// Ported from bead_star (43db29b, 17 Oct 2026) at David's request: every bead
// family now shares the same mouth procedure. The heart flank is an oblique,
// overhanging tip flank, so the countersink is a sphere sunk along the LOCAL
// wall normal at the y=0 crossing, NOT a revolve about the bore axis (that
// was the bead_star v1 defect: a bore-axis countersink wedges a fin into the
// rim on an oblique wall). A sphere meets any smooth wall in smooth curves,
// so the rim cannot grow a fin. Rim radius = hole_opening_diameter exactly.
// The heart outline is mirror-symmetric about the y axis, so the -x scoop is
// the yz-mirror of the +x one. The crossing uses the same scale-invariant
// interpolated rule as bead_star (band-style max-x measurement is scale
// dependent and would drift the rim by up to ~0.55 mm).
// bore_fillet_radius is retained as a bead-family parameter; its bell-flare
// role is played by the spherical scoop.
assert(hole_opening_diameter > hole_diameter, "hole_opening_diameter must exceed hole_diameter");
assert(hole_opening_diameter < width, "hole opening must fit within the face");
assert(hole_diameter < width, "hole throat must fit within the face");

extra = 5;                                   // mm scoop sink and bore overshoot
R_open = hole_opening_diameter / 2;

// crossing + local wall frame from the outline vertices (recomputed per
// bubble): scalar two-pass argmin because max() over vectors is not portable
// OpenSCAD, and this build has no normalize():
hz_pts = heart_points(width / 2, roundness);
hz_L = len(hz_pts);
hz_min_y = min([for (i = [0 : hz_L - 1]) if (hz_pts[i][0] > 0) abs(hz_pts[i][1])]);
hz_cross_i = [for (i = [0 : hz_L - 1]) if (hz_pts[i][0] > 0 && abs(hz_pts[i][1]) == hz_min_y) i][0];
hole_entry_x = max([
    for (i = [0 : hz_L - 1])
        let(p0 = hz_pts[i], p1 = hz_pts[(i + 1) % hz_L])
        if (p0[0] > 0 && p1[0] > 0 && p0[1] * p1[1] <= 0 && !(p0[1] == 0 && p1[1] == 0))
            p0[1] == 0 ? p0[0]
                       : p0[0] + (p1[0] - p0[0]) * (0 - p0[1]) / (p1[1] - p0[1])
]);
assert(hole_entry_x > 0, "hole_entry_x must be positive: no +x outline crossing of y=0 found");
hz_tan = hz_pts[(hz_cross_i + 2) % hz_L] - hz_pts[(hz_cross_i + hz_L - 2) % hz_L];
hz_mag = sqrt(hz_tan[0] * hz_tan[0] + hz_tan[1] * hz_tan[1]);
n_tan = [hz_tan[1] / hz_mag, -hz_tan[0] / hz_mag];
n_out = n_tan[0] > 0 ? n_tan : [-n_tan[0], -n_tan[1]];
half = hole_entry_x;
k_scoop = extra;
R_ball = sqrt(R_open * R_open + k_scoop * k_scoop); // rim radius exactly R_open
assert(R_ball <= height / 2, "countersink sphere must fit within the bead height");
assert(k_scoop > 0, "scoop sink must be positive");
// the straight bore must clear every wall the opening disc can reach (the
// oblique flank pokes beyond the centre-line crossing):
hz_wall_span_x = max([for (p = hz_pts) if (abs(p[1]) <= R_open) p[0]]);
hole_len = hz_wall_span_x + extra;
scoop_dx = -k_scoop * n_out[0];
scoop_dy = -k_scoop * n_out[1];
echo(bead_heart_entry_x = hole_entry_x, bead_heart_normal = n_out, bead_heart_hole_len = hole_len);

// Shared mouth: v2 sphere countersink is the default for this oblique wall
// (well revolve grazes it and fins). Geometry cut lives in bead_common.scad.
module string_hole() {
    translate([0, 0, height / 2])
        bead_string_hole(
            hole_entry_x = hole_entry_x,
            n_out = n_out,
            R_throat = R_throat,
            R_open = R_open,
            k = k_scoop,
            hole_len = hole_len);
}

// ---- Fillet geometry: bead.scad's quarter arc, carried in z-slices -------
// bead.scad revolves one profile whose corners hold a 32-segment quarter arc.
// The heart cannot revolve, so the SAME arc point set (same angles, same
// inscribed-chord convention: each slab takes the inset of its base point)
// drives uniform-erosion slices of the heart outline instead.
n_fillet = 32;
c = fillet_radius;
side_len = height - 2 * c;          // straight wall band (bead.scad: H - 2*c)
fillet_u = [for (i = [0 : n_fillet]) c - c * cos(-90 + 90 * i / n_fillet)]; // inset from wall
fillet_z = [for (i = [0 : n_fillet]) c + c * sin(-90 + 90 * i / n_fillet)]; // z of arc point

module heart_body() {
    union() {
        // bottom fillet: slabs [z_i, z_i+1] with inset u_i (inscribed chords)
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z[i]])
                linear_extrude(height = fillet_z[i+1] - fillet_z[i])
                    offset(r = -fillet_u[i])
                        heart_in_circle(w = width, roundness = roundness);
        // straight side wall; collapses like bead.scad when c == height/2
        if (side_len > 0.001)
            translate([0, 0, c])
                linear_extrude(height = side_len)
                    heart_in_circle(w = width, roundness = roundness);
        // top fillet: mirrored slabs [H - z_k+1, H - z_k] with inset u_k
        for (k = [0 : n_fillet - 1])
            translate([0, 0, height - fillet_z[k+1]])
                linear_extrude(height = fillet_z[k+1] - fillet_z[k])
                    offset(r = -fillet_u[k])
                        heart_in_circle(w = width, roundness = roundness);
    }
}

// ---- deliverable: the heart-face cylinder with the string hole ------------
difference() {
    heart_body();
    string_hole();
}
