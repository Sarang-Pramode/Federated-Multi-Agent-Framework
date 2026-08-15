"""Inline Markdown to ReportLab mini-HTML."""

from __future__ import annotations

import re

from .theme import PALETTE

_CODE_TOKEN = "\x00CODE%d\x00"

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.DOTALL)
_ITALIC_STAR_RE = re.compile(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])")
_ITALIC_UNDER_RE = re.compile(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])")
_CODE_RE = re.compile(r"`([^`]+)`")


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(text: str, mono_font: str = "WPMono", link_color: str | None = None) -> str:
    """Convert a line of Markdown into ReportLab paragraph markup."""
    if not text:
        return ""

    # Pull code spans out first so their contents are never re-parsed.
    codes: list[str] = []

    def stash_code(match: re.Match) -> str:
        codes.append(match.group(1))
        return _CODE_TOKEN % (len(codes) - 1)

    work = _CODE_RE.sub(stash_code, text)
    work = _escape(work)

    accent = link_color or PALETTE["accent"].hexval()[2:]
    if not accent.startswith("#"):
        accent = "#" + accent

    def link_sub(match: re.Match) -> str:
        label, url = match.group(1), match.group(2)
        return f'<link href="{url}" color="{accent}">{label}</link>'

    work = _LINK_RE.sub(link_sub, work)
    work = _BOLD_RE.sub(r"<b>\1</b>", work)
    work = _ITALIC_STAR_RE.sub(r"<i>\1</i>", work)
    work = _ITALIC_UNDER_RE.sub(r"<i>\1</i>", work)

    # Restore code spans as monospaced, tinted runs.
    code_color = PALETTE["accent_dark"].hexval()[2:]
    if not code_color.startswith("#"):
        code_color = "#" + code_color
    for idx, snippet in enumerate(codes):
        markup = f'<font face="{mono_font}" size="8.2" color="{code_color}">{_escape(snippet)}</font>'
        work = work.replace(_CODE_TOKEN % idx, markup)

    return work


def plain(text: str) -> str:
    """Strip Markdown syntax; used for width measurement and running heads."""
    if not text:
        return ""
    out = _CODE_RE.sub(r"\1", text)
    out = _LINK_RE.sub(r"\1", out)
    out = _BOLD_RE.sub(r"\1", out)
    out = _ITALIC_STAR_RE.sub(r"\1", out)
    out = _ITALIC_UNDER_RE.sub(r"\1", out)
    return out.strip()
