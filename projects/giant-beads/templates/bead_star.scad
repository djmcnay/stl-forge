/*
    BEAD STAR - fresh parametric start (17 Oct 2026)
    =================================================
    Star/flower cross-section bead with a swept ball-fillet string hole
    and quarter-round face fillets (width/12). No letters, no rim, no
    preview colouring.

    Geometry source: the principal-supplied parametric star/flower generator
    (kept verbatim; provenance copy in parametric_star_flower.scad): unified
    star/flower radial profile with independent valley depth, fitted so the
    outline touches its enclosing circle at every outward tip, one tip
    pointing vertically up.

    width        enclosing-circle diameter of the star face (mm). Maps to
                 the generator's `diameter`.
    roundness    dial 1..20 (default 12): 1 = sharp star, 10 = bulbous,
                 20 = flower. Feeds the generator directly.
    points       integer >= 3, number of tips/petals.
    petal_depth  dial 1..10 (default 3): valley depth. This is the
                 principal's rename of the generator's `depth` (OpenSCAD
                 identifiers cannot contain a hyphen, so `petal_depth`,
                 not `petal-depth`). Mapped explicitly at the call site:
                 `depth = petal_depth`.
    height       extrusion height = width / 2 (computed)

    Shared mouth: a straight bore plus the swept rolling-ball mouth
    fillet (ported from bead_heart.scad); this file keeps its local
    values (hole_entry_x, hole_len, r_mouth) and builds the cutter in
    place.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width = 120;
roundness = 12;                // 1..20: 1 = sharp star, 10 = bulbous, 20 = flower
points = 5;                    // number of tips/petals
petal_depth = 3;               // 1..10: valley depth
height = width / 2;

// ---- string hole (common family block) ---------------------------------
// Throat diameter at the centre plane (mm)
hole_diameter = 20;
// Bell-mouth diameter at the entrances (mm): max(1.2 * throat, height / 2).
// Retained for presets; inert now that the mouth is a swept ball fillet.
hole_opening_diameter = max(hole_diameter * 1.2, height / 2);
// Flare arc radius (mm): family rule width / 8; retained, unused by the mouth.
bore_fillet_radius = width / 8;
// Face fillet radius (mm): quarter-round where each flat face meets the
// side wall (NOT a chamfer); family rule width / 12.
fillet_radius = width / 12;
// Derived hole values
R_throat = hole_diameter / 2;
R_open = hole_opening_diameter / 2;
extra = 5;                     // mm bore overshoot past both walls
// Mouth radius: same family dial as bead.scad / bead_heart.scad, plus a
// star wall-safe cap. The star outline runs only ~3.6 mm from the mouth
// edge to a concave valley and ~8.5 mm to the next tip (at the default
// 5-point, roundness-12 outline), so a tangent ball larger than about 1 mm
// cuts across the valley/tip. The cap scales with the outline: 1 mm at
// width 120.
r_mouth_max = (height / 2.25) - (fillet_radius + R_throat);
r_wall_max  = width / 120;
r_mouth     = max(0.5, min(0.5 * hole_diameter, r_mouth_max, r_wall_max));

// Smooth bore surfaces; the star outline is polygonal and unaffected by $fn.
$fn = 128;

// Mouth: swept rolling-ball fillet (ported from bead_heart.scad). The star
// wall is oblique to the bore axis, so the revolved well cannot be used;
// the 2D corner sliver is swept along the actual mouth edge instead.

// ==================================================
// 1. MATHEMATICAL HELPERS
// ==================================================

function clamp(x, lo, hi) =
    max(lo, min(hi, x));


function lerp(a, b, t) =
    a*(1-t) + b*t;


function smoothstep(t) =
    let(x = clamp(t, 0, 1))
    x*x*(3-2*x);


// ==================================================
// 2. AUTOMATIC STAR VALLEY RATIO
// ==================================================

/*
    Original inner/outer radius ratio.

    At depth=5, the generator preserves
    this automatically determined ratio.

    This keeps 5, 6, 8 and 10 pointed
    stars proportionally attractive.
*/

function star_valley_ratio(n) =
    1 - 1.05*sin(180/n);


// ==================================================
// 3. INDEPENDENT VALLEY DEPTH
// ==================================================

/*
    depth = 1:
        Inner radius = 88% of outer radius.

    depth = 5:
        Inner radius uses original
        automatic star proportions.

    depth = 10:
        Inner radius = 8% of outer radius.

    IMPORTANT:

    This function depends on points and depth.

    It does NOT depend on roundness.
*/

