#!/usr/bin/env python3
"""Render whitepaper.md into a typeset PDF.

    ./.venv/bin/python build.py [--in whitepaper.md] [--out out/<name>.pdf]

The Markdown file is the single source of truth; this script owns layout only.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

from src import mdparse  # noqa: E402
from src.figures import register_svg_fonts  # noqa: E402
from src.flow import Renderer  # noqa: E402
from src.inline import render as inline_render  # noqa: E402
from src.theme import (  # noqa: E402
    CONTENT_WIDTH,
    PALETTE,
    NumberedCanvas,
    WhitepaperDoc,
    build_styles,
    register_fonts,
)

DEFAULT_IN = os.path.join(HERE, "whitepaper.md")
DEFAULT_OUT = os.path.join(HERE, "out", "Federated_Enterprise_Agent_Platform_v1.0.pdf")


def build_cover(meta: dict, styles: dict, fonts) -> list:
    mono = fonts.mono_family
    story: list = []
    story.append(Spacer(1, 26 * mm))
    story.append(Paragraph(meta.get("kicker", "White Paper"), styles["CoverKicker"]))
    story.append(HRFlowable(width="22%", thickness=2.6, color=PALETTE["accent"],
                            spaceBefore=7, spaceAfter=13, hAlign="LEFT"))
    story.append(Paragraph(inline_render(meta.get("title", ""), mono), styles["CoverTitle"]))
    story.append(Paragraph(inline_render(meta.get("subtitle", ""), mono), styles["CoverSubtitle"]))

    for key in ("lead", "lead2"):
        if meta.get(key):
            story.append(Paragraph(inline_render(meta[key], mono), styles["CoverLead"]))

    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.7, color=PALETTE["rule"],
                            spaceBefore=0, spaceAfter=11))

    fields = [
        ("Author", meta.get("author", "")),
        ("Document", meta.get("version", "")),
        ("Date", meta.get("date", "")),
        ("Status", meta.get("status", "")),
    ]
    cells = []
    for label, value in fields:
        if not value:
            continue
        cells.append([
            Paragraph(label, styles["CoverMetaLabel"]),
            Paragraph(inline_render(value, mono), styles["CoverMetaValue"]),
        ])
    if cells:
        meta_table = Table(cells, colWidths=[26 * mm, CONTENT_WIDTH - 26 * mm], hAlign="LEFT")
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2.4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.4),
        ]))
        story.append(meta_table)

    if meta.get("scope"):
        story.append(Spacer(1, 7 * mm))
        panel = Table(
            [[Paragraph(inline_render(meta["scope"], mono), styles["Callout"])]],
            colWidths=[CONTENT_WIDTH], hAlign="LEFT",
        )
        panel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent_soft"]),
            ("LINEBEFORE", (0, 0), (0, -1), 2.6, PALETTE["accent"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(panel)
    return story


def build_toc(styles: dict, fonts) -> list:
    sans = fonts.sans_family
    bold = f"{sans}-Bold" if sans != "Helvetica" else "Helvetica-Bold"

    toc = TableOfContents()
    toc.dotsMinLevel = 1
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName=bold, fontSize=9.8, leading=15,
                       textColor=PALETTE["ink"], spaceBefore=11, spaceAfter=2.5,
                       leftIndent=0, firstLineIndent=0, alignment=TA_LEFT),
        ParagraphStyle("TOC1", fontName=sans, fontSize=9.1, leading=13.4,
                       textColor=PALETTE["body"], leftIndent=11, firstLineIndent=0,
                       spaceBefore=1.4, alignment=TA_LEFT),
        ParagraphStyle("TOC2", fontName=sans, fontSize=8.3, leading=12,
                       textColor=PALETTE["muted"], leftIndent=25, firstLineIndent=0,
                       spaceBefore=0.6, alignment=TA_LEFT),
    ]

    story: list = [Paragraph("Contents", styles["TOCHeading"]),
                   HRFlowable(width="100%", thickness=0.7, color=PALETTE["rule"],
                              spaceBefore=0, spaceAfter=10),
                   toc]
    return story


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=DEFAULT_IN)
    ap.add_argument("--out", dest="dst", default=DEFAULT_OUT)
    args = ap.parse_args()

    started = time.time()
    with open(args.src, "r", encoding="utf-8") as handle:
        text = handle.read()

    meta, blocks = mdparse.parse(text)
    fonts = register_fonts()
    register_svg_fonts(fonts)
    styles = build_styles(fonts)

    renderer = Renderer(styles, fonts, CONTENT_WIDTH, os.path.join(HERE, "figures"))
    renderer.annotate(blocks)
    body = renderer.render(blocks)

    os.makedirs(os.path.dirname(args.dst), exist_ok=True)
    doc = WhitepaperDoc(args.dst, meta, fonts)

    story: list = []
    story.append(NextPageTemplate("body"))
    story.extend(build_cover(meta, styles, fonts))
    story.append(PageBreak())
    story.extend(build_toc(styles, fonts))
    story.append(PageBreak())
    story.extend(body)

    doc.multiBuild(story, canvasmaker=NumberedCanvas)

    elapsed = time.time() - started
    size_kb = os.path.getsize(args.dst) / 1024.0
    print(f"built {args.dst}")
    print(f"  fonts     : {fonts.sans_label} / {fonts.mono_label}")
    print(f"  figures   : {renderer.figure_count}")
    print(f"  tables    : {renderer.table_count}")
    print(f"  pages     : {doc.page}")
    print(f"  size      : {size_kb:.0f} KB in {elapsed:.1f}s")
    for note in fonts.notes:
        print(f"  font note : {note}")
    seen = set()
    for warning in renderer.warnings:
        if warning in seen:
            continue
        seen.add(warning)
        print(f"  WARNING   : {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
