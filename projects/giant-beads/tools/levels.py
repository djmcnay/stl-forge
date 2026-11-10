"""The level vocabulary shared by every view.

Colours mean levels, not identity: two parts that will be cut at the same height
share a colour, which is what makes the sheets readable at a glance.  Keeping the
table here means a new view cannot invent its own palette, and both engines
describe a level with the same words.
"""

# key, colour, legend heading, dotted stroke
ROLES = [
    ("silhouette", "#1B3B6F", "SILHOUETTE  -  the bead profile", False),
    ("etch", "#6C3483", "ETCHED  -  one depth, both faces", False),
    ("lights", "#D64541", "LIGHTS  -  raised domes", False),
    ("raised_tyre", "#0E7A55", "RAISED  -  spare tyre", False),
    ("raised_wheel", "#148F77", "RAISED  -  steel wheel", False),
    ("raised_seam", "#7DCE7A", "RAISED  -  waist seam", False),
    ("delete", "#98A0A5", "PROPOSED DELETE  -  your call", True),
    ("omit", "#BFC5C9", "OMIT  -  agreed, wasted at bead size", True),
]

ROLE_ORDER = [r[0] for r in ROLES]
ROLE_COLOUR = {r[0]: r[1] for r in ROLES}
ROLE_HEAD = {r[0]: r[2] for r in ROLES}
ROLE_DOTTED = {r[0]: r[3] for r in ROLES}

# Stroke weights for the clean sketch, which draws one line per feature.
STROKE = {"silhouette": 4.0, "etch": 3.0, "lights": 3.0,
          "raised_tyre": 3.0, "raised_wheel": 3.0, "raised_seam": 3.0}

# The sketch sheet talks about what will be *built* rather than about parts, so
# its headings differ slightly from the part map's.  Same colours, same order:
# only the six levels that survive on the bead are listed.
SKETCH_HEAD = {
    "silhouette": "SILHOUETTE  -  the bead profile",
    "etch": "ETCHED  -  one depth, both faces",
    "lights": "RAISED  -  lights (domes)",
    "raised_tyre": "RAISED  -  spare tyre",
    "raised_wheel": "RAISED  -  steel wheel",
    "raised_seam": "RAISED  -  waist seam",
}
SKETCH_ORDER = [k for k in ROLE_ORDER if k in SKETCH_HEAD]
LEVELS = [(k, ROLE_COLOUR[k], SKETCH_HEAD[k]) for k in SKETCH_ORDER]
LEVEL_COLOUR = {k: ROLE_COLOUR[k] for k in SKETCH_ORDER}
LEVEL_HEAD = dict(SKETCH_HEAD)
LEVEL_ORDER = list(SKETCH_ORDER)


def demo():
    """Self-check: every level a view may use is described here."""
    for key in ("silhouette", "etch", "lights", "raised_tyre", "raised_wheel",
                "raised_seam", "delete", "omit"):
        assert key in ROLE_COLOUR, key
        assert ROLE_HEAD[key] and ROLE_DOTTED[key] in (True, False)
    return "%d levels: %s" % (len(ROLES), ", ".join(ROLE_ORDER))


if __name__ == "__main__":
    print(demo())
