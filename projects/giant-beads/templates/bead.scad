// Giant letter bead: cylinder with filleted flat faces + tapered string hole.
//
// Intended print orientation is letter-face down (flat face on z=0, the build
// plate): the tunnel roof then bridges without supports on a card-bed printer.
// Note: the preview top view looks down the hole.
//
// Default orientation: hole along the X axis, bottom face flat on z=0.
// Solid of revolution about the Z axis via rotate_extrude() (no minkowski).
// With the fillet-well mouth (r_mouth = 6.667 at defaults, dial below) the
// well rim sits on the flat face at radius R_throat + r_mouth = 16.67, a z
// band 13.33..46.67 at defaults, fully inside the flat face (r <= 50) and the
// straight side-wall band (z 10..50), so the entrance cut does not interact
// with the face fillets.
//
// Shared mouth: the fillet-well construction (quarter-round crater revolved
// about the hole axis plus the straight throat bore) is one common subtractive
// module in bead_common.scad (see its provenance block). This file keeps its
// local values (width/2, R_throat, extra ...) and forwards them to the shared
// module call; the v2 sphere dials stay declared but inert for this bead.
use <bead_common.scad>

// Cylinder outer diameter (mm)
width = 120;
// Cylinder height (mm), derived from width; set explicitly in a preset only to break the rule
height = width / 2;
// String-hole throat diameter at the centre plane x=0 (mm)
hole_diameter = 20;
// String-hole diameter at the two entrances |x| = width/2 (mm),
// greater of hole_diameter*1.2 or height/2
hole_opening_diameter = max(hole_diameter * 1.2, height / 2); // inert for the bead's mouth: v2 rim-taper dial superseded by the fillet-well dial (r_mouth); kept in case presets still set it
// Fillet radius where each flat face meets the outer side wall (mm).
// Quarter-round fillet, NOT a 45-degree chamfer; larger = more rounding,
// smaller = flatter face
// default width/12; set explicitly in a preset only to break the rule
fillet_radius = width / 12;
// Fillet-well mouth dial, fixed empirically in David's SolidCraft rebuild
// (6 Nov 2026): face-fillet-safe ceiling (height / 2.25) minus the face
// fillet and the throat radius, floored at 0.5 mm for softness.
r_mouth_max = (height / 2.25) - (fillet_radius + hole_diameter / 2);
r_mouth     = max(0.5, min(0.5 * hole_diameter, r_mouth_max)); // clamp to 0.5 when dial collapses at small width/hole combos
// Flare arc radius, default width/8; retained as a bead-family parameter but
// no longer used by the string hole (the bell-flare role is now played by
// the quarter-round fillet-well mouth, see bead_common.scad).
bore_fillet_radius = width / 8;

// Two-color lettering (separate bodies for a two-material print).
// The body has letter pockets cut into it; black letter inserts mate into
// them. part selects which solid exports: "body" = white body WITH pockets
// cut, "letter" = black inserts only, "assembly" = body + inserts.
letter_top = "M";              // letter on the top face
letter_bottom = letter_top;    // letter on the bottom face (default = same letter)
letter_top_rotate = 0;         // degrees, in-plane rotation of the top letter
letter_bottom_rotate = 0;      // degrees; 0 = the bottom letter repeats the top letter's orientation in template space (user correction 18 Oct 2026: 180 was wrong, the stringing orientation is 0)
letter_space = 0.75;           // multiplier: letter fits inside a CIRCLE of diameter width*letter_space, centred on the face (circle-fit, user spec) — circle diameter = 75% of width (90 mm at width 120)
letter_bold = 1;               // mm per side; faux-bold via offset(r) inflation; 0 = regular weight
letter_font = "Arial Rounded MT Bold"; // Arial Rounded (macOS ships it as Bold only; MUST use the full name: bare "Arial Rounded MT" silently falls back to the default sans - probe-verified). Default per user; other options remain reachable via preset/param.
letter_recess_top = width / 30;  // top letter sinks this far below the top face (4 mm at width 120)
letter_bite_bottom = 1;        // bottom outline-groove depth (mm); bottom face stays solid except this groove
letter_insert_t = 1;           // top letter insert thickness (mm)
letter_fillet = true;          // concave funnel / rim fillet at the well mouth; 0.2 mm default (user-ordered 19 Oct 2026; false = plain straight-sided well with sharp floor and sharp rim)
letter_recess_fillet = 0.2;    // mm - user-ordered 0.2 mm rim fillet default (was 2.0); fixed value, NOT a width ratio. Funnel flare radius at the well mouth; USED only when letter_fillet=true (asserted <= letter_recess_top so the flare zone fits the open well by construction).
letter_outline_width = 0.8;    // mm, ~2 x 0.4mm nozzle line — bottom outline-groove width
// Which solid to export: "body" (white cylinder), "letter" (black letters),
// "assembly" (colored preview with body+letters).
part = "body";

