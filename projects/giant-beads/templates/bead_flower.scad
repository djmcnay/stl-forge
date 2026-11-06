/*
    BEAD FLOWER - step 4: tripled petal fillets, stigma at width / 2.2
    ============================================================
    Flower bead whose petals come from the generator's unified star/flower
    radial profile (templates/bead_star.scad, reused UNMODIFIED via `use`)
    and carry the family's quarter-round face fillets as the erosion-slab
    stack (bottom fillet slabs, straight mid-body, mirrored top slabs, SAME
    n_fillet = 32), now at the TRIPLED petal fillet radius width / 4
    (30 mm at width 120; the family doubling history: 2x at width / 6 in
    step 3, 3x at width / 4 in step 4, both principal-ordered 22 Oct 2026,
    FLOWER-ONLY: the family default stays width / 12 in bead.scad,
    bead_heart.scad and bead_star.scad, none of which this step touches).
    At width / 4 the petal fillet radius equals height / 2 exactly
    (30 = 60 / 2), so the two fillet bands meet at mid-height and the
    petals stand fully half-round in silhouette: the straight mid band
    collapses (the legal equality case of the petal fillet <= height / 2
    assert). That inset is in PLAN, so at low and high z a large erosion
    inset may strand the petals from the stigma disc; the union is verified
    one connected solid by a components count on the render (CGAL arbiter
    on any split) and REPORTED, never tuned by radius changes.
    The central stigma cylinder (width / 2.2 = 54.545 mm at width 120; the
    step-3 width / 3 and the superseded width / 2.5 correction are both
    replaced by this consolidated step-4 order) now carries ITS OWN
    quarter-round face fillets from the SAME erosion-slab construction over
    the stigma circle outline at stigma_fillet_radius = width / 12
    (10 mm at 120: the ORDINARY family fillet on the stigma top, no dome
    construction: a flat top face of radius 54.545 / 2 - 10 = 17.27 mm
    tangent to the rounded edge), also built BEFORE the union in the same
    z band 0..height. flower_body() unions the whole filleted petal solid
    with the whole filleted stigma solid, and the shared v2 string hole
    from bead_common.scad is subtracted as before.
    No cluster, no preset wiring, no main.py changes.

    width         120  outline driver, mm; petals' enclosing circle diameter
    width_stigma 54.5  stigma cylinder diameter, mm (width / 2.2;
                       54.545 mm at width 120)
    roundness      20  petal roundness dial 1..20 (20 = full petals)
    points          6  petal count, integer >= 3, one tip points up
    petal_depth     8  valley depth dial 1..10
    hole_diameter  20  string hole throat diameter, mm (the family hole)
    height          60  extrusion height, mm = width / 2 (family rule)
    fillet_radius  30  PETAL face fillet radius, mm (width / 4; tripled
                       from the family width / 12, 2x at step 3 and 3x at
                       step 4, both principal-ordered 22 Oct 2026,
                       FLOWER-ONLY)
    stigma_fillet_radius 10  stigma face fillet radius, mm (width / 12,
                       the ordinary family fillet on the stigma top first,
                       boss order 22 Oct 2026; flat top face radius
                       width_stigma / 2 - 10 = 17.27 mm at the defaults)

    Shared mouth: the plain bore module in bead_common.scad (just a
    hole). This file keeps only its local values (hole_entry_x,
    hole_len, ...) and forwards them to the call, EXACTLY as
    bead_star.scad does. Local rule: hole_entry_x is computed from
    THIS template's own UNION outline crossing at y = 0, never a
    pinned number, by scanning BOTH outlines (star polygon and the
    $fn-matched stigma circle) and taking the outermost interpolated
    crossing. At the defaults the petal valley on the +x axis dips
    inside the stigma, so the crossing is the stigma's own wall at
    width_stigma/2; on dial settings where the petal flank reaches
    past the stigma the crossing is the star's oblique flank.
*/

use <bead_star.scad>
use <bead_common.scad>

// ---- parameters --------------------------------------------------------
width = 120;              // outline driver, mm; petals' enclosing circle diameter
roundness = 20;           // petal roundness dial 1..20 (20 = full petals)
points = 6;               // petal count, integer >= 3
petal_depth = 8;          // valley depth dial 1..10
hole_diameter = 20;       // string hole throat diameter, mm
width_stigma = width / 2.2; // stigma cylinder diameter, mm (54.545 at 120;
                            // width / 2.5 correction superseded, step 4)
height = width / 2;       // extrusion height, mm (family rule)

// ---- string hole (ported family values) ---------------------------------
// Throat diameter at the centre plane (mm)
// Bell-mouth diameter at the two entrances (mm): greater of throat*1.2 or height/2
hole_opening_diameter = max(hole_diameter * 1.2, height / 2);
// Flare arc radius (mm), family rule width/8 (unused: the hole is plain)
bore_fillet_radius = width / 8;
// Smooth bore surfaces; the petal outline is polygonal and unaffected by $fn
$fn = 128;