function star_inner_ratio(n, depth) =

    let(
        d = clamp(depth, 1, 10),

        base = star_valley_ratio(n)
    )

    d <= 5

        ? lerp(
            0.88,
            base,
            (d-1)/4
        )

        : lerp(
            base,
            0.08,
            (d-5)/5
        );


// ==================================================
// 4. SHARP STAR RADIAL PROFILE
// ==================================================

/*
    u=0: outward tip
    u=1: inner valley

    Calculates the exact radial intersection
    with the straight edge joining the tip
    and valley.

    This preserves straight polygon edges
    when roundness=1.
*/

function sharp_radius(u, n, valley) =

    let(
        a = 180/n,

        theta = a*u
    )

    valley*sin(a)
    /
    (
        valley*sin(a-theta)
        + sin(theta)
    );


// ==================================================
// 5. SMOOTH ANGULAR TRANSITION
// ==================================================

/*
    Smooths the curve near the outward
    tip and the inner valley.

    width=0:
        Original sharp star.

    width>0:
        Zero radial derivative at the
        tip and valley.

    Intermediate roundness values therefore
    progressively remove the sharp corners.

    The central portion of the interval
    is preserved.
*/

function smooth_angle(u, width) =

    width <= 0
    ? u

    : u < width
    ? (
        2*u*u/width
        - pow(u,3)/pow(width,2)
    )

    : u > 1-width
    ? let(v = 1-u)
        1 - (
            2*v*v/width
            - pow(v,3)/pow(width,2)
        )

    : u;


// ==================================================
// 6. UNIFIED STAR / FLOWER RADIAL PROFILE
// ==================================================

/*
    This is the main shape-generating function.

    Inputs:

        u          0..1
        n          Number of points
        roundness  1..20
        depth      1..10

    Returns a NORMALISED radius.

    The output is bounded by:

        valley <= radius <= 1

    Therefore the outline cannot extend
    beyond the enclosing circle.

    Depth controls the valley radius.

    Roundness controls the curvature.

    These are independent parameters.
*/

function star_radius(
    u,
    n,
    roundness,
    depth
) =

    let(

        r = clamp(roundness, 1, 20),

        // Independent valley depth
        valley = star_inner_ratio(
            n,
            depth
        ),

        // ----------------------------------
        // SHARP -> BULBOUS
        // Roundness 1..10
        // ----------------------------------

        q = clamp(
            (r-1)/9,
            0,
            1
        ),

        remapped_u = smooth_angle(
            u,
            0.32*q
        ),

        sharp = sharp_radius(
            remapped_u,
            n,
            valley
        ),

        bulbous =
            valley +
            (1-valley)*pow(
                cos(90*u),
                2
            ),

        original_star =
            (1-q)*sharp
            + q*bulbous,


        // ----------------------------------
        // BULBOUS -> FLOWER
        // Roundness 10..20
        // ----------------------------------

        t = smoothstep(
            (r-10)/10
        ),

        petal_power =
            2 + 2*t,

        flower =
            valley +
            (1-valley) *
            (
                1 -
                pow(
                    sin(90*u),
                    petal_power
                )
            )

    )

    r <= 10
        ? original_star
        : flower;


// ==================================================
// 7. GENERATE 2D STAR / FLOWER VERTICES
// ==================================================

/*
    Generates points around the complete
    outline.

    Each outward point is positioned
    exactly on the enclosing circle.

    The first point is vertically upwards.

    Each angular sector has:

        samples_per_half samples from
        the outer tip to the valley

        samples_per_half samples from
        the valley to the next outer tip

    Integer sample indices guarantee that
    every outward tip is included exactly.
*/

function star_vertices(
    diameter = 50,
    points = 5,
    roundness = 1,
    depth = 5,
    samples_per_half = 64
) =

    let(

        R = diameter/2,

        n = points,

        samples = max(
            8,
            floor(samples_per_half)
        ),

        total_samples =
            2*n*samples
    )

    [

        for (i = [0:total_samples-1])

            let(

                // Angular position
                theta =
                    360*i/total_samples,

                // Integer position within
                // the current star sector
                j = i % (2*samples),

                // 0 at outward tips,
                // 1 at valleys
                u =
                    min(
                        j,
                        2*samples-j
                    ) / samples,

                // Normalised radial profile
                radial_fraction =
                    star_radius(
                        u,
                        n,
                        roundness,
                        depth
                    ),

                // Scale to circle diameter
                radius =
                    R*radial_fraction,

                // Orient one tip vertically
                angle =
                    90-theta
            )

            [
                radius*cos(angle),
                radius*sin(angle)
            ]

    ];


