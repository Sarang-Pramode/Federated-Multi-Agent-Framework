"""Blocks to ReportLab flowables: numbering, cross-references, panels."""

from __future__ import annotations

import os
import re

from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

from .figures import load_svg, resolve_width
from .inline import plain, render
from .mdparse import Block
from .theme import CONTENT_HEIGHT, PALETTE

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# A table taller than this share of the text block may break across pages.
TALL_TABLE_FRACTION = 0.5
# Header plus this many body rows must fit beneath a caption before a break.
MIN_ROWS_WITH_CAPTION = 4

ID_RE = re.compile(r"\s*\{#([\w-]+)\}\s*")
REF_RE = re.compile(r"\{(fig|tbl|ch|sec):([\w-]+)\}")

CALLOUT_COLORS = {
    "quote": ("accent", "accent_soft"),
    "insight": ("accent", "accent_soft"),
    "decision": ("teal", "teal_soft"),
    "rule": ("teal", "teal_soft"),
    "warning": ("warn", "warn_soft"),
    "antipattern": ("danger", "danger_soft"),
}

CALLOUT_KEYWORDS = [
    ("anti-pattern", "antipattern"),
    ("failure mode", "antipattern"),
    ("warning", "warning"),
    ("caution", "warning"),
    ("do not", "warning"),
    ("design rule", "decision"),
    ("decision", "decision"),
    ("rule of thumb", "decision"),
    ("north-star", "decision"),
    ("takeaway", "insight"),
    ("key point", "insight"),
]


