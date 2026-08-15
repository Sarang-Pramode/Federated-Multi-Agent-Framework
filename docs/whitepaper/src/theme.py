"""Visual theme, font resolution, page furniture and document template.

Everything that decides how the white paper *looks* lives here so that
``whitepaper.md`` can stay pure content.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------

PALETTE = {
    "ink": colors.HexColor("#16202B"),
    "body": colors.HexColor("#26333F"),
    "muted": colors.HexColor("#5D6C7B"),
    "faint": colors.HexColor("#8494A3"),
    "accent": colors.HexColor("#1C5A9E"),
    "accent_dark": colors.HexColor("#123F72"),
    "accent_soft": colors.HexColor("#E8F0F8"),
    "teal": colors.HexColor("#0F7267"),
    "teal_soft": colors.HexColor("#E4F1EF"),
    "warn": colors.HexColor("#A8551A"),
    "warn_soft": colors.HexColor("#FBF0E4"),
    "danger": colors.HexColor("#9C2B2B"),
    "danger_soft": colors.HexColor("#F9EAEA"),
    "rule": colors.HexColor("#D2DAE2"),
    "rule_soft": colors.HexColor("#E7ECF1"),
    "table_head": colors.HexColor("#EEF3F8"),
    "table_zebra": colors.HexColor("#F8FAFC"),
    "code_bg": colors.HexColor("#F4F6F9"),
    "paper": colors.HexColor("#FFFFFF"),
}

# --------------------------------------------------------------------------
# Page geometry
# --------------------------------------------------------------------------

PAGE_SIZE = A4
MARGIN_L = 19 * mm
MARGIN_R = 19 * mm
MARGIN_T = 20 * mm
MARGIN_B = 20 * mm

CONTENT_WIDTH = PAGE_SIZE[0] - MARGIN_L - MARGIN_R
CONTENT_HEIGHT = PAGE_SIZE[1] - MARGIN_T - MARGIN_B

SANS = "WPSans"
MONO = "WPMono"

# --------------------------------------------------------------------------
# Font resolution
# --------------------------------------------------------------------------

_FONT_DIRS = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/System/Library/Fonts",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
]

# Preference order. Each entry maps the four faces we need onto candidate
# filenames; the first family whose four faces all resolve wins.
_SANS_FAMILIES = [
    (
        "Inter",
        {
            "regular": ["Inter-Regular.ttf"],
            "bold": ["Inter-SemiBold.ttf", "Inter-Bold.ttf"],
            "italic": ["Inter-Italic.ttf"],
            "boldItalic": ["Inter-SemiBoldItalic.ttf", "Inter-BoldItalic.ttf"],
        },
    ),
    (
        "Liberation Sans",
        {
            "regular": ["LiberationSans-Regular.ttf"],
            "bold": ["LiberationSans-Bold.ttf"],
            "italic": ["LiberationSans-Italic.ttf"],
            "boldItalic": ["LiberationSans-BoldItalic.ttf"],
        },
    ),
    (
        "DejaVu Sans",
        {
            "regular": ["DejaVuSans.ttf"],
            "bold": ["DejaVuSans-Bold.ttf"],
            "italic": ["DejaVuSans-Oblique.ttf"],
            "boldItalic": ["DejaVuSans-BoldOblique.ttf"],
        },
    ),
    (
        "Helvetica Neue",
        {
            "regular": ["HelveticaNeue.ttc"],
            "bold": ["HelveticaNeue.ttc"],
            "italic": ["HelveticaNeue.ttc"],
            "boldItalic": ["HelveticaNeue.ttc"],
        },
    ),
]

_MONO_FAMILIES = [
    (
        "Liberation Mono",
        {
            "regular": ["LiberationMono-Regular.ttf"],
            "bold": ["LiberationMono-Bold.ttf"],
            "italic": ["LiberationMono-Italic.ttf"],
            "boldItalic": ["LiberationMono-BoldItalic.ttf"],
        },
    ),
    (
        "DejaVu Sans Mono",
        {
            "regular": ["DejaVuSansMono.ttf"],
            "bold": ["DejaVuSansMono-Bold.ttf"],
            "italic": ["DejaVuSansMono-Oblique.ttf"],
            "boldItalic": ["DejaVuSansMono-BoldOblique.ttf"],
        },
    ),
    (
        "Menlo",
        {
            "regular": ["Menlo.ttc"],
            "bold": ["Menlo.ttc"],
            "italic": ["Menlo.ttc"],
            "boldItalic": ["Menlo.ttc"],
        },
    ),
]

_FILE_INDEX: dict[str, str] | None = None


def _index_font_files() -> dict[str, str]:
    global _FILE_INDEX
    if _FILE_INDEX is not None:
        return _FILE_INDEX
    index: dict[str, str] = {}
    for root_dir in _FONT_DIRS:
        if not os.path.isdir(root_dir):
            continue
        for dirpath, _dirnames, filenames in os.walk(root_dir):
            for name in filenames:
                if name.lower().endswith((".ttf", ".otf")):
                    index.setdefault(name, os.path.join(dirpath, name))
    _FILE_INDEX = index
    return index


def _resolve_family(candidates) -> tuple[str, dict[str, str]] | None:
    index = _index_font_files()
    for label, faces in candidates:
        resolved: dict[str, str] = {}
        for face, filenames in faces.items():
            for filename in filenames:
                if filename in index:
                    resolved[face] = index[filename]
                    break
        if len(resolved) == 4:
            return label, resolved
    return None


@dataclass
class FontReport:
    sans_label: str = "Helvetica (built-in)"
    mono_label: str = "Courier (built-in)"
    sans_family: str = "Helvetica"
    mono_family: str = "Courier"
    notes: list[str] = field(default_factory=list)


def register_fonts() -> FontReport:
    """Register embedded TrueType faces under stable aliases.

    The aliases (``WPSans`` / ``WPMono``) are also used inside the SVG figures,
    so diagram type matches body type. If no suitable TrueType family is found
    the built-in Type 1 fonts are used and the aliases point at those instead.
    """
    report = FontReport()

    sans = _resolve_family(_SANS_FAMILIES)
    if sans:
        label, faces = sans
        try:
            pdfmetrics.registerFont(TTFont(SANS, faces["regular"]))
            pdfmetrics.registerFont(TTFont(f"{SANS}-Bold", faces["bold"]))
            pdfmetrics.registerFont(TTFont(f"{SANS}-Italic", faces["italic"]))
            pdfmetrics.registerFont(TTFont(f"{SANS}-BoldItalic", faces["boldItalic"]))
            pdfmetrics.registerFontFamily(
                SANS,
                normal=SANS,
                bold=f"{SANS}-Bold",
                italic=f"{SANS}-Italic",
                boldItalic=f"{SANS}-BoldItalic",
            )
            report.sans_label = label
            report.sans_family = SANS
        except Exception as exc:  # pragma: no cover - depends on host fonts
            report.notes.append(f"sans fallback ({label}): {exc}")

    mono = _resolve_family(_MONO_FAMILIES)
    if mono:
        label, faces = mono
        try:
            pdfmetrics.registerFont(TTFont(MONO, faces["regular"]))
            pdfmetrics.registerFont(TTFont(f"{MONO}-Bold", faces["bold"]))
            pdfmetrics.registerFontFamily(
                MONO, normal=MONO, bold=f"{MONO}-Bold", italic=MONO, boldItalic=f"{MONO}-Bold"
            )
            report.mono_label = label
            report.mono_family = MONO
        except Exception as exc:  # pragma: no cover - depends on host fonts
            report.notes.append(f"mono fallback ({label}): {exc}")

    if report.sans_family == "Helvetica":
        report.notes.append("No embeddable sans family found; using built-in Helvetica.")
    if report.mono_family == "Courier":
        report.notes.append("No embeddable mono family found; using built-in Courier.")
    return report


def _hyphenation_available() -> bool:
    try:
        import pyphen  # noqa: F401
    except Exception:
        return False
    return True


# --------------------------------------------------------------------------
# Paragraph styles
# --------------------------------------------------------------------------


def build_styles(fonts: FontReport) -> dict[str, ParagraphStyle]:
    sans = fonts.sans_family
    mono = fonts.mono_family
    bold = f"{sans}-Bold" if sans != "Helvetica" else "Helvetica-Bold"
    italic = f"{sans}-Italic" if sans != "Helvetica" else "Helvetica-Oblique"

    hyphen = {"hyphenationLang": "en_US"} if _hyphenation_available() else {}

    S: dict[str, ParagraphStyle] = {}

    # ---- cover -----------------------------------------------------------
    S["CoverKicker"] = ParagraphStyle(
        "CoverKicker", fontName=bold, fontSize=9, leading=12,
        textColor=PALETTE["accent"], spaceAfter=0, textTransform="uppercase",
    )
    S["CoverTitle"] = ParagraphStyle(
        "CoverTitle", fontName=bold, fontSize=31, leading=36,
        textColor=PALETTE["ink"], spaceBefore=14, spaceAfter=6,
    )
    S["CoverSubtitle"] = ParagraphStyle(
        "CoverSubtitle", fontName=sans, fontSize=13.5, leading=19,
        textColor=PALETTE["muted"], spaceAfter=20,
    )
    S["CoverLead"] = ParagraphStyle(
        "CoverLead", fontName=sans, fontSize=10, leading=15.4,
        textColor=PALETTE["body"], spaceAfter=9, alignment=TA_LEFT, **hyphen,
    )
    S["CoverMetaLabel"] = ParagraphStyle(
        "CoverMetaLabel", fontName=bold, fontSize=7.4, leading=10,
        textColor=PALETTE["faint"], textTransform="uppercase",
    )
    S["CoverMetaValue"] = ParagraphStyle(
        "CoverMetaValue", fontName=sans, fontSize=9.2, leading=13,
        textColor=PALETTE["ink"],
    )

    # ---- structure -------------------------------------------------------
    S["TOCHeading"] = ParagraphStyle(
        "TOCHeading", fontName=bold, fontSize=17, leading=21,
        textColor=PALETTE["ink"], spaceAfter=14,
    )
    S["PartKicker"] = ParagraphStyle(
        "PartKicker", fontName=bold, fontSize=9.5, leading=13,
        textColor=PALETTE["accent"], textTransform="uppercase", spaceAfter=6,
    )
    S["PartTitle"] = ParagraphStyle(
        "PartTitle", fontName=bold, fontSize=24, leading=29,
        textColor=PALETTE["ink"], spaceAfter=10,
    )
    S["PartIntro"] = ParagraphStyle(
        "PartIntro", fontName=sans, fontSize=10.2, leading=16,
        textColor=PALETTE["muted"], spaceAfter=8, alignment=TA_LEFT, **hyphen,
    )
    S["H2"] = ParagraphStyle(
        "H2", fontName=bold, fontSize=15.5, leading=19.5,
        textColor=PALETTE["ink"], spaceBefore=18, spaceAfter=7, keepWithNext=1,
    )
    S["H3"] = ParagraphStyle(
        "H3", fontName=bold, fontSize=11.4, leading=15,
        textColor=PALETTE["accent_dark"], spaceBefore=13, spaceAfter=4.5, keepWithNext=1,
    )
    S["H4"] = ParagraphStyle(
        "H4", fontName=bold, fontSize=9.6, leading=13,
        textColor=PALETTE["ink"], spaceBefore=10, spaceAfter=3, keepWithNext=1,
    )

    # ---- body ------------------------------------------------------------
    S["Body"] = ParagraphStyle(
        "Body", fontName=sans, fontSize=9.3, leading=14.1,
        textColor=PALETTE["body"], alignment=TA_JUSTIFY, spaceAfter=7.4, **hyphen,
    )
    S["BodyLead"] = ParagraphStyle(
        "BodyLead", parent=S["Body"], fontSize=10.1, leading=15.6,
        textColor=PALETTE["ink"], spaceAfter=8.4,
    )
    S["Bullet"] = ParagraphStyle(
        "Bullet", parent=S["Body"], leftIndent=13, bulletIndent=2.5,
        spaceAfter=3.6, alignment=TA_LEFT, bulletFontName=sans, bulletFontSize=9.3,
    )
    S["BulletL2"] = ParagraphStyle(
        "BulletL2", parent=S["Bullet"], leftIndent=26, bulletIndent=15.5,
        fontSize=9.0, leading=13.4,
    )
    S["Numbered"] = ParagraphStyle(
        "Numbered", parent=S["Body"], leftIndent=17, bulletIndent=2.5,
        spaceAfter=3.6, alignment=TA_LEFT, bulletFontName=sans, bulletFontSize=9.3,
    )
    S["Reference"] = ParagraphStyle(
        "Reference", parent=S["Body"], fontSize=8.4, leading=12.2,
        leftIndent=19, firstLineIndent=-19, spaceAfter=5.2, alignment=TA_LEFT,
    )

    # ---- tables ----------------------------------------------------------
    S["TableHeader"] = ParagraphStyle(
        "TableHeader", fontName=bold, fontSize=7.9, leading=10.4,
        textColor=PALETTE["ink"], alignment=TA_LEFT,
    )
    S["TableCell"] = ParagraphStyle(
        "TableCell", fontName=sans, fontSize=7.9, leading=10.9,
        textColor=PALETTE["body"], alignment=TA_LEFT,
    )
    S["TableCellRight"] = ParagraphStyle(
        "TableCellRight", parent=S["TableCell"], alignment=TA_RIGHT,
    )
    S["TableCellCenter"] = ParagraphStyle(
        "TableCellCenter", parent=S["TableCell"], alignment=TA_CENTER,
    )
    S["TableHeaderRight"] = ParagraphStyle(
        "TableHeaderRight", parent=S["TableHeader"], alignment=TA_RIGHT,
    )
    S["TableHeaderCenter"] = ParagraphStyle(
        "TableHeaderCenter", parent=S["TableHeader"], alignment=TA_CENTER,
    )

    # ---- captions and callouts ------------------------------------------
    S["FigureCaption"] = ParagraphStyle(
        "FigureCaption", fontName=sans, fontSize=7.9, leading=11.4,
        textColor=PALETTE["muted"], spaceBefore=5, spaceAfter=12, alignment=TA_LEFT,
    )
    S["TableCaption"] = ParagraphStyle(
        "TableCaption", fontName=sans, fontSize=7.9, leading=11.4,
        textColor=PALETTE["muted"], spaceBefore=2, spaceAfter=4.5,
        alignment=TA_LEFT, keepWithNext=1,
    )
    S["Callout"] = ParagraphStyle(
        "Callout", fontName=sans, fontSize=9.1, leading=13.8,
        textColor=PALETTE["ink"], alignment=TA_LEFT, spaceAfter=5, **hyphen,
    )
    S["Code"] = ParagraphStyle(
        "Code", fontName=mono, fontSize=7.6, leading=10.6,
        textColor=PALETTE["ink"], alignment=TA_LEFT,
    )

    return S


# --------------------------------------------------------------------------
# Canvas with "page X of Y"
# --------------------------------------------------------------------------


class NumberedCanvas(rl_canvas.Canvas):
    """Buffers pages so the footer can print a resolved total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states: list[dict] = []

    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._stamp_page_number(total)
            super().showPage()
        super().save()

    def _stamp_page_number(self, total: int) -> None:
        spec = getattr(self, "_wp_footer", None)
        if not spec:
            return
        self.saveState()
        self.setFont(spec["font"], spec["size"])
        self.setFillColor(PALETTE["faint"])
        self.drawRightString(spec["x"], spec["y"], f"Page {spec['page']} of {total}")
        self.restoreState()


