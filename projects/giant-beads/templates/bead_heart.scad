/*
    BEAD HEART - fresh parametric start (16 Oct 2026)
    =================================================
    Heart cross-section bead: plain extruded outline, no letters. The
    string hole (bore with a rolling-ball rim fillet - see the "String
    hole" section below and the difference() at the bottom of the file)
    came later, so this file DOES carry a hole despite the original
    "no hole, no rim" plan.

    Geometry source: the supplied ChatGPT parametric heart generator (kept
    verbatim; provenance copy in parametric_heart_reference.scad): cubic Bezier
    profiles for a sharp and a bubble heart, linear control-point
    interpolation, fitted so the heart touches its enclosing circle at the
    bottom tip and at two symmetrical upper-lobe shoulder points.

    width      enclosing-circle diameter of the heart face (mm)
    roundness  dial 1..10 (default 5): 1 = sharp/elongated, 10 = full bubble.
               Mapped to the generator's 0..1 profile blend.
    height     extrusion height = width / 2 (computed)

    Shared mouth: the string hole and its rim treatment are local to this
    file (the heart's wall is not perpendicular to the bore axis, so the
    letter bead's revolved well does not fit). The heart outline below
    stays per-template.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width     = 120;
roundness = 5;                 // 1..10: 1 = sharp/elongated, 10 = full bubble
height    = width / 2;

// ---- string hole (common family block) ---------------------------------
// Throat diameter at the centre plane (mm)
hole_diameter = 20;
// Flare arc radius (mm): family rule width / 8; retained, unused by the mouth.
bore_fillet_radius = width / 8;
// Face fillet radius (mm): quarter-round where each flat face meets the
// side wall (NOT a chamfer); family rule width / 12.
fillet_radius = width / 12;
// Derived hole values
R_throat = hole_diameter / 2;
extra = 5;                     // mm bore overshoot past both walls
// Mouth radius: face-fillet-safe ceiling (height / 2.25) minus the face
// fillet and the throat radius, floored at 0.5 mm. 6.667 mm at defaults.
r_mouth_max = (height / 2.25) - (fillet_radius + R_throat);
r_mouth = max(0.5, min(0.5 * hole_diameter, r_mouth_max));

// Smooth bore surfaces; the heart outline is polygonal and unaffected by $fn.
$fn = 128;

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

// ---- roundness dial: 1..10 -> generator 0..1 -----------------------------
roundness01 = clamp01((roundness - 1) / 9);

assert(width > 0, "width must be positive");
assert(hole_diameter < width, "hole throat must fit within the face");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2 so fillets never overlap");

// ---- String hole: bore + rolling-ball rim fillet --------------------------
// The heart wall at the mouth is the vertical extrusion of the heart
// outline, so the correct G1 mouth is a ball of radius r_mouth
// rolled along the bore/wall edge. The cut is the sweep of the 2D corner
// sliver (edge point + ball arc) along that edge, which keeps the fillet
// tangent to BOTH surfaces all the way round. This replaces the revolved
// well: the well only stays tangent where the wall is perpendicular to
// the bore axis, and the heart's flank moves ~7 mm in x across the mouth
// (wall x is 49.1 at y = -13 but 56.4 at y = +13), which is exactly
// what produced the teardrop lip and the fin.
// bore_fillet_radius is retained as a bead-family parameter, unused.

// crossing + local wall frame from the outline vertices (recomputed per
// roundness dial): scalar two-pass argmin because max() over vectors is not
// portable OpenSCAD, and this build has no normalize():
hz_pts = heart_points(width / 2, roundness01);
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
assert(r_mouth > 0, "mouth fillet collapsed: height too small for this hole");
// the straight bore must clear every wall it can reach (the
// oblique flank pokes beyond the centre-line crossing):
hz_wall_span_x = max([for (p = hz_pts) if (abs(p[1]) <= R_throat + r_mouth) p[0]]);
hole_len = hz_wall_span_x + extra;
echo(bead_heart_entry_x = hole_entry_x, bead_heart_r_mouth = r_mouth, bead_heart_hole_len = hole_len);

// ---- Ball-fillet mouth ----------------------------------------------------
// A true rolling-ball fillet: at both mouths, remove the material between
// the sharp edge and the ball of radius r_mouth that is tangent to
// both the bore and the wall. The cut is the sweep of that 2D corner
// sliver along the mouth edge, so the fillet stays tangent to BOTH
// surfaces all the way round even though the heart's wall is oblique to
// the bore axis. This is the difference from the revolved well, which is
// only tangent where the wall is perpendicular to the bore axis and so
// left the teardrop lip / fin.

// wall position and outward normal as functions of y on the +x lobe
function wall_x_at(y) =
    max([for (i = [0 : hz_L - 1])
        let(p0 = hz_pts[i], p1 = hz_pts[(i + 1) % hz_L])
        if (p0[0] > 0 && p1[0] > 0 && p0[1] != p1[1] &&
            (p0[1] - y) * (p1[1] - y) <= 0)
            p0[0] + (p1[0] - p0[0]) * (y - p0[1]) / (p1[1] - p0[1])]);

// outward wall normal from a finite difference of the outline (smoother
// than a single polygon segment; the y-increasing tangent gives
// n = (t.y, -t.x))
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

mf_r = r_mouth;
mf_n = 240;                                  // samples around the mouth edge
mf_arc = 16;                                 // samples across the fillet arc
mf_th = [for (i = [0 : mf_n - 1]) 360 * i / mf_n];
mf_E = [for (a = mf_th)
    [wall_x_at(R_throat * cos(a)), R_throat * cos(a),
     height / 2 + R_throat * sin(a)]];
mf_nb = [for (a = mf_th) [0, cos(a), sin(a)]];         // bore outward normal
mf_nw = [for (a = mf_th) wall_n_at(R_throat * cos(a))]; // wall outward normal
mf_c0 = [for (i = [0 : mf_n - 1]) vdot(mf_nb[i], mf_nw[i])];
mf_s0 = [for (i = [0 : mf_n - 1]) sqrt(max(1e-9, 1 - mf_c0[i] * mf_c0[i]))];
// in-plane axis perpendicular to the bore normal
mf_e2 = [for (i = [0 : mf_n - 1])
    vmul(vsub(mf_nw[i], vmul(mf_nb[i], mf_c0[i])), 1 / mf_s0[i])];

// One cross-section, perpendicular to the mouth edge: the edge point,
// then the ball arc from the bore tangency (phi = 180) to the wall
// tangency (phi = acos(c0)). The polygon is exactly the sliver the
// fillet removes.
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

mf_w = mf_arc + 2;                           // vertices per cross-section
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

// Shared mouth: straight bore + the swept ball fillet at both mouths
// (the heart is symmetric about x = 0).
module string_hole() {
    translate([0, 0, height / 2])
        rotate([0, 90, 0])
            cylinder(h = 2 * (hole_entry_x + extra), r = R_throat, center = true);
    mf_cutter();
    mirror([1, 0, 0]) mf_cutter();
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
                        heart_in_circle(w = width, roundness = roundness01);
        // straight side wall; collapses like bead.scad when c == height/2
        if (side_len > 0.001)
            translate([0, 0, c])
                linear_extrude(height = side_len)
                    heart_in_circle(w = width, roundness = roundness01);
        // top fillet: mirrored slabs [H - z_k+1, H - z_k] with inset u_k
        for (k = [0 : n_fillet - 1])
            translate([0, 0, height - fillet_z[k+1]])
                linear_extrude(height = fillet_z[k+1] - fillet_z[k])
                    offset(r = -fillet_u[k])
                        heart_in_circle(w = width, roundness = roundness01);
    }
}

// ---- deliverable: the heart-face cylinder with the string hole ------------
difference() {
    heart_body();
    string_hole();
}
