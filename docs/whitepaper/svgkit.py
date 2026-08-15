"""Minimal SVG drawing toolkit for the white paper diagrams.

Diagrams are generated rather than hand-written so that spacing, colour, type
and arrowheads stay identical across all figures. Only SVG constructs that
svglib renders reliably are used: rect, line, polyline, polygon, path, circle,
text. In particular arrowheads are explicit polygons because svglib does not
implement ``marker-end``, and every attribute is a presentation attribute
because CSS class support is partial.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Palette mirrors src/theme.py so figures and body text agree.
C = {
    "ink": "#16202B",
    "body": "#26333F",
    "muted": "#5D6C7B",
    "faint": "#8494A3",
    "accent": "#1C5A9E",
    "accent_dark": "#123F72",
    "accent_soft": "#E8F0F8",
    "accent_mid": "#C7DBEE",
    "teal": "#0F7267",
    "teal_soft": "#E4F1EF",
    "teal_mid": "#BFDFDA",
    "warn": "#A8551A",
    "warn_soft": "#FBF0E4",
    "warn_mid": "#F0D6B6",
    "danger": "#9C2B2B",
    "danger_soft": "#F9EAEA",
    "danger_mid": "#EFC9C9",
    "violet": "#5B4B9E",
    "violet_soft": "#EDEAF7",
    "rule": "#D2DAE2",
    "rule_soft": "#E7ECF1",
    "wash": "#F7F9FB",
    "wash2": "#EFF3F7",
    "paper": "#FFFFFF",
}

FONT = "WPSans"
MONO = "WPMono"


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@dataclass
class Canvas:
    width: float
    height: float = 0.0
    parts: list[str] = field(default_factory=list)
    max_y: float = 0.0
    max_x: float = 0.0
    overflow: list[str] = field(default_factory=list)

    # -- extent tracking ---------------------------------------------------

    def _extend(self, x: float, y: float, what: str = "") -> None:
        """Record the furthest point drawn so the canvas can size itself."""
        if y > self.max_y:
            self.max_y = y
        if x > self.max_x:
            self.max_x = x
        if x > self.width - 2 and what:
            self.overflow.append(f"{what} reaches x={x:.0f} of {self.width:g}")

    def finish(self, pad: float = 10.0, frame: bool = True, min_height: float = 0.0):
        """Size the canvas to its content and draw the outer hairline last.

        Declaring heights by hand is the main source of clipped figures, so the
        height is derived from what was actually drawn.
        """
        self.height = max(self.max_y + pad, min_height)
        if frame:
            # The frame spans the full width by design, so it must not be
            # reported as a horizontal overrun.
            recorded = list(self.overflow)
            self.rect(0.5, 0.5, self.width - 1, self.height - 1, fill="none",
                      stroke=C["rule_soft"], sw=1.0, rx=3)
            self.overflow = recorded
        return self

    # -- raw ---------------------------------------------------------------

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def render(self) -> str:
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width:g}" '
            f'height="{self.height:g}" viewBox="0 0 {self.width:g} {self.height:g}">'
        )
        body = "\n  ".join(self.parts)
        return f"{head}\n  {body}\n</svg>\n"

    # -- primitives --------------------------------------------------------

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1.0, rx=0, dash=None,
             opacity=None):
        attrs = [f'x="{x:g}"', f'y="{y:g}"', f'width="{w:g}"', f'height="{h:g}"',
                 f'fill="{fill}"']
        if rx:
            attrs.append(f'rx="{rx:g}"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{sw:g}"')
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity:g}"')
        self.add(f'<rect {" ".join(attrs)}/>')
        self._extend(x + w, y + h, "rect")

    def line(self, x1, y1, x2, y2, stroke=None, sw=1.0, dash=None):
        stroke = stroke or C["rule"]
        attrs = [f'x1="{x1:g}"', f'y1="{y1:g}"', f'x2="{x2:g}"', f'y2="{y2:g}"',
                 f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        self.add(f'<line {" ".join(attrs)}/>')
        self._extend(max(x1, x2), max(y1, y2))

    def polyline(self, points, stroke=None, sw=1.0, dash=None, fill="none"):
        stroke = stroke or C["rule"]
        pts = " ".join(f"{x:g},{y:g}" for x, y in points)
        attrs = [f'points="{pts}"', f'fill="{fill}"', f'stroke="{stroke}"',
                 f'stroke-width="{sw:g}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        self.add(f'<polyline {" ".join(attrs)}/>')
        self._extend(max(p[0] for p in points), max(p[1] for p in points))

    def polygon(self, points, fill="none", stroke=None, sw=1.0):
        pts = " ".join(f"{x:g},{y:g}" for x, y in points)
        attrs = [f'points="{pts}"', f'fill="{fill}"']
        if stroke:
            attrs += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        self.add(f'<polygon {" ".join(attrs)}/>')
        self._extend(max(p[0] for p in points), max(p[1] for p in points))

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1.0):
        attrs = [f'cx="{cx:g}"', f'cy="{cy:g}"', f'r="{r:g}"', f'fill="{fill}"']
        if stroke:
            attrs += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        self.add(f'<circle {" ".join(attrs)}/>')
        self._extend(cx + r, cy + r)

    def text(self, x, y, content, size=9, fill=None, anchor="start", weight="normal",
             font=FONT, italic=False, opacity=None):
        fill = fill or C["ink"]
        # Approximate advance width; enough to catch gross horizontal overruns.
        span = len(str(content)) * size * (0.56 if weight == "bold" else 0.52)
        right = x + span if anchor == "start" else (x + span / 2 if anchor == "middle" else x)
        self._extend(right, y + size * 0.26, f'text "{str(content)[:34]}"')
        attrs = [f'x="{x:g}"', f'y="{y:g}"', f'font-family="{font}"',
                 f'font-size="{size:g}"', f'fill="{fill}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight != "normal":
            attrs.append(f'font-weight="{weight}"')
        if italic:
            attrs.append('font-style="italic"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity:g}"')
        self.add(f'<text {" ".join(attrs)}>{esc(content)}</text>')

    # -- composites --------------------------------------------------------

    def arrow(self, x1, y1, x2, y2, stroke=None, sw=1.1, head=6.0, dash=None,
              both=False):
        """Straight connector with an explicit triangular head."""
        stroke = stroke or C["accent"]
        angle = math.atan2(y2 - y1, x2 - x1)
        back = head * 0.92
        ex = x2 - back * math.cos(angle)
        ey = y2 - back * math.sin(angle)
        sx, sy = x1, y1
        if both:
            sx = x1 + back * math.cos(angle)
            sy = y1 + back * math.sin(angle)
        self.line(sx, sy, ex, ey, stroke=stroke, sw=sw, dash=dash)
        self._head(x2, y2, angle, stroke, head)
        if both:
            self._head(x1, y1, angle + math.pi, stroke, head)

    def _head(self, x, y, angle, fill, head):
        half = head * 0.46
        bx = x - head * math.cos(angle)
        by = y - head * math.sin(angle)
        nx = -math.sin(angle)
        ny = math.cos(angle)
        self.polygon([
            (x, y),
            (bx + nx * half, by + ny * half),
            (bx - nx * half, by - ny * half),
        ], fill=fill)

    def elbow(self, x1, y1, x2, y2, stroke=None, sw=1.1, dash=None, first="v",
              head=6.0):
        """Right-angled connector; ``first`` picks the leading axis."""
        stroke = stroke or C["accent"]
        if first == "v":
            mid = [(x1, y1), (x1, y2), (x2, y2)]
            angle = 0.0 if x2 >= x1 else math.pi
        else:
            mid = [(x1, y1), (x2, y1), (x2, y2)]
            angle = math.pi / 2 if y2 >= y1 else -math.pi / 2
        back = head * 0.92
        end = list(mid[-1])
        end[0] -= back * math.cos(angle)
        end[1] -= back * math.sin(angle)
        self.polyline(mid[:-1] + [tuple(end)], stroke=stroke, sw=sw, dash=dash)
        self._head(x2, y2, angle, stroke, head)

    def box(self, x, y, w, h, title=None, subtitle=None, lines=None, fill=None,
            stroke=None, accent=None, title_size=9.2, sub_size=7.4, rx=3.5,
            title_weight="bold", pad=8.0, sw=1.1, align="center"):
        """Rounded panel with an optional left accent bar and stacked labels."""
        fill = fill or C["paper"]
        stroke = stroke or C["rule"]
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx)
        if accent:
            self.rect(x, y + 1.0, 2.8, h - 2.0, fill=accent, rx=1.4)

        if align == "center":
            tx = x + w / 2
            anchor = "middle"
        else:
            tx = x + pad
            anchor = "start"

        rows = []
        if title:
            rows.append((title, title_size, C["ink"], title_weight, FONT))
        if subtitle:
            rows.append((subtitle, sub_size, C["muted"], "normal", FONT))
        for line in (lines or []):
            rows.append((line, sub_size, C["muted"], "normal", FONT))

        if not rows:
            return
        gaps = [r[1] * 1.32 for r in rows]
        total = sum(gaps)
        cursor = y + h / 2 - total / 2 + rows[0][1] * 0.94
        for (label, size, colour, weight, font), gap in zip(rows, gaps):
            self.text(tx, cursor, label, size=size, fill=colour, anchor=anchor,
                      weight=weight, font=font)
            cursor += gap

    def band(self, x, y, w, h, label, fill=None, stroke=None, label_colour=None,
             label_size=7.6, dash=None, rx=4.0):
        """Labelled background region used to group boxes into planes."""
        fill = fill or C["wash"]
        stroke = stroke or C["rule_soft"]
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.0, rx=rx, dash=dash)
        if label:
            self.text(x + 8, y + 12.4, label, size=label_size,
                      fill=label_colour or C["faint"], weight="bold")

    def chip(self, x, y, label, size=7.0, fill=None, text_colour=None, pad=5.0,
             h=13.0, stroke=None):
        """Small pill; width is estimated from the label length."""
        w = max(20.0, len(label) * size * 0.56 + pad * 2)
        self.rect(x, y, w, h, fill=fill or C["accent_soft"], rx=h / 2,
                  stroke=stroke, sw=0.8 if stroke else 1.0)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size,
                  fill=text_colour or C["accent_dark"], anchor="middle")
        return w

    def legend(self, x, y, entries, size=7.2, gap=13.0, swatch=8.0, columns=1,
               col_width=150.0):
        """entries: list of (colour, label) or (colour, label, 'line')."""
        for index, entry in enumerate(entries):
            colour, label = entry[0], entry[1]
            shape = entry[2] if len(entry) > 2 else "box"
            col = index // math.ceil(len(entries) / columns) if columns > 1 else 0
            row = index % math.ceil(len(entries) / columns) if columns > 1 else index
            ex = x + col * col_width
            ey = y + row * gap
            if shape == "line":
                self.line(ex, ey + swatch / 2, ex + swatch + 3, ey + swatch / 2,
                          stroke=colour, sw=1.6)
            else:
                self.rect(ex, ey, swatch, swatch, fill=colour, rx=1.6,
                          stroke=C["rule"], sw=0.6)
            self.text(ex + swatch + 6, ey + swatch * 0.86, label, size=size,
                      fill=C["muted"])

    def hbar(self, x, y, w, h, fill, label=None, label_colour=None, label_size=6.8,
             stroke=None):
        self.rect(x, y, max(w, 0.6), h, fill=fill, rx=1.6, stroke=stroke,
                  sw=0.7 if stroke else 1.0)
        if label and w > 26:
            self.text(x + w / 2, y + h / 2 + label_size * 0.36, label,
                      size=label_size, fill=label_colour or C["paper"],
                      anchor="middle")
        elif label:
            self.text(x + w + 4, y + h / 2 + label_size * 0.36, label,
                      size=label_size, fill=label_colour or C["muted"])

    def axis_x(self, x, y, w, ticks, label=None, size=6.8):
        """Horizontal axis with ``ticks`` as list of (offset, label)."""
        self.line(x, y, x + w, y, stroke=C["rule"], sw=0.9)
        for offset, label_text in ticks:
            self.line(x + offset, y, x + offset, y + 3.2, stroke=C["rule"], sw=0.9)
            self.text(x + offset, y + 11.5, label_text, size=size, fill=C["faint"],
                      anchor="middle")
        if label:
            self.text(x + w, y + 22, label, size=size, fill=C["faint"], anchor="end")

    def caption_note(self, x, y, text, size=7.0, fill=None):
        self.text(x, y, text, size=size, fill=fill or C["faint"], italic=True)

    def title(self, x, y, text, size=9.6):
        self.text(x, y, text, size=size, fill=C["ink"], weight="bold")

    def frame(self):
        """Hairline frame so a figure reads as a distinct object on the page."""
        self.rect(0.5, 0.5, self.width - 1, self.height - 1, fill="none",
                  stroke=C["rule_soft"], sw=1.0, rx=3)


def wrap(text: str, limit: int) -> list[str]:
    """Greedy word wrap for diagram labels."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if current and len(trial) > limit:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines
