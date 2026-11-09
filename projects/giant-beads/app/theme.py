"""The bead-bench theme: warm paper, deep green-black, one brass accent.

Native Gradio theme tokens only.  The small custom_css block is the
house tier-2 allowance: spacing, the bead picker's card shape, and the
viewer frame.  No injected HTML or JavaScript.
"""
from __future__ import annotations

import gradio as gr
from gradio.themes.utils import colors, sizes

# Brass is the one accent.  The shades give Gradio a complete ramp so
# focus rings, sliders and selected states stay in the same family.
BRASS = colors.Color(
    c50="#FBF4E6",
    c100="#F4E7CE",
    c200="#E8D0A6",
    c300="#D9B77B",
    c400="#C8A05A",
    c500="#B08D57",
    c600="#987542",
    c700="#7C5D32",
    c800="#5E4524",
    c900="#3F2E17",
    c950="#241A0C",
    name="brass",
)

LIGHT = {
    "ground": "#F4F0E7",
    "surface": "#FBF8F1",
    "surface_2": "#EDE7DB",
    "line": "#D7CFC1",
    "text": "#20261F",
    "muted": "#687066",
    "accent": "#8B6A36",
    "accent_text": "#FFF9EB",
    "placeholder": "#7A8178",
}
DARK = {
    "ground": "#0F1512",
    "surface": "#161D19",
    "surface_2": "#1E2723",
    "line": "#2A342E",
    "text": "#E8E4DA",
    "muted": "#9AA39C",
    "accent": "#C39C63",
    "accent_text": "#12160F",
    "placeholder": "#8D958D",
}

CSS = """
.gradio-container { max-width: 1480px !important; margin: 0 auto !important;
    padding: 24px !important; }
.workbench-header h1 { font-size: 30px !important; font-weight: 600 !important;
    letter-spacing: -0.02em; margin: 0 0 4px 0 !important; }
.workbench-header p { color: var(--body-text-color-subdued);
    margin: 0 0 4px 0 !important; max-width: 72ch; text-wrap: pretty; }
.bench-card { background: var(--background-fill-primary) !important;
    padding: 8px !important;
    border: 1px solid var(--border-color-primary) !important; }
.bench-card > .gr-group { background: transparent !important; }
.bench-card > .gr-group > .styler { background: transparent !important; }
.section-title h2 { font-size: 18px !important; font-weight: 500 !important;
    letter-spacing: -0.01em; margin: 0 0 2px 0 !important; }
.bead-picker { gap: 6px !important; }
.bead-picker label { border: 1px solid var(--border-color-primary);
    border-radius: 6px !important; padding: 10px 12px !important;
    background: var(--background-fill-primary); }
.bead-picker label:has(input:checked) {
    border-color: var(--checkbox-border-color-selected);
    background: var(--background-fill-secondary); }
.bead-picker input { accent-color: var(--checkbox-background-color-selected); }
.viewer-shell { border: 1px solid var(--border-color-primary);
    border-radius: 6px; overflow: hidden; }
.viewer-shell .block { border: 0 !important; }
.viewer-shell canvas { filter: grayscale(0.82) sepia(0.18)
    saturate(0.85) brightness(0.92); }
.viewer-shell .icon-button-wrapper.top-panel { display: none !important; }
.meta, .family-summary { font-size: 13px !important;
    color: var(--body-text-color-subdued); text-wrap: pretty; }
.meta code, .family-summary code { font-family: var(--font-mono);
    font-size: 12px; }
.override-fields { border-left: 2px solid var(--border-color-primary);
    padding-left: 12px; margin-top: 4px; }
"""