class Renderer:
    def __init__(self, styles: dict, fonts, content_width: float, figures_dir: str):
        self.styles = styles
        self.fonts = fonts
        self.width = content_width
        self.figures_dir = figures_dir
        self.mono = fonts.mono_family
        self.refs: dict[str, str] = {}
        self.warnings: list[str] = []
        self.figure_count = 0
        self.table_count = 0

    # -- pass 1: numbering + reference registry ---------------------------

    def annotate(self, blocks: list[Block]) -> None:
        part = 0
        chapter = 0
        section = 0
        subsection = 0
        figure = 0
        table = 0
        expect_table_caption = False
        previous_kind = ""

        for block in blocks:
            if block.kind == "para" and previous_kind == "part":
                block.attrs["part_intro"] = True
            previous_kind = block.kind

            if block.kind in ("part", "chapter", "section", "subsection"):
                block.text, ident = _extract_id(block.text)
                numbered = block.attrs.get("numbered", True)
                if block.kind == "part":
                    part += 1
                    label = f"Part {ROMAN[part] if part < len(ROMAN) else part}"
                    block.attrs["label"] = label
                    if ident:
                        self.refs[ident] = label
                elif block.kind == "chapter":
                    if numbered:
                        chapter += 1
                        section = 0
                        subsection = 0
                        block.attrs["number"] = str(chapter)
                        if ident:
                            self.refs[ident] = str(chapter)
                elif block.kind == "section":
                    if numbered:
                        section += 1
                        subsection = 0
                        block.attrs["number"] = f"{chapter}.{section}"
                        if ident:
                            self.refs[ident] = f"{chapter}.{section}"
                elif block.kind == "subsection":
                    if numbered:
                        subsection += 1
                        block.attrs["number"] = f"{chapter}.{section}.{subsection}"
                        if ident:
                            self.refs[ident] = f"{chapter}.{section}.{subsection}"
                continue

            if block.kind == "figure":
                figure += 1
                block.attrs["number"] = str(figure)
                ident = block.attrs.get("id")
                if ident:
                    self.refs[ident] = str(figure)
                continue

            if block.kind == "para" and block.text.startswith("Table."):
                table += 1
                caption = block.text[len("Table."):].strip()
                caption, ident = _extract_id(caption)
                block.kind = "table-caption"
                block.text = caption
                block.attrs["number"] = str(table)
                if ident:
                    self.refs[ident] = str(table)
                expect_table_caption = True
                continue

            if block.kind == "table":
                if not expect_table_caption:
                    pass
                expect_table_caption = False

        self.figure_count = figure
        self.table_count = table

    # -- reference substitution -------------------------------------------

    def subst(self, text: str) -> str:
        def repl(match: re.Match) -> str:
            kind, ident = match.group(1), match.group(2)
            # Accept either the bare id or the conventional prefixed form, so
            # {fig:smoke} resolves against an id of "smoke" or "fig-smoke".
            candidates = [ident, f"{kind}-{ident}"]
            if kind in ("ch", "sec"):
                candidates += [f"ch-{ident}", f"sec-{ident}"]
            value = next((self.refs[c] for c in candidates if c in self.refs), None)
            if value is None:
                self.warnings.append(f"unresolved reference {{{kind}:{ident}}}")
                return {"fig": "Figure ?", "tbl": "Table ?", "ch": "?", "sec": "?"}[kind]
            prefix = {"fig": "Figure ", "tbl": "Table ", "ch": "", "sec": ""}[kind]
            return f"{prefix}{value}"

        return REF_RE.sub(repl, text)

    def para(self, text: str, style_name: str) -> Paragraph:
        return Paragraph(render(self.subst(text), self.mono), self.styles[style_name])

    # -- pass 2: flowables -------------------------------------------------

    def render(self, blocks: list[Block]) -> list:
        story: list = []
        first_part_seen = False
        previous_kind = ""
        pending_caption: str | None = None

        for index, block in enumerate(blocks):
            kind = block.kind
            after_part = previous_kind in ("part", "part-intro")
            previous_kind = "part-intro" if (kind == "para" and block.attrs.get("part_intro")) else kind

            if kind == "part":
                if first_part_seen:
                    story.append(PageBreak())
                first_part_seen = True
                story.append(Spacer(1, 34 * mm))
                story.append(self._heading(block.attrs["label"], "PartKicker", "part",
                                           toc_level=0, toc_text=block.attrs["label"] + " - " + plain(block.text)))
                story.append(Paragraph(render(self.subst(block.text), self.mono),
                                       self.styles["PartTitle"]))
                story.append(HRFlowable(width="100%", thickness=1.4, color=PALETTE["accent"],
                                        spaceBefore=4, spaceAfter=12))
                continue

            if kind == "chapter":
                number = block.attrs.get("number")
                title = plain(self.subst(block.text))
                display = f"{number}. {title}" if number else title
                if after_part:
                    # The part divider already carries a rule; a second one
                    # immediately below reads as a stray line.
                    story.append(Spacer(1, 6))
                else:
                    story.append(CondPageBreak(150))
                    story.append(HRFlowable(width="34%", thickness=2.2, color=PALETTE["accent"],
                                            spaceBefore=6, spaceAfter=7, hAlign="LEFT"))
                accent = _hex(PALETTE["accent"])
                markup = (f'<font color="{accent}">{number}.</font> {render(self.subst(block.text), self.mono)}'
                          if number else render(self.subst(block.text), self.mono))
                story.append(self._heading_markup(markup, "H2", "chapter", toc_level=1,
                                                  toc_text=display))
                continue

            if kind == "section":
                number = block.attrs.get("number")
                title = plain(self.subst(block.text))
                display = f"{number} {title}" if number else title
                markup = (f"{number}&nbsp;&nbsp;{render(self.subst(block.text), self.mono)}"
                          if number else render(self.subst(block.text), self.mono))
                story.append(self._heading_markup(markup, "H3", "section", toc_level=2,
                                                  toc_text=display))
                continue

            if kind == "subsection":
                number = block.attrs.get("number")
                markup = (f"{number}&nbsp;&nbsp;{render(self.subst(block.text), self.mono)}"
                          if number else render(self.subst(block.text), self.mono))
                story.append(Paragraph(markup, self.styles["H4"]))
                continue

            if kind == "para":
                if block.attrs.get("part_intro"):
                    style = "PartIntro"
                elif block.attrs.get("lead"):
                    style = "BodyLead"
                else:
                    style = "Body"
                story.append(self.para(block.text, style))
                continue

            if kind == "table-caption":
                markup = (f"<b>Table {block.attrs['number']}.</b> "
                          + render(self.subst(block.text), self.mono))
                pending_caption = markup
                continue

            if kind == "table":
                from .tables import build_table
                rows = [[self.subst(cell) for cell in row] for row in block.rows]
                table = build_table(rows, block.aligns, self.styles, self.width, self.mono)
                story.extend(self._table_group(pending_caption, table))
                pending_caption = None
                story.append(Spacer(1, 9))
                continue

            if kind == "bullets":
                story.extend(self._list(block.items, ordered=False))
                story.append(Spacer(1, 4.5))
                continue

            if kind == "numbers":
                story.extend(self._list(block.items, ordered=True))
                story.append(Spacer(1, 4.5))
                continue

            if kind == "callout":
                story.append(self._callout(block))
                continue

            if kind == "code":
                story.append(self._code(block.text))
                continue

            if kind == "figure":
                story.extend(self._figure(block))
                continue

            if kind == "refs":
                for entry in block.items:
                    story.append(Paragraph(_reference_markup(entry, self.mono),
                                           self.styles["Reference"]))
                continue

            if kind == "pagebreak":
                story.append(PageBreak())
                continue

            if kind == "rule":
                story.append(HRFlowable(width="100%", thickness=0.6, color=PALETTE["rule"],
                                        spaceBefore=6, spaceAfter=10))
                continue

        return story

    # -- helpers -----------------------------------------------------------

    def _heading(self, text: str, style_name: str, kind: str, toc_level: int,
                 toc_text: str) -> Paragraph:
        return self._heading_markup(render(text, self.mono), style_name, kind, toc_level, toc_text)

    def _heading_markup(self, markup: str, style_name: str, kind: str, toc_level: int,
                        toc_text: str) -> Paragraph:
        para = Paragraph(markup, self.styles[style_name])
        para._toc_level = toc_level
        para._toc_text = toc_text
        para._toc_kind = kind
        para._toc_key = _slug(f"{kind}-{toc_text}")
        return para

    def _list(self, items, ordered: bool) -> list:
        out = []
        for level, marker, text in items:
            style = self.styles["Bullet"] if level == 0 else self.styles["BulletL2"]
            if ordered:
                style = self.styles["Numbered"] if level == 0 else self.styles["BulletL2"]
                bullet = f"{marker}."
            else:
                bullet = "\u2022" if level == 0 else "\u2013"
            out.append(Paragraph(render(self.subst(text), self.mono), style, bulletText=bullet))
        return out

    def _callout(self, block: Block) -> Table:
        kind = block.attrs.get("type", "quote")
        if kind == "quote" and block.items:
            probe = plain(block.items[0]).lower()[:60]
            for keyword, mapped in CALLOUT_KEYWORDS:
                if keyword in probe:
                    kind = mapped
                    break
        bar_key, bg_key = CALLOUT_COLORS.get(kind, CALLOUT_COLORS["quote"])

        inner = []
        for idx, text in enumerate(block.items):
            para = Paragraph(render(self.subst(text), self.mono), self.styles["Callout"])
            inner.append(para)
        if inner:
            inner[-1].style = self.styles["Callout"]

        table = Table([[inner]], colWidths=[self.width], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALETTE[bg_key]),
            ("LINEBEFORE", (0, 0), (0, -1), 2.6, PALETTE[bar_key]),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        wrapper = Table([[table]], colWidths=[self.width], hAlign="LEFT")
        wrapper.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return wrapper

    def _code(self, text: str) -> Table:
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        block = XPreformatted(safe, self.styles["Code"])
        table = Table([[block]], colWidths=[self.width], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALETTE["code_bg"]),
            ("BOX", (0, 0), (-1, -1), 0.4, PALETTE["rule_soft"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        outer = Table([[table]], colWidths=[self.width], hAlign="LEFT")
        outer.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        return outer

    def _table_group(self, caption_markup: str | None, table: Table) -> list:
        """Keep a caption with its table, but let a tall table break across pages.

        A caption styled keepWithNext binds it to the table as one unbreakable
        unit, which is right for a small table and wrong for a long one: a table
        that would fit on a fresh page is moved there whole, stranding whatever
        precedes it above half a page of white. Past a height threshold the
        caption is therefore released and the table is allowed to split on its
        repeated header row, guarded by a conditional break so the caption can
        never land with fewer than a few rows beneath it.
        """
        if caption_markup is None:
            return [table]

        table_height = table.wrap(self.width, CONTENT_HEIGHT)[1]
        if table_height <= CONTENT_HEIGHT * TALL_TABLE_FRACTION:
            return [Paragraph(caption_markup, self.styles["TableCaption"]), table]

        style = self.styles["TableCaption"].clone("TableCaptionSplit")
        style.keepWithNext = 0
        caption = Paragraph(caption_markup, style)
        caption_height = caption.wrap(self.width, CONTENT_HEIGHT)[1]
        row_heights = getattr(table, "_rowHeights", None) or []
        keep = caption_height + sum(row_heights[:MIN_ROWS_WITH_CAPTION])
        return [CondPageBreak(keep), caption, table]

    def _figure(self, block: Block) -> list:
        src = block.attrs.get("src")
        if not src:
            self.warnings.append("figure block without src")
            return []
        path = os.path.join(self.figures_dir, src)
        target = resolve_width(block.attrs.get("width"), self.width)
        try:
            drawing = load_svg(path, target, max_height=CONTENT_HEIGHT - 95)
        except Exception as exc:
            self.warnings.append(f"figure {src}: {exc}")
            return [self.para(f"*Figure unavailable: {src}*", "Body")]

        markup = (f"<b>Figure {block.attrs['number']}.</b> "
                  + render(self.subst(block.text), self.mono))
        caption = Paragraph(markup, self.styles["FigureCaption"])
        return [Spacer(1, 5), KeepTogether([drawing, Spacer(1, 2), caption])]


def _reference_markup(entry: str, mono_font: str) -> str:
    """Put the URL of a reference on its own line.

    Long URLs otherwise break mid-word inside the citation text, which reads
    like a typo rather than a line break.
    """
    match = re.search(r"https?://\S+", entry)
    if not match:
        return render(entry, mono_font)
    head = entry[: match.start()].strip()
    url = match.group(0).rstrip(".,;")
    tail = entry[match.end():].strip()
    parts = [render(head, mono_font)] if head else []
    parts.append(f'<font size="7.5" color="{_hex(PALETTE["accent"])}">{url}</font>')
    if tail:
        parts.append(render(tail, mono_font))
    return "<br/>".join(parts)


def _extract_id(text: str) -> tuple[str, str | None]:
    match = ID_RE.search(text)
    if not match:
        return text.strip(), None
    ident = match.group(1)
    cleaned = ID_RE.sub(" ", text).strip()
    return cleaned, ident


def _hex(color) -> str:
    value = color.hexval()
    return "#" + value[2:] if value.startswith("0x") else value


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:90]
