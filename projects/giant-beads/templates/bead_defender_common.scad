// Shared 2D etch helpers for the Defender bead pair.
// All coordinates are in the bead face plane; etch grooves are shallow.

module etch_line(p0, p1, w = 0.8) {
    hull() {
        translate(p0) circle(r = w / 2);
        translate(p1) circle(r = w / 2);
    }
}

module etch_polyline(pts, w = 0.8) {
    for (i = [0 : len(pts) - 2])
        etch_line(pts[i], pts[i + 1], w);
}

module etch_loop(pts, w = 0.8) {
    etch_polyline(concat(pts, [pts[0]]), w);
}

module etch_rect(x0, y0, x1, y1, w = 0.8) {
    etch_loop([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], w);
}

module etch_ring(c, r, w = 0.8) {
    translate(c)
        difference() {
            circle(r = r + w / 2);
            circle(r = r - w / 2);
        }
}

module etch_arc(c, r, a0, a1, w = 0.8, n = 48) {
    for (i = [0 : n - 1])
        etch_line(
            c + [r * cos(a0 + (a1 - a0) * i / n),
                 r * sin(a0 + (a1 - a0) * i / n)],
            c + [r * cos(a0 + (a1 - a0) * (i + 1) / n),
                 r * sin(a0 + (a1 - a0) * (i + 1) / n)],
            w);
}

module etch_spokes(c, r0, r1, count, phase = 0, w = 0.8) {
    for (i = [0 : count - 1])
        etch_line(
            c + [r0 * cos(phase + 360 * i / count),
                 r0 * sin(phase + 360 * i / count)],
            c + [r1 * cos(phase + 360 * i / count),
                 r1 * sin(phase + 360 * i / count)],
            w);
}
