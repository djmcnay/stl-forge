"""Giant-beads theme: Aurora Hex plus the app's small layout CSS.

Aurora Hex is the house default for Gradio apps. The shared class lives
in ``aurora_hex.py`` so it can be copied to other projects; this module
only appends the bead-select and viewer rules.
"""
from __future__ import annotations

try:
    from .aurora_hex import AuroraHexTheme
except ImportError:
    from aurora_hex import AuroraHexTheme

APP_CSS = """
.bead-select { border: 1px solid var(--border-color-primary) !important;
    border-radius: 6px !important; }
.bead-select:focus-within { border-color: var(--border-color-accent) !important; }
.viewer-shell { border: 1px solid var(--border-color-primary);
    border-radius: 6px; overflow: hidden; }
.viewer-shell .block { border: 0 !important; }
.viewer-shell canvas { filter: saturate(0.9) brightness(0.98); }
.viewer-shell .icon-button-wrapper.top-panel { display: none !important; }
"""


class BeadTheme(AuroraHexTheme):
    def __init__(self):
        super().__init__()
        self.name = "aurora_hex_beads"
        self.custom_css = self.custom_css + APP_CSS


def theme() -> BeadTheme:
    return BeadTheme()
