/*
    BEAD STAR - fresh parametric start (17 Oct 2026)
    =================================================
    Star/flower cross-section bead with a bell-mouth string hole and
    quarter-round face fillets (width/12). No letters, no rim, no
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

    Shared mouth: the v2 construction is one common subtractive module in
    bead_common.scad (see its provenance block); this file keeps only its
    local values (hole_entry_x, n_out, hole_len, ...) and forwards them to
    the call. The flank recompute below stays per-template.
*/
use <bead_common.scad>

// ---- parameters -------------------------------------------------------
width = 120;
roundness = 12;
points = 5;
petal_depth = 3;
height = width / 2;

// ---- string hole (ported from templates/bead.scad) -----------------------
// Throat diameter at the centre plane (mm)
hole_diameter = 20;
// Bell-mouth diameter at the two entrances (mm): greater of throat*1.2 or height/2
hole_opening_diameter = max(hole_diameter * 1.2, height / 2);
// Flare arc radius (mm), default width/8 (bead.scad rule)
bore_fillet_radius = width / 8;
// Smooth bore surfaces; the star outline is polygonal and unaffected by $fn.
$fn = 128;

// ---- face fillets (mirrored from templates/bead.scad) --------------------
// Quarter-round where each flat face meets the side wall (NOT a chamfer).
// bead.scad default: fillet_radius = width / 12  ->  10 mm at width 120.
fillet_radius = width / 12;

// Mouth default for this template is the SPHERE countersink
// (bead_string_hole, sunk along the local wall normal) — the well revolve
// cannot be tangent to this oblique star flank and wedges a fin into the
// rim (see bead_common.scad wall-normal constraint). The well remains the
// letter-bead (bead.scad) default where the wall is flat/perpendicular.

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

// ---- Bell-mouth string hole along X, centred on the cylinder (y=0, z=height/2) --
// hole_entry_x is the exact x where the outline crosses the hole centre line
// y=0 on the +x side, by linear interpolation between the outline vertices
// straddling it (or a vertex sitting exactly on y=0). Interpolating the true
// crossing, not taking max-x over a fixed |y|<tolerance band, is what makes
// this scale invariant. Verified exactly linear at width 60/120/240/300/480.
// At defaults (width 120, roundness 12, points 5, petal_depth 3) it is
// x = 49.7114, NOT 60.
//
// MOUTH CONSTRUCTION (v2 - spherical countersink along the LOCAL wall normal).
// The star flank at y=0 is an OBLIQUE, overhanging tip flank: it tilts sharply
// away from the crossing on the valley side, so a countersink revolved about
// the BORE axis touches the wall at one grazing point and wedges a sharp fin
// into the mouth rim (the teardrop-with-fin defect seen in the first render).
// Instead each mouth is countersunk the machinist's way: a sphere sunk along
// the LOCAL wall normal at the crossing, so the opening rim is smooth on the
// wall (a sphere meets any smooth wall in smooth curves - no fin can exist),
// the 30 mm scoop rim scales with hole_opening_diameter exactly, and the
// funnel blends continuously into the 20 mm throat bore along X.
//   rim radius = R_open exactly: sphere sqrt(R_open^2 + k^2) sunk k along n_out
//   scoop centre = crossing plane minus k * outward wall normal
// bore_fillet_radius is retained as a bead-family parameter; its bell role is
// played here by the spherical scoop.
extra = 5;                                   // mm scoop sink and bore overshoot
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
tangent_v = star_pts[(cross_i + 2) % L_pts] - star_pts[(cross_i + L_pts - 2) % L_pts];
// unit wall normal (this OpenSCAD build has no normalize(); sign fixed +x):
t_mag = sqrt(tangent_v[0] * tangent_v[0] + tangent_v[1] * tangent_v[1]);
n_tan = [tangent_v[1] / t_mag, -tangent_v[0] / t_mag];
n_out = n_tan[0] > 0 ? n_tan : [-n_tan[0], -n_tan[1]];
R_throat = hole_diameter / 2;
R_open = hole_opening_diameter / 2;
half = hole_entry_x;
k_scoop = extra;
R_ball = sqrt(R_open * R_open + k_scoop * k_scoop); // rim radius exactly R_open
assert(k_scoop > 0, "scoop depth must be positive");
assert(R_ball <= height / 2, "scoop sphere must fit within the bead height");
// the straight bore must clear every wall the opening disc can reach (the
// oblique flank pokes beyond the centre-line crossing):
wall_span_x = max([for (p = star_pts) if (abs(p[1]) <= R_open) p[0]]);
hole_len = wall_span_x + extra;
scoop_dx = -k_scoop * n_out[0];
scoop_dy = -k_scoop * n_out[1];
echo(star_hole_entry_x = hole_entry_x, star_wall_normal = n_out, star_hole_len = hole_len);

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