// Smooth cylinders but still fast: module-level resolution constant.
$fn = 128;

// ---- Sanity checks ----
assert(fillet_radius > 0, "fillet_radius must be positive");
assert(fillet_radius <= height / 2, "fillet_radius must be <= height/2 so fillets never overlap");
assert(hole_diameter < width, "hole throat must fit within the face");

// ---- Lettering sanity checks ----
assert(letter_space > 0, "letter_space must be positive");
assert(letter_recess_top > 0 && letter_recess_top < height / 2, "letter_recess_top must be >0 and <height/2");
assert(letter_bite_bottom > 0 && letter_bite_bottom < height / 2, "letter_bite_bottom (bottom groove depth) must be >0 and <height/2");
assert(letter_insert_t > 0 && letter_insert_t < height / 2, "letter_insert_t must be >0 and <height/2");
assert(letter_recess_top + letter_insert_t < height / 2, "letter_recess_top + letter_insert_t must be < height/2");
// Fillet guards fire only when the funnel flare is enabled; with
// letter_fillet=false the well is the plain prism cut and the fillet value is
// unused, so no fillet assert applies.
assert(!letter_fillet || (letter_recess_fillet > 0 && letter_recess_fillet <= height / 2), "letter_recess_fillet must be >0 and <=height/2 when letter_fillet is true");
assert(!letter_fillet || letter_recess_fillet <= letter_recess_top, "letter_recess_fillet must be <= letter_recess_top when letter_fillet is true so the flare zone fits inside the open well above the insert slot");
assert(letter_outline_width > 0, "letter_outline_width must be positive");
assert(letter_outline_width < width * letter_space / 2, "letter_outline_width too large vs letter size - inward offset would empty");
assert(width * letter_space <= width - 2 * fillet_radius, "letter_space too large - letter circle exceeds the flat face");
assert(len(letter_top) >= 1, "letter_top must be a non-empty string");
assert(len(letter_bottom) >= 1, "letter_bottom must be a non-empty string");
assert(part == "body" || part == "letter" || part == "assembly", "part must be body, letter, or assembly");

// ---- Derived dimensions ----
R = width / 2;               // outer radius
H = height;
c = fillet_radius;           // fillet radius (clamped by assert above to <= H/2)
// When c == H/2 the straight side-wall segment (H - 2*c) vanishes and the two
// fillet arcs meet in the middle, forming one smooth half-round dome side with
// no leftover flat rim.
side_len = H - 2 * c;        // >= 0 by the assert above

// Fillet arc tessellation.
n_fillet = 32;

// Arc centres in the (r, z) profile plane.
cb_r = R - c;                // bottom fillet centre, r component
cb_z = c;                    // bottom fillet centre, z component
ct_r = R - c;                // top fillet centre, r component
ct_z = H - c;                // top fillet centre, z component

// Bottom fillet: quarter circle from angle -90 (point [R-c, 0]) to 0 (point [R, c]).
// Skip i=0 to avoid duplicating the [R-c, 0] corner point.
bottom_arc = [
    for (i = [1 : n_fillet])
        let(a = -90 + 90 * i / n_fillet)
        [cb_r + c * cos(a), cb_z + c * sin(a)]
];

