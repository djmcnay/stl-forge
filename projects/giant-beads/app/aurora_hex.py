"""Aurora Hex: the default Gradio theme for David's tools.

Synced from araminta-skills/skills/gradio-design/assets/aurora_hex.py.
Midnight royal purple ground, one teal action colour, violet selection,
and a dawn lavender/mint wash only in light mode. No orange, no brown.

Copy this file into a project (usually ``app/aurora_hex.py``) and either
use ``AuroraHexTheme`` directly or subclass it to append app-specific
CSS. In Gradio 6, pass the theme at launch:

    demo.launch(theme=AuroraHexTheme())
"""
from __future__ import annotations

import gradio as gr
from gradio.themes.utils import colors, sizes

TEAL = colors.Color(
    c50="#E8FBF7",
    c100="#C7F4EB",
    c200="#96E8DC",
    c300="#63D7C8",
    c400="#3FC4B4",
    c500="#2AAE9E",
    c600="#1B7F74",
    c700="#17766C",
    c800="#13544D",
    c900="#0D3B36",
    c950="#082320",
    name="teal",
)
PLUM = colors.Color(
    c50="#F7F1FC",
    c100="#EDE1F7",
    c200="#DBC6EE",
    c300="#C3A5E1",
    c400="#A87FD0",
    c500="#8D5EBA",
    c600="#74499C",
    c700="#5A367A",
    c800="#402556",
    c900="#291637",
    c950="#160B1E",
    name="plum",
)

BASE_CSS = """
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
.meta, .family-summary { font-size: 13px !important;
    color: var(--body-text-color-subdued); text-wrap: pretty; }
.meta code, .family-summary code { font-family: var(--font-mono);
    font-size: 12px; }
.override-fields { border-left: 2px solid var(--border-color-primary);
    padding-left: 12px; margin-top: 4px; }
"""


class AuroraHexTheme(gr.themes.Base):
    """Midnight purple, teal action, violet selection."""

    def __init__(self):
        super().__init__(
            primary_hue=TEAL,
            secondary_hue=PLUM,
            neutral_hue=PLUM,
            spacing_size=sizes.spacing_md,
            radius_size=sizes.radius_md,
            text_size=sizes.text_md,
            font=(
                "Avenir Next",
                "Avenir",
                "Segoe UI",
                "system-ui",
                "sans-serif",
            ),
            font_mono=(
                "SFMono-Regular",
                "Menlo",
                "Consolas",
                "monospace",
            ),
        )
        self.name = "aurora_hex"
        self.custom_css = BASE_CSS
        super().set(
            body_background_fill=(
                "linear-gradient(135deg, #F3EAFC 0%, #E5F6F1 100%)"
            ),
            body_background_fill_dark="#0D0913",
            body_text_color="#1B1226",
            body_text_color_dark="#F0EAF7",
            body_text_color_subdued="#6B5C78",
            body_text_color_subdued_dark="#A99BB8",
            body_text_size="15px",
            background_fill_primary="#FBF8FE",
            background_fill_primary_dark="#171020",
            background_fill_secondary="#EFE6F7",
            background_fill_secondary_dark="#21152E",
            border_color_primary="#D6C6E4",
            border_color_primary_dark="#352347",
            border_color_accent="#1B7F74",
            border_color_accent_dark="#45C7B3",
            block_background_fill="#FBF8FE",
            block_background_fill_dark="#171020",
            block_border_color="#D6C6E4",
            block_border_color_dark="#352347",
            block_border_width="1px",
            block_radius="6px",
            block_shadow="none",
            block_shadow_dark="none",
            block_label_text_color="#6B5C78",
            block_label_text_color_dark="#A99BB8",
            block_label_text_size="12px",
            block_title_text_color="#1B1226",
            block_title_text_color_dark="#F0EAF7",
            block_title_text_size="14px",
            block_title_text_weight="500",
            panel_background_fill="#FBF8FE",
            panel_background_fill_dark="#171020",
            panel_border_color="#D6C6E4",
            panel_border_color_dark="#352347",
            input_background_fill="#EFE6F7",
            input_background_fill_dark="#21152E",
            input_border_color="#D6C6E4",
            input_border_color_dark="#352347",
            input_border_color_focus="#1B7F74",
            input_border_color_focus_dark="#45C7B3",
            input_border_width="1px",
            input_radius="6px",
            input_placeholder_color="#8A7A98",
            input_placeholder_color_dark="#82738F",
            input_shadow="none",
            input_shadow_dark="none",
            input_shadow_focus="none",
            input_shadow_focus_dark="none",
            slider_color="#1B7F74",
            slider_color_dark="#45C7B3",
            # Teal advances the task; violet confirms a selection.
            checkbox_background_color_selected="#8D5EBA",
            checkbox_background_color_selected_dark="#B27BE0",
            checkbox_border_color_selected="#8D5EBA",
            checkbox_border_color_selected_dark="#C3A5E1",
            checkbox_border_color_focus="#1B7F74",
            checkbox_border_color_focus_dark="#45C7B3",
            checkbox_label_background_fill_selected="#EDE1F7",
            checkbox_label_background_fill_selected_dark="#2A1738",
            checkbox_label_text_color_selected="#1B1226",
            checkbox_label_text_color_selected_dark="#F0EAF7",
            button_primary_background_fill="#1B7F74",
            button_primary_background_fill_dark="#45C7B3",
            button_primary_background_fill_hover="#17766C",
            button_primary_background_fill_hover_dark="#63D7C8",
            button_primary_border_color="#1B7F74",
            button_primary_border_color_dark="#45C7B3",
            button_primary_text_color="#F4FFFC",
            button_primary_text_color_dark="#061411",
            button_primary_text_color_hover="#F4FFFC",
            button_primary_text_color_hover_dark="#061411",
            button_primary_shadow="none",
            button_primary_shadow_hover="none",
            button_primary_shadow_active="none",
            button_primary_shadow_dark="none",
            button_primary_shadow_hover_dark="none",
            button_primary_shadow_active_dark="none",
            button_secondary_background_fill="#EFE6F7",
            button_secondary_background_fill_dark="#21152E",
            button_secondary_background_fill_hover="#E4D6F1",
            button_secondary_background_fill_hover_dark="#2B1B3B",
            button_secondary_border_color="#D6C6E4",
            button_secondary_border_color_dark="#352347",
            button_secondary_text_color="#1B1226",
            button_secondary_text_color_dark="#F0EAF7",
            button_secondary_text_color_hover="#1B1226",
            button_secondary_text_color_hover_dark="#F0EAF7",
            button_secondary_shadow="none",
            button_secondary_shadow_hover="none",
            button_secondary_shadow_active="none",
            button_secondary_shadow_dark="none",
            button_secondary_shadow_hover_dark="none",
            button_secondary_shadow_active_dark="none",
            button_cancel_background_fill="#B34A67",
            button_cancel_background_fill_dark="#C15B79",
            button_cancel_text_color="#FFF6FA",
            button_cancel_text_color_dark="#FFF6FA",
            button_transform_hover="none",
            button_transform_active="none",
            button_transition="none",
            shadow_drop="none",
            shadow_drop_lg="none",
            shadow_inset="none",
            section_header_text_size="18px",
            section_header_text_weight="500",
        )
