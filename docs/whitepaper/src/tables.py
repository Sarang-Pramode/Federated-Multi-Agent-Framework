"""Pipe-table to ReportLab Table conversion with automatic column widths."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, Table, TableStyle

from .inline import plain, render
from .theme import PALETTE

CELL_PAD_H = 4.6
CELL_PAD_V = 3.4
MIN_COL_WIDTH = 30.0


def _text_width(text: str, font: str, size: float) -> float:
    try:
        return pdfmetrics.stringWidth(text, font, size)
    except Exception:
        return len(text) * size * 0.5


def _longest_word_width(text: str, font: str, size: float) -> float:
    widest = 0.0
    for word in text.split():
        widest = max(widest, _text_width(word, font, size))
    return widest


def compute_widths(rows: list[list[str]], avail: float, font: str, bold_font: str,
                   size: float) -> list[float]:
    ncols = len(rows[0])
    pad = 2 * CELL_PAD_H

    natural = [0.0] * ncols
    floor = [0.0] * ncols
    for row_idx, row in enumerate(rows):
        face = bold_font if row_idx == 0 else font
        for col, cell in enumerate(row):
            text = plain(cell)
            natural[col] = max(natural[col], _text_width(text, face, size) + pad)
            floor[col] = max(floor[col], _longest_word_width(text, face, size) + pad)
    floor = [max(MIN_COL_WIDTH, f) for f in floor]
    # A single very wide cell should not be able to pin a column open.
    floor = [min(f, avail / max(2, ncols) * 1.9) for f in floor]
    # Intrinsically narrow columns (short labels, numbers, verdicts) should not
    # be squeezed into wrapping just because a prose column is greedy; let the
    # prose columns absorb the squeeze instead.
    narrow_cap = avail * 0.12
    floor = [max(floor[i], min(natural[i], narrow_cap)) for i in range(ncols)]

    total_natural = sum(natural)
    if total_natural <= avail:
        # Grow proportionally so the table always spans the text block.
        scale = avail / total_natural if total_natural else 1.0
        return [w * scale for w in natural]

    widths = list(natural)
    for _ in range(60):
        excess = sum(widths) - avail
        if excess <= 0.05:
            break
        shrinkable = [i for i in range(ncols) if widths[i] > floor[i] + 0.05]
        if not shrinkable:
            break
        headroom = sum(widths[i] - floor[i] for i in shrinkable)
        if headroom <= excess:
            for i in shrinkable:
                widths[i] = floor[i]
            break
        for i in shrinkable:
            widths[i] -= (widths[i] - floor[i]) / headroom * excess

    total = sum(widths)
    if total > avail:
        widths = [w * avail / total for w in widths]
    elif total < avail:
        widths = [w * avail / total for w in widths]
    return widths


def build_table(rows: list[list[str]], aligns: list[str], styles: dict, avail: float,
                mono_font: str) -> Table:
    header_style = {
        "left": styles["TableHeader"],
        "right": styles["TableHeaderRight"],
        "center": styles["TableHeaderCenter"],
    }
    cell_style = {
        "left": styles["TableCell"],
        "right": styles["TableCellRight"],
        "center": styles["TableCellCenter"],
    }

    body_font = styles["TableCell"].fontName
    head_font = styles["TableHeader"].fontName
    size = styles["TableCell"].fontSize
    widths = compute_widths(rows, avail, body_font, head_font, size)

    data = []
    for row_idx, row in enumerate(rows):
        rendered = []
        for col, cell in enumerate(row):
            align = aligns[col] if col < len(aligns) else "left"
            style = header_style[align] if row_idx == 0 else cell_style[align]
            rendered.append(Paragraph(render(cell, mono_font), style))
        data.append(rendered)

    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")

    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), CELL_PAD_H),
        ("RIGHTPADDING", (0, 0), (-1, -1), CELL_PAD_H),
        ("TOPPADDING", (0, 0), (-1, -1), CELL_PAD_V),
        ("BOTTOMPADDING", (0, 0), (-1, -1), CELL_PAD_V),
        ("BACKGROUND", (0, 0), (-1, 0), PALETTE["table_head"]),
        ("TOPPADDING", (0, 0), (-1, 0), CELL_PAD_V + 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, 0), CELL_PAD_V + 1.2),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, PALETTE["accent"]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, PALETTE["accent"]),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, PALETTE["rule_soft"]),
        ("LINEBELOW", (0, -1), (-1, -1), 0.7, PALETTE["rule"]),
    ]
    for row_idx in range(2, len(data), 2):
        commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), PALETTE["table_zebra"]))

    table.setStyle(TableStyle(commands))
    return table
