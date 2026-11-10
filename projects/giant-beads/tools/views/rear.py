"""Rear elevation of the Defender 90 - every per-view number lives here.

A view module is pure data: the frame, probe geometry for the recolour pass, the
ink edits the principal asked for, and the clean sketch model.  The engines
(`part_map.py`, `bead_sketch.py`) contain no view-specific numbers, so a second
view (side, front) is a new file in this folder plus an entry in
`views/__init__.py` - see `tools/README.md` for the walk-through.

Coordinates are overlay pixels: origin top-left, y down, in the frame of
`OVERLAY`.  That frame is the photograph scaled 2x with no offset, which is why
the sketch lands on the photo without any fitting.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REFDIR = os.path.normpath(os.path.join(HERE, "..", "..", "references", "defender"))

NAME = "rear"
TITLE = "DEFENDER REAR"
OVERLAY = os.path.join(REFDIR, "rear-trace-overlay.png")
PHOTO = os.path.join(REFDIR, "rear.png")
STEM = "rear"                      # prefix for every output file

ART_W, ART_H = 1316, 1420          # drawing area (overlay canvas is 1316x1560)
PHOTO_H = 1560                     # overlay canvas height
CX = 660                           # body centre line
BEAD_WIDTH_MM = 120

# The trace clips the widest point of the body at the canvas edge, so for the
# recolour pass the whole canvas width is taken as the bead width.
BODY_LEFT, BODY_RIGHT = 0, 1316


def mirror_x(pts, cx=CX):
    return [[2 * cx - x, y] for x, y in pts]


def mirror_box(box, cx=CX):
    x0, y0, x1, y1 = box
    return [2 * cx - x1, y0, 2 * cx - x0, y1]


# ---- the outline the probes follow -------------------------------------
BODY_EDGE = [
    [208, 69], [196, 76], [178, 90], [160, 99], [148, 110], [137, 120],
    [129, 132], [124, 144], [119, 156], [115, 168], [112, 180], [110, 192],
    [108, 204],
]
BODY_SIDE = [
    [108, 204], [101, 300], [90, 420], [78, 540], [73, 600], [72, 640],
    [72, 668], [38, 688], [38, 1076],
]

# ---- wheel-arch flares -------------------------------------------------
# The trace draws the flares as arcs that run off the canvas, so they enclose
# nothing on their own.  These wedges fill the area between each arch, the hip
# line and the body flank, which is what makes the flare part of the silhouette
# instead of a dangling line.
FLARE_WEDGES = [
    [[37, 845], [26, 848], [22, 852], [14, 860], [8, 868], [4, 876], [1, 884],
     [1, 1081], [14, 1097], [37, 1077]],
    [[1280, 843], [1290, 848], [1297, 856], [1304, 864], [1310, 876],
     [1313, 884], [1313, 1081], [1297, 1097], [1280, 1077]],
]

# ---- ink edits requested by the principal ------------------------------
# The rear silhouette is the principal's trace; these are the only changes to
# it, each one asked for explicitly and listed on every sheet the tools produce.

# Removed: strokes in the trace that are not on the bead.
REMOVE_SEEDS = [(700, 81)]                 # roof's inner panel line (x, y)
REMOVE_RECTS = [[298, 1004, 308, 1034],    # door bottom rail, left jamb
                [1004, 1004, 1013, 1034]]  # door bottom rail, right jamb
REMOVE_ANNULI = [dict(c=[700, 713], r_in=112, r_out=137)]   # traced 12 rim holes

# Added: strokes that are not in the trace.
ADDED = [
    dict(type="lines", lines=[                     # wheel-arch closure
        [[36.5, 1077], [36.5, 1100]],
        [[1279.5, 1077], [1279.5, 1100]]]),
    dict(type="lines", lines=[                     # hip closure to the sill
        [[1, 901], [1, 1080]],
        [[1314, 924], [1314, 1080]]]),
    dict(type="circle_ring_array", c=[700, 713],   # 8 larger rim holes
         ring=126, count=8, start_deg=-4, radius=13),
]

EDITS_REMOVED = [
    "roof inner panel line (single outline)",
    "door bottom rail jambs",
    "traced 12 rim holes (replaced by 8 at r=126, radius 13)",
]
EDITS_ADDED = [
    "wheel-arch closure strips: x=36.5 and x=1279.5, y 1077-1100",
    "hip closure verticals: x=1 (y 901-1080), x=1314 (y 924-1080)",
    "8 rim holes, 45 deg spacing, r=126, radius 13",
]
# Prose for the foot of the sheets, grouped the way the principal reads it.
EDITS_NOTES = [
    "Edits to your trace",
    " -  roof inner panel line removed: one outline only",
    " -  door bottom rail removed: etch runs round the whole door",
    " -  12 small rim holes replaced by 8 larger ones, equally spaced",
    " +  2 strips closing the wheel-arch corners",
    " +  2 straight verticals closing the hips down to the sill",
    "",
    "Levels",
    " -  every purple etch is one depth, both faces",
    " -  raised, each its own height: lights, spare tyre,",
    "    steel wheel, waist seam",
    " -  bumper: bottom edge is silhouette, top edge is an etch;",
    "    cross member sits flush with the car",
]


# ---- probe regions (recolour pass) -------------------------------------
# role: silhouette -> the bead profile itself
#       etch       -> engraved line on the face
#       lights     -> raised domes
#       raised_*   -> its own extrusion level
#       delete     -> proposed removal
#       omit       -> agreed omission
# bias: an ink pixel belongs here when its distance to these probes is smaller
#       than to any other part's, so a probe keeps the stroke it sits on even
#       when a neighbouring probe is closer.
PARTS = [
    # -- silhouette ------------------------------------------------------
    dict(id="body", name="Body outline (roof + flanks)", role="silhouette",
         bias=4, probes=[
             dict(type="lines", lines=[
                 [[208, 69], [1112, 69]],
                 BODY_EDGE, mirror_x(BODY_EDGE),
                 BODY_SIDE, mirror_x(BODY_SIDE)])]),
    dict(id="bottom_tyres", name="Tyres at the bottom (L + R)", role="silhouette",
         bias=0, probes=[
             dict(type="rounded_rects", radius=[0, 0, 55, 55], boxes=[
                 [14, 1076, 206, 1378], [1104, 1076, 1298, 1378]]),
             dict(type="lines", lines=[
                 [[120, 1085], [203, 1140]], [[86, 1085], [38, 1085]],
                 mirror_x([[120, 1085], [203, 1140]]),
                 mirror_x([[86, 1085], [38, 1085]])])]),
    dict(id="arch_join", name="Wheel-arch closure (added)", role="silhouette",
         bias=0, draw=True, probes=[ADDED[0]]),
    dict(id="hip_join", name="Hip closure to the sill (added)", role="silhouette",
         bias=0, draw=True, probes=[ADDED[1]]),
    dict(id="bumper_bottom", name="Bumper bottom edge", role="silhouette",
         bias=6, probes=[
             dict(type="lines", lines=[[[62, 1131], [1254, 1131]]])]),

    # -- etched ----------------------------------------------------------
    dict(id="bumper_top", name="Bumper top edge + ends", role="etch",
         bias=2, probes=[
             dict(type="lines", lines=[
                 [[62, 1036], [1254, 1036]], [[62, 1036], [62, 1131]],
                 [[1254, 1036], [1254, 1131]]])]),
    dict(id="roof_gutter", name="Roof gutter / body join", role="etch",
         bias=0, probes=[
             dict(type="lines", lines=[
                 [[94, 208], [318, 208]], [[1002, 208], [1227, 208]]])]),
    dict(id="door_outline", name="Rear door frame", role="etch",
         bias=2, probes=[
             dict(type="rounded_rect", box=[322, 140, 998, 1002],
                  radius=[45, 45, 8, 8])]),
    dict(id="rear_window", name="Rear door window", role="etch",
         bias=0, probes=[
             dict(type="rounded_rect", box=[368, 196, 948, 564], radius=36)]),
    dict(id="alpine_windows", name="Alpine quarter windows (L + R)", role="etch",
         bias=0, probes=[
             dict(type="rounded_rects", radius=30, boxes=[
                 [122, 256, 280, 556], [1036, 256, 1194, 556]])]),
    dict(id="number_plate", name="Number plate", role="etch",
         bias=0, probes=[
             dict(type="rect", box=[70, 780, 298, 906])]),
    dict(id="spare_holes", name="Spare rim holes (8, respaced)", role="etch",
         bias=3, probes=[ADDED[2]]),
    dict(id="spare_nuts", name="Spare wheel nuts (5)", role="etch",
         bias=2, probes=[
             dict(type="circle_ring_array", c=[700, 713], ring=63,
                  count=5, start_deg=54, radius=9)]),
    dict(id="spare_hub", name="Spare hub circle", role="etch",
         bias=2, probes=[
             dict(type="circles", radius=43, centres=[[700, 713]])]),

    # -- lights ----------------------------------------------------------
    dict(id="lights", name="Round lamps (6, L + R)", role="lights",
         bias=4, probes=[
             dict(type="circles", radius=27, centres=[[75, 717], [1244, 715]]),
             dict(type="circles", radius=26, centres=[[70, 961], [1244, 962]]),
             dict(type="circles", radius=37, centres=[[155, 961], [1162, 961]])]),

    # -- raised levels ---------------------------------------------------
    dict(id="spare_tyre", name="Spare tyre (outer edge)", role="raised_tyre",
         bias=4, probes=[
             dict(type="circles", radius=300, centres=[[700, 713]])]),
    dict(id="spare_wheel", name="Steel wheel outer edge", role="raised_wheel",
         bias=4, probes=[
             dict(type="circles", radius=171.5, centres=[[700, 713]])]),
    dict(id="waist_seam", name="Waist capping seams (L + R)", role="raised_seam",
         bias=0, probes=[
             dict(type="lines", lines=[
                 [[66, 606], [322, 606]], [[66, 636], [322, 636]],
                 [[998, 606], [1256, 606]], [[998, 636], [1256, 636]]])]),

    # -- proposed deletions ----------------------------------------------
    dict(id="reflectors", name="Reflector strips (L + R)", role="delete",
         bias=0, probes=[
             dict(type="rects", boxes=[
                 [36, 1005, 106, 1025], mirror_box([36, 1005, 106, 1025])])]),
    dict(id="spare_dish", name="Spare dish circles", role="delete",
         bias=0, probes=[
             dict(type="circles", radius=108, centres=[[700, 713]]),
             dict(type="circles", radius=90, centres=[[700, 713]])]),
    dict(id="spare_rim", name="Spare steel wheel trim", role="delete",
         bias=2, probes=[
             dict(type="circles", radius=155, centres=[[700, 713]]),
             dict(type="circles", radius=139, centres=[[700, 713]])]),

    # -- agreed omissions ------------------------------------------------
    dict(id="door_hinges", name="Door hinges (3)", role="omit",
         bias=0, probes=[
             dict(type="rects", boxes=[
                 [950, 212, 1060, 270], [997, 663, 1050, 757],
                 [965, 905, 1040, 950]])]),
    dict(id="door_handle", name="Door latch / handle", role="omit",
         bias=0, probes=[
             dict(type="rect", box=[370, 630, 406, 714])]),
]

# ---- clean sketch model ------------------------------------------------
# One stroke per feature.  "kind" is the primitive, and any part whose
# geometry is already inside the silhouette polygon uses kind="none" so it can
# still be named on the sheet without being drawn twice.
def build_parts():
    tyre_c = [700, 713]
    parts = [
        # -- silhouette (the polygon comes from the trace) ---------------
        dict(id="outline", name="Body + tyres", level="silhouette",
             kind="polygon", points="SIL"),
        dict(id="bumper_bottom", name="Bumper bottom edge", level="silhouette",
             kind="line", points=[[62, 1131], [1254, 1131]]),
        dict(id="arch_flare", name="Wheel-arch flare (in the profile)", level="silhouette",
             kind="none"),

        # -- etched, one stroke each -------------------------------------
        dict(id="bumper_top", name="Bumper top edge + ends", level="etch",
             kind="polyline", points=[[62, 1132], [62, 1036], [1254, 1036],
                                      [1254, 1132]]),
        dict(id="roof_gutter", name="Roof gutter / body join", level="etch",
             kind="lines", lines=[[[107, 208], [324, 208]],
                                  [[990, 208], [1213, 208]]]),
        dict(id="door", name="Rear door frame", level="etch",
             kind="round_rect", box=[324, 144, 990, 1002],
             radius=[44, 44, 6, 6]),
        dict(id="rear_window", name="Rear door window", level="etch",
             kind="round_rect", box=[368, 196, 947, 555], radius=34),
        dict(id="alpine_L", name="Alpine window, left", level="etch",
             kind="round_rect", box=[127, 262, 275, 550], radius=28),
        dict(id="alpine_R", name="Alpine window, right", level="etch",
             kind="round_rect", box=mirror_box([127, 262, 275, 550]), radius=28),
        dict(id="number_plate", name="Number plate", level="etch",
             kind="round_rect", box=[74, 786, 272, 900], radius=5),
        dict(id="spare_holes", name="Spare rim holes (8)", level="etch",
             kind="ring_array", c=tyre_c, ring=126, count=8, start_deg=-4,
             radius=13),
        dict(id="spare_nuts", name="Spare wheel nuts (5)", level="etch",
             kind="ring_array", c=tyre_c, ring=63, count=5, start_deg=54,
             radius=9),
        dict(id="spare_hub", name="Spare hub circle", level="etch",
             kind="circle", c=tyre_c, r=43),

        # -- raised, each its own height ---------------------------------
        dict(id="lights", name="Round lamps (6, L + R)", level="lights",
             kind="circles", centres=[[75, 717], [1244, 715], [70, 961],
                                      [1244, 962], [155, 961], [1162, 961]],
             radii=[27, 27, 26, 26, 37, 37]),
        dict(id="spare_tyre", name="Spare tyre", level="raised_tyre",
             kind="circle", c=tyre_c, r=300),
        dict(id="spare_wheel", name="Steel wheel edge", level="raised_wheel",
             kind="circle", c=tyre_c, r=171.5),
        dict(id="waist_seam", name="Waist capping seams (L + R)", level="raised_seam",
             kind="lines", lines=[[[74, 606], [324, 606]], [[74, 636], [324, 636]],
                                  [[990, 606], [1246, 606]],
                                  [[990, 636], [1246, 636]]]),
    ]
    return parts