class BeadTheme(gr.themes.Base):
    """Deliberate, quiet, a little old-fashioned."""

    def __init__(self):
        super().__init__(
            primary_hue=BRASS,
            secondary_hue=colors.stone,
            neutral_hue=colors.stone,
            spacing_size=sizes.spacing_md,
            radius_size=sizes.radius_md,
            text_size=sizes.text_md,
            font=(
                "ui-sans-serif",
                "system-ui",
                "-apple-system",
                "BlinkMacSystemFont",
                "Segoe UI",
                "sans-serif",
            ),
            font_mono=(
                "SFMono-Regular",
                "Menlo",
                "Consolas",
                "monospace",
            ),
        )
        self.name = "bead_bench"
        self.custom_css = CSS
        super().set(
            body_background_fill=LIGHT["ground"],
            body_background_fill_dark=DARK["ground"],
            body_text_color=LIGHT["text"],
            body_text_color_dark=DARK["text"],
            body_text_color_subdued=LIGHT["muted"],
            body_text_color_subdued_dark=DARK["muted"],
            body_text_size="15px",
            background_fill_primary=LIGHT["surface"],
            background_fill_primary_dark=DARK["surface"],
            background_fill_secondary=LIGHT["surface_2"],
            background_fill_secondary_dark=DARK["surface_2"],
            border_color_primary=LIGHT["line"],
            border_color_primary_dark=DARK["line"],
            border_color_accent=LIGHT["accent"],
            border_color_accent_dark=DARK["accent"],
            block_background_fill=LIGHT["surface"],
            block_background_fill_dark=DARK["surface"],
            block_border_color=LIGHT["line"],
            block_border_color_dark=DARK["line"],
            block_border_width="1px",
            block_radius="6px",
            block_shadow="none",
            block_shadow_dark="none",
            block_label_text_color=LIGHT["muted"],
            block_label_text_color_dark=DARK["muted"],
            block_label_text_size="12px",
            block_title_text_color=LIGHT["text"],
            block_title_text_color_dark=DARK["text"],
            block_title_text_size="14px",
            block_title_text_weight="500",
            panel_background_fill=LIGHT["surface"],
            panel_background_fill_dark=DARK["surface"],
            panel_border_color=LIGHT["line"],
            panel_border_color_dark=DARK["line"],
            input_background_fill=LIGHT["surface_2"],
            input_background_fill_dark=DARK["surface_2"],
            input_border_color=LIGHT["line"],
            input_border_color_dark=DARK["line"],
            input_border_color_focus=LIGHT["accent"],
            input_border_color_focus_dark=DARK["accent"],
            input_border_width="1px",
            input_radius="6px",
            input_placeholder_color=LIGHT["placeholder"],
            input_placeholder_color_dark=DARK["placeholder"],
            input_shadow="none",
            input_shadow_dark="none",
            input_shadow_focus="none",
            input_shadow_focus_dark="none",
            slider_color=LIGHT["accent"],
            slider_color_dark=DARK["accent"],
            checkbox_background_color_selected=LIGHT["accent"],
            checkbox_background_color_selected_dark=DARK["accent"],
            checkbox_border_color_selected=LIGHT["accent"],
            checkbox_border_color_selected_dark=DARK["accent"],
            checkbox_border_color_focus=LIGHT["accent"],
            checkbox_border_color_focus_dark=DARK["accent"],
            checkbox_label_background_fill_selected=LIGHT["surface_2"],
            checkbox_label_background_fill_selected_dark=DARK["surface_2"],
            button_primary_background_fill=LIGHT["accent"],
            button_primary_background_fill_dark=DARK["accent"],
            button_primary_background_fill_hover="#9C7A43",
            button_primary_background_fill_hover_dark="#D0AC77",
            button_primary_border_color=LIGHT["accent"],
            button_primary_border_color_dark=DARK["accent"],
            button_primary_text_color=LIGHT["accent_text"],
            button_primary_text_color_dark=DARK["accent_text"],
            button_primary_text_color_hover=LIGHT["accent_text"],
            button_primary_text_color_hover_dark=DARK["accent_text"],
            button_primary_shadow="none",
            button_primary_shadow_hover="none",
            button_primary_shadow_active="none",
            button_primary_shadow_dark="none",
            button_primary_shadow_hover_dark="none",
            button_primary_shadow_active_dark="none",
            button_secondary_background_fill=LIGHT["surface_2"],
            button_secondary_background_fill_dark=DARK["surface_2"],
            button_secondary_background_fill_hover=LIGHT["line"],
            button_secondary_background_fill_hover_dark="#2A342E",
            button_secondary_border_color=LIGHT["line"],
            button_secondary_border_color_dark=DARK["line"],
            button_secondary_text_color=LIGHT["text"],
            button_secondary_text_color_dark=DARK["text"],
            button_secondary_text_color_hover=LIGHT["text"],
            button_secondary_text_color_hover_dark=DARK["text"],
            button_secondary_shadow="none",
            button_secondary_shadow_hover="none",
            button_secondary_shadow_active="none",
            button_secondary_shadow_dark="none",
            button_secondary_shadow_hover_dark="none",
            button_secondary_shadow_active_dark="none",
            button_cancel_background_fill="#B4553F",
            button_cancel_background_fill_dark="#B4553F",
            button_cancel_text_color="#FFF9EB",
            button_cancel_text_color_dark="#FFF9EB",
            button_transform_hover="none",
            button_transform_active="none",
            button_transition="none",
            shadow_drop="none",
            shadow_drop_lg="none",
            shadow_inset="none",
            section_header_text_size="18px",
            section_header_text_weight="500",
        )


def theme() -> BeadTheme:
    return BeadTheme()