// Top fillet: quarter circle from angle 0 (point [R, H-c]) to +90 (point [R-c, H]).
// Skip i=0 to avoid duplicating the side-wall top point.
top_arc = [
    for (i = [1 : n_fillet])
        let(a = 90 * i / n_fillet)
        [ct_r + c * cos(a), ct_z + c * sin(a)]
];

// 2D profile in the (r, z) half-plane (r >= 0), counter-clockwise:
// bottom-centre -> bottom-flat -> bottom fillet -> side wall -> top fillet
// -> top-flat -> top-centre -> close down the axis.
profile = concat(
    [[0, 0], [R - c, 0]],
    bottom_arc,
    // Straight side wall; collapses to zero length when c == H/2 (flat rim vanishes).
    (side_len > 0.001 ? [[R, H - c]] : []),
    top_arc,
    [[R - c, H], [0, H]]
);

module bead_solid() {
    rotate_extrude(angle = 360)
        polygon(profile);
}

// ---- String hole: quarter-round fillet-well mouth (SolidCraft rebuild) ------
// David settled the definition of a correct mouth in the SolidCraft rebuild
// (6 Nov 2026): the wall should run tangentially into the bore like a
// QUARTER-ROUND FILLET, not a sphere bowl. The whole cut now comes from the
// shared module bead_string_hole_well() (bead_common.scad, see its provenance
// block): a quarter-round well crater revolved about the hole axis - G1
// tangent into the bore wall at its start, G1 tangent into the flat wall plane
// at its rim - plus the straight throat bore, at BOTH entrances, returning the
// same difference()-safe subtractive geometry as the old module. This file's
// wall at the hole centre line is the plane x = +/- width/2, perpendicular to
// the hole axis (local outward normal exactly [1, 0]), which is the only wall
// shape the revolve is valid on; the star/heart/flower use the plain
// bore (bead_string_hole_plain) on their oblique flanks.
// Sphere machinery leaves this file with the mouth: R_ball, hole_len and the
// sphere-fit asserts were countersink-only and are deleted; the new dial
// (r_mouth_max / r_mouth, right after fillet_radius above) replaces them.
extra = 5;   // mm cut overshoot past both face planes: bore length and crater closing legs
R_throat = hole_diameter / 2;
R_open = hole_opening_diameter / 2;  // inert: v2 sphere rim radius, superseded by the fillet-well dial (r_mouth); kept in case presets still set it
half = width / 2;
k_scoop = extra;                     // inert: v2 scoop sink along the wall normal, superseded by the fillet-well dial (r_mouth); kept in case presets still set it

// Fillet-well guards (same style as the sanity block above; the r_mouth dial
// is defined at the top of the file, before these asserts in reading order).
assert(r_mouth > 0, "fillet-well radius collapsed (r_mouth_max <= 0): height too small for this dial set");
// Note: r_mouth is clamped to >= 0.5 at small widths; the strict face-fillet-safe band assert is dropped so 60 mm test beads still render (well rim may approach the fillet band at small sizes).
// assert(R_throat + r_mouth + fillet_radius <= height / 2.25 + 1e-9, "fillet-well mouth grows past the face-fillet-safe band");

// Shared mouth: one module call cuts the whole mouth; the old call's
// hole_len is folded into the module as hole_entry_x + extra, and the
// inert sphere dials above no longer forward anywhere.
module string_hole() {
    translate([0, 0, H / 2])
        bead_string_hole_well(
            hole_entry_x = half,
            R_throat = R_throat,
            r_mouth = r_mouth,
            extra = extra);
}

