"""Load a view's data module and hand its contents to an engine.

A view is one elevation - `rear` today, `side` and `front` next.  Every number
specific to that elevation lives in `views/<name>.py`; the engines only know how
to use them.  Adding a view is a new module plus a run with `--view`.

`REQUIRED` is the contract.  It is checked on load, so a half-finished view
fails with a readable message instead of a NameError deep inside a render.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

REQUIRED = (
    # identity + frame
    "NAME", "TITLE", "OVERLAY", "PHOTO", "STEM",
    "ART_W", "ART_H", "PHOTO_H", "CX", "BEAD_WIDTH_MM", "BODY_LEFT", "BODY_RIGHT",
    # the outline the probes follow
    "BODY_EDGE", "FLARE_WEDGES",
    # ink edits the principal asked for
    "REMOVE_SEEDS", "REMOVE_RECTS", "REMOVE_ANNULI", "ADDED",
    "EDITS_REMOVED", "EDITS_ADDED", "EDITS_NOTES",
    # probe regions + the clean sketch model
    "PARTS", "build_parts",
)


def available():
    d = os.path.join(HERE, "views")
    return sorted(f[:-3] for f in os.listdir(d)
                  if f.endswith(".py") and not f.startswith("_"))


def load(name):
    if name not in available():
        raise SystemExit("no view '%s' (have: %s)" % (name, ", ".join(available())))
    mod = importlib.import_module("views." + name)
    missing = [k for k in REQUIRED if not hasattr(mod, k)]
    if missing:
        raise SystemExit("view '%s' is missing: %s" % (name, ", ".join(missing)))
    if mod.NAME != name:
        raise SystemExit("view '%s' declares NAME = '%s'" % (name, mod.NAME))
    return mod


def bind(namespace, view):
    """Publish a view's data as module-level names in an engine."""
    for key in REQUIRED:
        namespace[key] = getattr(view, key)


def out_paths(view):
    """Where a view's artifacts live, derived from the trace it came from."""
    refdir = os.path.dirname(view.OVERLAY)
    stem = view.STEM
    return dict(
        parts_png=os.path.join(refdir, "%s-parts-by-colour.png" % stem),
        parts_json=os.path.join(refdir, "%s-parts.json" % stem),
        sketch_png=os.path.join(refdir, "%s-bead-sketch.png" % stem),
        sketch_json=os.path.join(refdir, "%s-bead-sketch.json" % stem),
        overlay_png=os.path.join(refdir, "%s-bead-sketch-overlay.png" % stem),
    )
