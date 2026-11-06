/*
    PARAMETRIC HEART GENERATOR (REFERENCE)
    ======================================
    Author-provided reference implementation. Compile this file directly to
    see five example hearts; it is the geometry source for the build brief.

    r          Radius of enclosing circle
    roundness  0 = sharp heart, 1 = bubble heart
    resolution Number of outline samples per half
*/

// 1. MATHEMATICAL HELPERS

function clamp01(x) = max(0, min(1, x));

function lerp(a, b, t) = a * (1-t) + b*t;

// Cubic Bezier evaluation. Supports 2D vector control points.
function bezier(c, t) =
    c[0] * pow(1-t, 3) +
    c[1] * (3 * pow(1-t, 2) * t) +
    c[2] * (3 * (1-t) * t*t) +
    c[3] * pow(t, 3);

// 2. SHARP HEART CONTROL POINTS (RIGHT HALF, Y increases DOWNWARDS)

function sharp_controls() = [
    [[0.000, 0.130],[0.045, 0.035],[0.120, 0.000],[0.235, 0.000]],
    [[0.235, 0.000],[0.385, 0.000],[0.500, 0.095],[0.500, 0.275]],
    [[0.500, 0.275],[0.500, 0.435],[0.440, 0.490],[0.345, 0.585]],
    [[0.345, 0.585],[0.210, 0.710],[0.075, 0.830],[0.000, 0.930]]
];

// 3. BUBBLE HEART CONTROL POINTS

function bubble_controls() = [
    [[0.000, 0.075],[0.060, 0.075],[0.125, 0.000],[0.235, 0.000]],
    [[0.235, 0.000],[0.405, 0.000],[0.500, 0.130],[0.500, 0.295]],
    [[0.500, 0.295],[0.500, 0.440],[0.440, 0.540],[0.345, 0.635]],
    [[0.345, 0.635],[0.170, 0.825],[0.090, 0.910],[0.000, 0.910]]
];

// 4. INTERPOLATE CONTROL POINTS

function heart_controls(roundness) =
    let(a = sharp_controls(), b = bubble_controls(), q = clamp01(roundness))
    [for (i = [0:3]) [for (j = [0:3]) lerp(a[i][j], b[i][j], q)]];

// 5. EVALUATE THE RIGHT HALF

function heart_side(t, controls) =
    let(segment = min(3, floor(t*4)), local_t = t*4 - segment)
    bezier(controls[segment], local_t);

// 6. COMPLETE RAW OUTLINE (right half + mirrored left half)

function heart_raw(roundness = 0, resolution = 512) =
    let(controls = heart_controls(roundness), n = max(256, floor(resolution)))
    concat(
        [for (i = [0:n]) heart_side(i/n, controls)],
        [for (i = [n-1:-1:1]) let(p = heart_side(i/n, controls)) [-p[0], p[1]]]
    );

// 7. FIT A CIRCLE TOUCHING THREE POINTS

function heart_circle_center_y(raw, bottom_y) =
    min([
        for (p = raw)
            if (p[1] < bottom_y - 1e-9)
                (bottom_y*bottom_y - p[0]*p[0] - p[1]*p[1]) / (2 * (bottom_y-p[1]))
    ]);

// 8. FITTED HEART VERTICES (circle centred at origin, radius r, bottom at [0,-r])

function heart_points(r = 25, roundness = 0, resolution = 512) =
    let(
        raw = heart_raw(roundness, resolution),
        bottom_y = max([for (p = raw) p[1]]),
        centre_y = heart_circle_center_y(raw, bottom_y),
        raw_radius = bottom_y - centre_y,
        scale_factor = r / raw_radius
    )
    [for (p = raw) [p[0] * scale_factor, (centre_y-p[1]) * scale_factor]];

// 9. USER-FACING MODULES

module heart_2d(r = 25, roundness = 0, resolution = 512) {
    assert(r > 0, "Heart radius must be positive")
        polygon(points = heart_points(r, roundness, resolution));
}

module heart_in_circle(w = 50, roundness = 0, resolution = 512) {
    heart_2d(r = w/2, roundness = roundness, resolution = resolution);
}

// 10. EXAMPLE PREVIEW (reference file only)

preview_examples = true;

if (preview_examples) {
    $fn = 256;
    radius = 25;
    for (i = [0:4]) {
        q = i/4;
        translate([(i-2)*60, 0]) {
            color([0.7, 0.7, 0.7]) difference() { circle(r=radius); circle(r=radius-0.2); }
            color([0.25, 0.25, 0.25]) heart_2d(r = radius, roundness = q);
        }
    }
}

// ============================================================
// VALIDATION BLOCK (reference spec section 5) - NOT part of the
// deliverable; copy this block into a scratch validation file.
// Expected: radial_error ~0, bottom_error ~0, touches = true.
// ============================================================
/*
test_radius = 25;
for (q = [0, 0.25, 0.5, 0.75, 1]) {
    pts = heart_points(r = test_radius, roundness = q, resolution = 512);
    distances = [for (p = pts) norm(p)];
    radial_max = max(distances);
    bottom = min([for (p = pts) p[1]]);
    upper_right_contacts = [for (p = pts) if (p[0] > 0 && p[1] > 0 && abs(norm(p)-test_radius) < 0.02) p];
    upper_left_contacts  = [for (p = pts) if (p[0] < 0 && p[1] > 0 && abs(norm(p)-test_radius) < 0.02) p];
    echo(roundness = q, radial_error = radial_max-test_radius, bottom_error = bottom+test_radius,
         upper_right_touch = len(upper_right_contacts) > 0, upper_left_touch = len(upper_left_contacts) > 0);
}
*/