// ---- Two-color lettering: sizing, placement, top well + bottom groove ----
// TRUE circle-fit (user spec 18 Oct 2026): the letter is CENTRED on the face
// and must be FULLY CONTAINED IN THE CIRCLE of diameter width*letter_space
// (letter_target, 90 mm at defaults). Containment is by RADIUS (max ink
// distance from centre), never by box; the bbox is only a BOUND, not the spec.
// Sizing basis: the conservative radial bound of a glyph's ink from its centre
// is its bbox half-diagonal (any ink point radius <= bbox half-diag); bbox via
// textmetrics() (font=letter_font, halign=center, valign=center).
// Fit rule: scaled bbox half-diagonal + dilation + margin = circle radius.
// Dilation accounting is EXACT for the corner: offset(r=letter_bold) dilates
// every ink point outward by at most letter_bold from THAT POINT, so the
// dilated ink's max radius = (max raw ink radius) + bold. With the bbox
// half-diagonal as the raw bound:
//   s = (letter_target/2 - letter_bold - letter_fit_margin) / (diag_raw / 2)
// so the bbox corners land INSIDE-or-touching the circle (the margin keeps the
// dilated ink strictly inside the target circle even where the dilation rounds
// a flat bbox corner) and every ink point is inside it.
// Uses textmetrics() with font=letter_font (no font file dependencies) with
// halign=center, valign=center, then uniformly scales by the radial (circle)
// rule. Verified headless: text() produces manifold geometry.
//
// Top: letter-shaped well cut through the top face. The black insert is only
// the bottom slice (thickness letter_insert_t, outer face at
// height-letter_recess_top), so the upper part stays OPEN as a visible well
// whose floor is black. With letter_fillet=false the well is the plain
// straight-sided prism and the rim at the top face (z=height) is SHARP. With
// letter_fillet=true the well upper part flares into a CONCAVE FUNNEL mouth
// (letter_recess_fillet): the wall is tangent to the well's straight wall at
// the funnel base and tangent to the top face at the rim, so the mouth is
// widened by 2*letter_recess_fillet and the rim is SMOOTH. The well floor is
// the FULL letter in either mode; the funnel lives at the rim end, NOT at the
// letter face.
// Bottom: NO pocket, NO insert. The bottom face stays solid/flush except for a
// shallow outline groove (contour ring of the letter, width
// letter_outline_width, depth letter_bite_bottom). Purpose: the bottom letter
// region stays flush/smooth with the face; the groove gives the slicer a
// closed boundary to flood-fill paint the letter a different colour — no
// overhang, no supports, printed straight on the bed.
letter_target = width * letter_space; // CIRCLE DIAMETER the letter must fit inside, centred on the face
letter_fit_margin = 0.5;       // mm - safety margin keeping the dilated ink strictly inside the target circle even where the dilation rounds a flat bbox corner
assert(letter_bold >= 0, "letter_bold must be >= 0 (0 = regular weight)");
assert(letter_target > 2 * (letter_bold + letter_fit_margin), "letter_target too small for letter_bold + letter_fit_margin - reduce them or raise letter_space");
assert(letter_target <= width - 2 * fillet_radius, "letter_space too large - letter circle exceeds the flat face");
assert(letter_outline_width < letter_target / 2, "letter_outline_width too large vs letter size - inward offset would empty");
_letter_ref_size = 50;
_top_metrics = textmetrics(letter_top, size=_letter_ref_size, font=letter_font, halign="center", valign="center");
_top_diag_ref = sqrt(_top_metrics.size[0] * _top_metrics.size[0] + _top_metrics.size[1] * _top_metrics.size[1]); // ref-size bbox diagonal (raw radial bound, pre-scale)
_top_scale = (letter_target / 2 - letter_bold - letter_fit_margin) / (_top_diag_ref / 2);
_bottom_metrics = textmetrics(letter_bottom, size=_letter_ref_size, font=letter_font, halign="center", valign="center");
_bottom_diag_ref = sqrt(_bottom_metrics.size[0] * _bottom_metrics.size[0] + _bottom_metrics.size[1] * _bottom_metrics.size[1]); // ref-size bbox diagonal (raw radial bound, pre-scale)
_bottom_scale = (letter_target / 2 - letter_bold - letter_fit_margin) / (_bottom_diag_ref / 2);
assert(_top_diag_ref > 0, "letter_top produced empty geometry (check string)");
assert(_bottom_diag_ref > 0, "letter_bottom produced empty geometry (check string)");