// ---- face fillets (mirrored from templates/bead.scad) --------------------
// Quarter-round where each flat face meets the side wall (NOT a chamfer).
// Family default: fillet_radius = width / 12  ->  10 mm at width 120.

// Mouth: JUST A HOLE (bead_string_hole_plain, bead_common.scad).
// PETAL fillet TRIPLED to width / 4 (30 mm at 120): 2x at width / 6 in
// step 3, 3x at width / 4 in step 4, principal-ordered 22 Oct 2026,
// FLOWER-ONLY; the family default stays width / 12 in bead.scad /
// bead_heart.scad / bead_star.scad (do NOT touch those). 30 = height / 2:
// the two fillet bands meet at mid-height, so the petal silhouette is
// fully half-round (the legal equality case of the fillet <= height / 2
// assert; note the large plan insets this carries, verified below).
// STIGMA fillet STAYS at the family default width / 12 (10 mm at 120:
// "normal fillet on the stigma top first", boss order 22 Oct 2026), so the
// enlarged 54.545 mm disc ends in a 17.27 mm flat top face, NOT a dome.
fillet_radius = width / 4;           // petals: tripled (3x), principal order 22 Oct 2026
stigma_fillet_radius = width / 12;   // stigma: family default, ordinary top fillet
// No r_mouth dial: this template's mouth is a plain bore.

// ---- geometry gates -----------------------------------------------------
assert(width > 0, "width must be positive");
assert(points >= 3 && points == floor(points), "points must be an integer >= 3");
assert(roundness >= 1 && roundness <= 20, "roundness must be 1..20");
assert(petal_depth >= 1 && petal_depth <= 10, "petal_depth must be 1..10");
assert(height == width / 2, "height must compute to width / 2 exactly");
assert(width_stigma > 0, "width_stigma must be positive");
assert(width_stigma < width, "width_stigma must be < width");
assert(hole_diameter > 0, "hole_diameter must be positive");
assert(width_stigma > hole_diameter, "stigma must clear the throat bore");
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2 so fillets never overlap");
assert(stigma_fillet_radius > 0, "stigma_fillet_radius must be positive");
assert(stigma_fillet_radius <= width_stigma / 2, "stigma_fillet_radius must be <= width_stigma/2");
assert(stigma_fillet_radius <= height / 2, "stigma_fillet_radius must be <= height/2 so the stigma fillets never overlap");

// ---- union outline y=0 (+x) crossing: outermost of both outlines wins ----
extra = 5;   // mm bore overshoot past both walls (family value)
R_stigma = width_stigma / 2;

// petals: the generator's outline vertices, reused verbatim
star_pts = star_vertices(width, points, roundness, petal_depth);
L_star = len(star_pts);

// stigma: the $fn-matched circle points (the cylinder's own tessellation),
// included in the polygon scan so the wall crossing is interpolated the
// same way the star's is
circle_pts = [for (i = [0 : $fn - 1])
              let(a = 360 * i / $fn) [R_stigma * cos(a), R_stigma * sin(a)]];
L_circ = len(circle_pts);

// interpolated y=0 (+x) crossing of one outline, bead_star's pairs scan:
// consecutive vertices straddling the line, linear interpolation between
// them (or a vertex sitting exactly on y = 0)
function outline_crossing(pts) =
    max([
        for (i = [0 : len(pts) - 1])
            let(p0 = pts[i], p1 = pts[(i + 1) % len(pts)])
            if (p0[0] > 0 && p1[0] > 0 && p0[1] * p1[1] <= 0
                && !(p0[1] == 0 && p1[1] == 0))
                p0[1] == 0 ? p0[0]
                           : p0[0] + (p1[0] - p0[0]) * (0 - p0[1]) / (p1[1] - p0[1])
    ]);

cross_star = outline_crossing(star_pts);
cross_circ = outline_crossing(circle_pts);
// the union's crossing is the outermost of the two:
hole_entry_x = max(cross_star, cross_circ);
assert(hole_entry_x > 0, "hole_entry_x must be positive: no +x union crossing of y=0 found");

// the straight bore must clear every wall it can reach
R_open = hole_opening_diameter / 2;
wall_span_x = max(
    max([for (p = star_pts)   if (abs(p[1]) <= R_open) p[0]]),
    max([for (p = circle_pts) if (abs(p[1]) <= R_open) p[0]]));
hole_len = wall_span_x + extra;
echo(flower_hole_entry_x = hole_entry_x, flower_cross_star = cross_star,
     flower_cross_stigma = cross_circ, flower_hole_len = hole_len);

