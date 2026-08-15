"""SVG figure loading: vector diagrams scaled to the text block."""

from __future__ import annotations

import os

from reportlab.graphics.shapes import Drawing
from svglib.fonts import register_font
from svglib.svglib import svg2rlg

WIDTH_KEYWORDS = {
    "full": 1.0,
    "wide": 0.94,
    "two-thirds": 0.68,
    "half": 0.5,
}


def register_svg_fonts(fonts) -> None:
    """Teach svglib the aliases the diagrams use.

    The SVG sources set ``font-family="WPSans"`` so diagram type matches body
    type. Without this mapping svglib silently falls back to Helvetica.
    """
    sans = fonts.sans_family
    mono = fonts.mono_family
    sans_bold = f"{sans}-Bold" if sans != "Helvetica" else "Helvetica-Bold"
    sans_italic = f"{sans}-Italic" if sans != "Helvetica" else "Helvetica-Oblique"
    sans_bold_italic = f"{sans}-BoldItalic" if sans != "Helvetica" else "Helvetica-BoldOblique"
    mono_bold = f"{mono}-Bold" if mono != "Courier" else "Courier-Bold"

    mappings = [
        ("WPSans", "normal", "normal", sans),
        ("WPSans", "bold", "normal", sans_bold),
        ("WPSans", "normal", "italic", sans_italic),
        ("WPSans", "bold", "italic", sans_bold_italic),
        ("WPMono", "normal", "normal", mono),
        ("WPMono", "bold", "normal", mono_bold),
    ]
    for family, weight, style, target in mappings:
        try:
            register_font(family, weight=weight, style=style, rlgFontName=target)
        except Exception:
            pass


def resolve_width(spec: str | None, content_width: float) -> float:
    if not spec:
        return content_width
    spec = spec.strip().lower()
    if spec in WIDTH_KEYWORDS:
        return content_width * WIDTH_KEYWORDS[spec]
    if spec.endswith("%"):
        try:
            return content_width * float(spec[:-1]) / 100.0
        except ValueError:
            return content_width
    try:
        value = float(spec)
    except ValueError:
        return content_width
    return content_width * value if value <= 1.0 else min(value, content_width)


def load_svg(path: str, target_width: float, max_height: float | None = None) -> Drawing:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"figure not found: {path}")
    drawing = svg2rlg(path)
    if drawing is None:
        raise ValueError(f"could not parse SVG: {path}")

    native_w = float(drawing.width or 0) or target_width
    native_h = float(drawing.height or 0) or target_width

    scale = target_width / native_w
    if max_height is not None and native_h * scale > max_height:
        scale = max_height / native_h

    drawing.scale(scale, scale)
    drawing.width = native_w * scale
    drawing.height = native_h * scale
    drawing.hAlign = "CENTER"
    return drawing