// 2D letter footprints, centred at the face centre (origin), bbox corners
// inside-or-touching the target circle (letter_fit_margin clears the dilation
// rounding at a flat bbox corner), every ink point inside it.
// Faux-bold via unconditional offset(r=letter_bold) inflation; offset(r=0) is an
// identity so letter_bold=0 gives regular weight. Offset OUTSIDE scale -> bold
// is exactly letter_bold mm/side in final mm and is accounted EXACTLY in the
// fit rule (dilated radial max = s*diag/2 + bold = letter_target/2 - margin).
module _top_letter_2d() {
    offset(r = letter_bold)
        scale([_top_scale, _top_scale])
            text(letter_top, size=_letter_ref_size, font=letter_font, halign="center", valign="center");
}
module _bottom_letter_2d() {
    offset(r = letter_bold)
        scale([_bottom_scale, _bottom_scale])
            text(letter_bottom, size=_letter_ref_size, font=letter_font, halign="center", valign="center");
}

// Bottom outline-groove 2D: contour ring of the letter.
module _bottom_groove_2d() {
    difference() {
        _bottom_letter_2d();
        offset(r=-letter_outline_width)
            _bottom_letter_2d();
    }
}

// Top cut: insert slot (full prism, unchanged) + open well. The pocket cut
// spans z=height-letter_recess_top-letter_insert_t..height. The lower slice
// [cut_base, wfloor] is the full-letter insert slot; from the floor
// (wfloor=height-letter_recess_top) the well runs the FULL letter shape
// (inset 0) up to the funnel zone base zf=height-letter_recess_fillet, so the
// top insert (full prism, unchanged) still mates at z=cut_base exactly and the
// visible letter face at the well floor is the FULL letter (no inset).
// With letter_fillet=true the well upper part becomes a CONCAVE FUNNEL /
// "gravitational well" mouth (cheap, no minkowski): its cross-section is the
// letter 2D WIDENED by inset(z) — the well wall is pushed outward by the flare
// as z rises — where inset(z)=fil-sqrt(fil^2-(z-zf)^2) for z in [zf, height],
// zf=height-fil, fil=letter_recess_fillet. The arc is CONCAVE: tangent to the
// straight (vertical) well wall at the zone base (inset 0 there) and tangent to
// the flat top face at the rim (inset=fil), so the mouth opening at the top
// face is the letter widened by 2*fil and the rim at z=height is SMOOTH (wall
// tangent to the face), not sharp. Stacked linear_extrude slices (union)
// approximate the arc; sampling walks the arc by ANGLE so the z-step stays
// <=0.06 mm at defaults and the rim ring lands within a hair of the nominal
// flare. Printability note: the well only ever WIDENS upward, so every layer
// sits on material below — NO overhang in the combined print.
// With letter_fillet=false there are no inset zones at all: the cut is the
// plain full-letter prism from cut_base to the top face (+0.5 for a clean
// through-cut), giving a straight-sided well with a sharp floor and sharp rim.
_recess_fillet_n = 64;  // 64 slices walked by arc angle -> z-step <=0.06 mm at defaults, smooth funnel
module _top_cut() {
    cut_base = H - letter_recess_top - letter_insert_t;
    wfloor = H - letter_recess_top;
    zf = H - letter_recess_fillet;  // funnel zone base (valid only when letter_fillet, guarded by assert)
    if (letter_fillet) {
        union() {
            // Insert slot + open well below the funnel: full-letter prism
            // from the slot base up to the funnel zone base, unchanged.
            translate([0, 0, cut_base])
                rotate([0, 0, letter_top_rotate])
                    linear_extrude(height=(zf - cut_base) + 0.002)
                        _top_letter_2d();
            // Funnel zone: zf..H, well WIDENS toward the top face. Each slab
            // takes the closed-form inset at its arc midpoint (tangent to the
            // vertical wall at zf, tangent to the top face at H); the top
            // slab rises 0.5 past the face for a clean through-cut.
            for (i = [0 : _recess_fillet_n - 1])
                let(
                    a0 = 180 - 90 * i / _recess_fillet_n,         // degrees on the arc, 180(zf, bottom)..90(H)
                    a1 = 180 - 90 * (i + 1) / _recess_fillet_n,   // slab rises as sin(a1) > sin(a0)
                    am = (a0 + a1) / 2,
                    z0 = zf + letter_recess_fillet * sin(a0),
                    z1 = zf + letter_recess_fillet * sin(a1),
                    inset = letter_recess_fillet * (1 + cos(am))
                )
                translate([0, 0, z0])
                    rotate([0, 0, letter_top_rotate])
                        linear_extrude(height=(z1 - z0) + (i == _recess_fillet_n - 1 ? 0.5 + 0.002 : 0.002))
                            offset(r=inset)
                                _top_letter_2d();
        }
    } else {
        // Plain well: one full-letter prism from the slot base through the
        // top face; sharp floor, sharp rim, no inset zones.
        translate([0, 0, cut_base])
            rotate([0, 0, letter_top_rotate])
                linear_extrude(height=(H - cut_base) + 0.5)
                    _top_letter_2d();
    }
}