# --------------------------------------------------------------------------
# Document template
# --------------------------------------------------------------------------


class WhitepaperDoc(BaseDocTemplate):
    def __init__(self, filename: str, meta: dict, fonts: FontReport, **kwargs):
        self.meta = meta
        self.fonts = fonts
        self.current_chapter = ""
        self.current_part = ""
        self._page_chapter = ""
        self._page_part = ""
        super().__init__(
            filename,
            pagesize=PAGE_SIZE,
            leftMargin=MARGIN_L,
            rightMargin=MARGIN_R,
            topMargin=MARGIN_T,
            bottomMargin=MARGIN_B,
            title=meta.get("title", "White Paper"),
            author=meta.get("author", ""),
            subject=meta.get("subtitle", ""),
            creator="docs/whitepaper/build.py",
            **kwargs,
        )

        frame = Frame(
            MARGIN_L, MARGIN_B, CONTENT_WIDTH, CONTENT_HEIGHT,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
            id="main",
        )
        cover_frame = Frame(
            MARGIN_L, MARGIN_B, CONTENT_WIDTH, CONTENT_HEIGHT,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
            id="cover",
        )
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPageEnd=self._cover_chrome),
            PageTemplate(id="body", frames=[frame], onPageEnd=self._body_chrome),
        ])

    # -- running head bookkeeping -----------------------------------------

    def beforeDocument(self):
        # multiBuild reuses this instance across passes; without a reset the
        # running heads leak the final chapter of the previous pass onto the
        # front matter of the next one.
        self.current_chapter = ""
        self.current_part = ""

    def _cover_chrome(self, canvas, doc):
        canvas._wp_footer = None

    def _body_chrome(self, canvas, doc):
        sans = self.fonts.sans_family
        left_text = self.meta.get("running_title", self.meta.get("title", ""))
        # Read at page end: a part divider or new chapter that opens on this
        # page then names the page correctly.
        right_text = self.current_chapter or self.current_part or ""

        top_y = PAGE_SIZE[1] - MARGIN_T + 8.5
        canvas.saveState()
        canvas.setFont(sans, 7.2)
        canvas.setFillColor(PALETTE["faint"])
        canvas.drawString(MARGIN_L, top_y, left_text)
        if right_text:
            canvas.drawRightString(PAGE_SIZE[0] - MARGIN_R, top_y, _clip(right_text, 78))
        canvas.setStrokeColor(PALETTE["rule_soft"])
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_L, top_y - 3.6, PAGE_SIZE[0] - MARGIN_R, top_y - 3.6)

        bottom_y = MARGIN_B - 13
        canvas.setStrokeColor(PALETTE["rule_soft"])
        canvas.line(MARGIN_L, bottom_y + 9.5, PAGE_SIZE[0] - MARGIN_R, bottom_y + 9.5)
        canvas.setFont(sans, 7.2)
        canvas.setFillColor(PALETTE["faint"])
        canvas.drawString(MARGIN_L, bottom_y, self.meta.get("footer_left", ""))
        canvas.restoreState()

        canvas._wp_footer = {
            "font": sans,
            "size": 7.2,
            "x": PAGE_SIZE[0] - MARGIN_R,
            "y": bottom_y,
            "page": doc.page,
        }

    # -- outline + table of contents --------------------------------------

    def afterFlowable(self, flowable):
        level = getattr(flowable, "_toc_level", None)
        if level is None:
            return
        text = getattr(flowable, "_toc_text", "")
        key = getattr(flowable, "_toc_key", None)
        kind = getattr(flowable, "_toc_kind", "")

        if kind == "part":
            self.current_part = text
            self.current_chapter = ""
        elif kind == "chapter":
            self.current_chapter = text

        if key:
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=(level > 0))
        self.notify("TOCEntry", (level, text, self.page, key))


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"