// ==================================================
// 8. PRIMARY USER-FACING MODULE
// ==================================================

module star_2d(
    diameter = 50,
    points = 5,
    roundness = 1,
    depth = 5,
    samples_per_half = 64
) {

    assert(
        diameter > 0,
        "Diameter must be positive"
    )

    assert(
        points >= 3
        && points == floor(points),
        "Points must be an integer >= 3"
    )

    assert(
        roundness >= 1
        && roundness <= 20,
        "Roundness must be 1..20"
    )

    assert(
        depth >= 1
        && depth <= 10,
        "Depth must be 1..10"
    )

    polygon(
        points = star_vertices(
            diameter,
            points,
            roundness,
            depth,
            samples_per_half
        )
    );

}

// ---- geometry gates (compile-time checks on the bead parameters) --------
assert(width > 0, "width must be positive");
assert(points >= 3 && points == floor(points), "points must be an integer >= 3");
assert(roundness >= 1 && roundness <= 20, "roundness must be 1..20");
assert(petal_depth >= 1 && petal_depth <= 10, "petal_depth must be 1..10");
assert(height == width / 2, "height must compute to width / 2 exactly");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2 so fillets never overlap");

// ---- Plain string hole along X, centred on the cylinder (y=0, z=height/2) --
// hole_entry_x is the exact x where the outline crosses the hole centre line
// y=0 on the +x side, by linear interpolation between the outline vertices
// straddling it (or a vertex sitting exactly on y=0). Interpolating the true
// crossing, not taking max-x over a fixed |y|<tolerance band, is what makes
// this scale invariant. Verified exactly linear at width 60/120/240/300/480.
// At defaults (width 120, roundness 12, points 5, petal_depth 3) it is
// x = 49.7114, NOT 60.
//
// MOUTH: a straight 20 mm bore plus the swept rolling-ball fillet at both
// entrances (radius capped by the star wall-safe dial; see r_mouth above).
// The old spherical scoop, ball rollover, and revolved well are out.
star_pts = star_vertices(width, points, roundness, petal_depth);
L_pts = len(star_pts);
// index of the outline vertex nearest the hole axis on the +x side
// (max() over vectors is not portable OpenSCAD, so a two-pass scalar min):
min_y = min([for (i = [0 : L_pts - 1]) if (star_pts[i][0] > 0) abs(star_pts[i][1])]);
cross_i = [for (i = [0 : L_pts - 1]) if (star_pts[i][0] > 0 && abs(star_pts[i][1]) == min_y) i][0];
hole_entry_x = max([
    for (i = [0 : L_pts - 1])
        let(p0 = star_pts[i], p1 = star_pts[(i + 1) % L_pts])
        if (p0[0] > 0 && p1[0] > 0 && p0[1] * p1[1] <= 0 && !(p0[1] == 0 && p1[1] == 0))
            p0[1] == 0 ? p0[0]
                       : p0[0] + (p1[0] - p0[0]) * (0 - p0[1]) / (p1[1] - p0[1])
]);
assert(hole_entry_x > 0, "hole_entry_x must be positive: no +x outline crossing of y=0 found");
// the straight bore must clear every wall it can reach (the
// oblique flank pokes beyond the centre-line crossing):
wall_span_x = max([for (p = star_pts) if (abs(p[1]) <= R_open) p[0]]);
hole_len = wall_span_x + extra;
echo(star_hole_entry_x = hole_entry_x, star_hole_len = hole_len,
     star_r_mouth = r_mouth);

// ---- Ball-fillet mouth (ported from bead_heart.scad) ---------------------
// A true rolling-ball fillet: remove the material between the sharp edge
// and the ball of radius r_mouth tangent to both the bore and the
// wall. The 2D corner sliver is swept along the actual mouth edge, so it
// stays tangent to both surfaces even though the star wall is oblique.