// ---- fillet geometry: bead.scad's quarter arc, carried in z-slices -------
// bead.scad revolves one profile whose corners hold a 32-segment quarter arc.
// The star cannot revolve, so the SAME arc point set (same angles, same
// inscribed-chord convention: each slab takes the inset of its base point)
// drives uniform-erosion slices of the star outline instead. The star has
// CUSPS at its tips, so offset(r=-u) erosion is the correct inset primitive
// (hull() would fill the clefts); vertices are never hand-displaced.
n_fillet = 32;
// slab z-step: petals c / n_fillet = 30 / 32 = 0.9375 mm,
//              stigma sc / n_fillet = 10 / 32 = 0.3125 mm (n_fillet kept 32)
c = fillet_radius;
side_len = height - 2 * c;          // petal straight wall band (bead.scad: H - 2*c);
                                    // 0 at c = height / 2: the two fillet bands meet
fillet_u = [for (i = [0 : n_fillet]) c - c * cos(-90 + 90 * i / n_fillet)]; // inset from wall
fillet_z = [for (i = [0 : n_fillet]) c + c * sin(-90 + 90 * i / n_fillet)]; // z of arc point

// stigma arc tables: the SAME formulas, the SAME slab count n_fillet = 32
// and the SAME z band 0..height, driven by the stigma's own radius
// (10 mm; the petals now run 30 mm, so the two stacks are NOT shared tables)
sc = stigma_fillet_radius;
side_len_s = height - 2 * sc;       // stigma straight wall band
fillet_u_s = [for (i = [0 : n_fillet]) sc - sc * cos(-90 + 90 * i / n_fillet)]; // inset from stigma wall
fillet_z_s = [for (i = [0 : n_fillet]) sc + sc * sin(-90 + 90 * i / n_fillet)]; // z of arc point

// ---- body: filleted petals, THEN the filleted stigma cylinder (one solid) -
// Step-4 construction: petal_body() stands alone as the erosion-slab stack
// over the star outline with the TRIPLED quarter-round face fillets at
// both faces (width / 4 = 30 mm at defaults, n_fillet = 32 kept). The union
// with the filleted stigma solid happens only AFTER that filleted petal
// solid exists, and the stigma is fully built with its own z band
// 0..height before the union as well. With c = height / 2 the straight
// mid band vanishes: the bottom and top fillet slabs abut exactly at
// z = height / 2. The 30 mm plan insets can leave the petals detached
// from the stigma disc in low and high z bands (their valley at 14.28 is
// deep inside the enlarged stigma wall at 27.27); this is verified by a
// components count on the render and REPORTED, never hand-tuned.
module petal_body() {
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

module stigma_body() {
    // central stigma cylinder with ITS OWN quarter-round face fillets: the
    // SAME erosion-slab construction over the stigma circle outline (bottom
    // + top stacks exactly like the petals', same slab count and arc
    // formulas, same z band 0..height), built BEFORE the union. The circle
    // is convex, so offset(r = -u) erosion is the plain inward inset of it
    // (no cusps on this outline).
    union() {
        // bottom fillet: slabs [z_i, z_i+1] with inset u_i (inscribed chords)
        for (i = [0 : n_fillet - 1])
            translate([0, 0, fillet_z_s[i]])
                linear_extrude(height = fillet_z_s[i+1] - fillet_z_s[i])
                    offset(r = -fillet_u_s[i])
                        circle(r = R_stigma);
        // straight side wall; collapses like bead.scad when sc == height/2
        if (side_len_s > 0.001)
            translate([0, 0, sc])
                linear_extrude(height = side_len_s)
                    circle(r = R_stigma);
        // top fillet: mirrored slabs [H - z_k+1, H - z_k] with inset u_k
        for (k = [0 : n_fillet - 1])
            translate([0, 0, height - fillet_z_s[k+1]])
                linear_extrude(height = fillet_z_s[k+1] - fillet_z_s[k])
                    offset(r = -fillet_u_s[k])
                        circle(r = R_stigma);
    }
}

module flower_body() {
    // step-4 union order unchanged in KIND: the whole (tripled-fillet)
    // petal solid first, then the whole filleted stigma solid joins it;
    // each solid is fully built with its own z band 0..height before the
    // union. The enlarged stigma wall (r = 27.27 at defaults) stands
    // proud of the petal valley (crossing 14.28), but the petals' 30 mm
    // plan insets may strand their low/high z bands from the disc: the
    // union connection is NOT assumed any more, it is verified by a
    // components count on the defaults render (CGAL arbiter on a split)
    // and reported.
    union() {
        petal_body();
        stigma_body();
    }
}

// ---- shared mouth, just a hole ---------------------------------------------
module string_hole() {
    translate([0, 0, height / 2])
        bead_string_hole_plain(
            R_throat = hole_diameter / 2,
            hole_len = hole_len);
}

// ---- deliverable: the flower bead with the string hole, z = 0 base ------
difference() {
    flower_body();
    string_hole();
}