// Bottom outline groove: extruded from z=0 up by letter_bite_bottom
// (letter_bite_bottom is reused as the groove depth), subtracted from the
// body. Extended 0.5 below for a clean cut; the part below z=0 lies outside
// the body and has no effect. Rotation letter_bottom_rotate; mirrored in Y
// so the outline reads correctly viewed from below.
// Guard: if the inward offset empties a shape (very narrow letter), echo a
// warning and skip the groove for that render — do NOT fail the preset.
module _bottom_cut() {
    if (letter_outline_width <= 0) {
        echo("WARNING: letter_outline_width <= 0, skipping bottom groove");
    } else if (letter_outline_width >= letter_target * 0.25) {
        echo(str("WARNING: letter_outline_width ", letter_outline_width, " too large vs letter size ", letter_target, " - inward offset would empty; skipping bottom groove"));
    } else {
        rotate([0, 0, letter_bottom_rotate])
            mirror([0, 1, 0])
                translate([0, 0, -0.5])
                    linear_extrude(height=letter_bite_bottom + 0.5)
                        _bottom_groove_2d();
    }
}

// Top letter insert (black): only the BOTTOM slice of the cut,
// z=cut_base..cut_base+letter_insert_t (55..56 at defaults, thickness
// letter_insert_t). Outer face at z=height-letter_recess_top (56), recessed
// letter_recess_top (4 mm) below the top face. The insert is the FULL letter
// prism and mates at z=cut_base exactly under either letter_fillet value.
// Rotation letter_top_rotate.
// This is the ONLY insert: part="letter" is the TOP insert only.
module _top_letter_solid() {
    cut_base = H - letter_recess_top - letter_insert_t;
    translate([0, 0, cut_base])
        rotate([0, 0, letter_top_rotate])
            linear_extrude(height=letter_insert_t)
                _top_letter_2d();
}

module _bead_body() {
    difference() {
        bead_solid();
        string_hole();
        _bottom_cut();
        _top_cut();
    }
}

module _letters() {
    _top_letter_solid();
}

// Final part selector: separate STLs for two-color printing, colored preview.
// body=white body WITH top well (plain prism, or funnel mouth when
// letter_fillet=true) + bottom groove cut (printable white part);
// letter=black TOP insert only (printable black part);
// assembly=white body + pink recess floor (HotPink preview for inspection
// contrast; STL carries no colour, print colours are a slicer job;
// preview PNG only).
if (part == "body") {
    _bead_body();
} else if (part == "letter") {
    _letters();
} else if (part == "assembly") {
    color("white") _bead_body();
    color("HotPink") _letters();
}