// wall position and outward normal as functions of y on the +x side
function wall_x_at(y) =
    max([for (i = [0 : L_pts - 1])
        let(p0 = star_pts[i], p1 = star_pts[(i + 1) % L_pts])
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
mf_overlap = 0.2;                            // mm the sliver reaches into the bore
mf_n = 240;                                  // samples around the mouth edge
mf_arc = 16;                                 // samples across the fillet arc
mf_th = [for (i = [0 : mf_n - 1]) 360 * i / mf_n];
mf_E = [for (a = mf_th)
    [wall_x_at(R_throat * cos(a)), R_throat * cos(a),
     height / 2 + R_throat * sin(a)]];
mf_nb = [for (a = mf_th) [0, cos(a), sin(a)]];          // bore outward normal
mf_nw = [for (a = mf_th) wall_n_at(R_throat * cos(a))]; // wall outward normal
mf_c0 = [for (i = [0 : mf_n - 1]) vdot(mf_nb[i], mf_nw[i])];
mf_s0 = [for (i = [0 : mf_n - 1]) sqrt(max(1e-9, 1 - mf_c0[i] * mf_c0[i]))];
// in-plane axis perpendicular to the bore normal
mf_e2 = [for (i = [0 : mf_n - 1])
    vmul(vsub(mf_nw[i], vmul(mf_nb[i], mf_c0[i])), 1 / mf_s0[i])];

// One cross-section, perpendicular to the mouth edge: the edge point,
// a small strip that reaches into the bore (so the sliver and the bore
// cutter overlap instead of sharing a coplanar face), then the ball arc
// from the bore tangency (phi = 180) to the wall tangency
// (phi = acos(c0)). The polygon is exactly the sliver the fillet removes.
function mf_sec(i) =
    let(c0 = mf_c0[i], s0 = mf_s0[i], e1 = mf_nb[i], e2 = mf_e2[i],
        th = acos(max(-1, min(1, c0))),
        b_c = -mf_r * (1 + c0) / s0,
        tb = vadd(mf_E[i], vmul(e2, b_c)),
        e_in = vsub(mf_E[i], vmul(e1, mf_overlap)),
        tb_in = vsub(tb, vmul(e1, mf_overlap)))
    concat(
        [mf_E[i], e_in, tb_in],
        [for (k = [0 : mf_arc])
            let(phi = 180 - (180 - th) * k / mf_arc)
                vadd(mf_E[i],
                     vadd(vmul(e1, mf_r * (1 + cos(phi))),
                          vmul(e2, b_c + mf_r * sin(phi))))]
    );

mf_w = mf_arc + 4;                           // vertices per cross-section
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
// (the star is symmetric about x = 0).
module string_hole() {
    translate([0, 0, height / 2])
        bead_string_hole_plain(
            R_throat = R_throat,
            hole_len = hole_len);
    mf_cutter();
    mirror([1, 0, 0]) mf_cutter();
}

// ---- Fillet geometry: bead.scad's quarter arc, carried in z-slices -------
// bead.scad revolves one profile whose corners hold a 32-segment quarter arc.
// The star cannot revolve, so the SAME arc point set (same angles, same
// inscribed-chord convention: each slab takes the inset of its base point)
// drives uniform-erosion slices of the star outline instead. The star has
// CUSPS at its tips, so offset(r=-u) erosion is the correct inset primitive
// (hull() would fill the clefts); vertices are never hand-displaced.
n_fillet = 32;
c = fillet_radius;
side_len = height - 2 * c;          // straight wall band (bead.scad: H - 2*c)
fillet_u = [for (i = [0 : n_fillet]) c - c * cos(-90 + 90 * i / n_fillet)]; // inset from wall
fillet_z = [for (i = [0 : n_fillet]) c + c * sin(-90 + 90 * i / n_fillet)]; // z of arc point

// ---- deliverable: the star-face cylinder with the string hole ------------
// petal_depth (bead family name) maps to the generator's `depth` argument.
// One tip points vertically up (the generator orients it; no rotation here).
// Quarter-round face fillets at both faces (width/12), z = 0 base.
module star_body() {
    union() {
        // bottom fillet: slabs [z_i, z_i+1] with inset u_i (inscribed chords)
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z[i]])
                linear_extrude(height = fillet_z[i+1] - fillet_z[i])
                    offset(r = -fillet_u[i])
                        star_2d(diameter = width, points = points,
                                roundness = roundness, depth = petal_depth);
        // straight side wall; collapses like bead.scad when c == height/2
        if (side_len > 0.001)
            translate([0, 0, c])
                linear_extrude(height = side_len)
                    star_2d(diameter = width, points = points,
                            roundness = roundness, depth = petal_depth);
        // top fillet: mirrored slabs [H - z_k+1, H - z_k] with inset u_k
        for (k = [0 : n_fillet - 1])
            translate([0, 0, height - fillet_z[k+1]])
                linear_extrude(height = fillet_z[k+1] - fillet_z[k])
                    offset(r = -fillet_u[k])
                        star_2d(diameter = width, points = points,
                                roundness = roundness, depth = petal_depth);
    }
}

difference() {
    star_body();
    string_hole();
}
