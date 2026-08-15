"""A deliberately small Markdown subset parser.

Only the constructs the white paper actually uses are supported, which keeps
the renderer predictable:

* ``#``/``##``/``###``/``####`` headings, with a trailing ``{-}`` to opt out of
  automatic numbering
* paragraphs, ``-`` bullets (two levels), ``1.`` ordered lists
* GitHub pipe tables with alignment row
* ``>`` blockquotes, rendered as callout panels
* fenced code blocks
* ``::: figure id=... width=...`` / ``::: pagebreak`` / ``::: refs`` directives,
  where a figure block holds a Markdown image line and its caption
* YAML-ish front matter delimited by ``---``

A paragraph whose text begins with ``Table.`` is treated as the caption of the
table that follows it, and is renumbered automatically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
ORDERED_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
DIRECTIVE_RE = re.compile(r"^:::\s*(\w[\w-]*)\s*(.*)$")
FENCE_RE = re.compile(r"^(```|~~~)\s*(\w*)\s*$")
IMAGE_RE = re.compile(r"^!\[[^\]]*\]\(([^)\s]+)\)$")
RULE_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")


@dataclass
class Block:
    kind: str
    text: str = ""
    items: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    aligns: list = field(default_factory=list)
    attrs: dict = field(default_factory=dict)


def _parse_front_matter(lines: list[str]) -> tuple[dict, int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict[str, str] = {}
    for idx in range(1, len(lines)):
        raw = lines[idx]
        if raw.strip() == "---":
            return meta, idx + 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip()] = value
    return meta, len(lines)


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    parts = re.split(r"(?<!\\)\|", stripped)
    return [p.strip().replace("\\|", "|") for p in parts]


def _parse_aligns(line: str, ncols: int) -> list[str]:
    aligns = []
    for cell in _split_row(line):
        cell = cell.strip()
        if cell.startswith(":") and cell.endswith(":"):
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    while len(aligns) < ncols:
        aligns.append("left")
    return aligns[:ncols]


def _parse_attrs(spec: str) -> dict:
    attrs: dict[str, str] = {}
    for match in re.finditer(r"(\w[\w-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)", spec):
        key, value = match.group(1), match.group(2)
        if value and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        attrs[key] = value
    leftover = re.sub(r"(\w[\w-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|\S+)", "", spec).strip()
    if leftover:
        attrs.setdefault("_rest", leftover)
    return attrs


def parse(text: str) -> tuple[dict, list[Block]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    meta, start = _parse_front_matter(lines)
    blocks: list[Block] = []

    i = start
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            blocks.append(Block(kind="para", text=" ".join(s.strip() for s in para).strip()))
            para = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # blank line -> paragraph boundary
        if not stripped:
            flush_para()
            i += 1
            continue

        # fenced code
        fence = FENCE_RE.match(stripped)
        if fence:
            flush_para()
            marker = fence.group(1)
            lang = fence.group(2)
            i += 1
            code: list[str] = []
            while i < len(lines) and lines[i].strip() != marker:
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(Block(kind="code", text="\n".join(code), attrs={"lang": lang}))
            continue

        # directives
        directive = DIRECTIVE_RE.match(stripped)
        if directive:
            flush_para()
            name = directive.group(1).lower()
            attrs = _parse_attrs(directive.group(2))
            if name == "pagebreak":
                blocks.append(Block(kind="pagebreak"))
                i += 1
                continue
            body: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            i += 1
            if name == "figure":
                # The image is written in standard Markdown so that GitHub shows
                # the diagram; the caption is whatever else is in the block.
                caption_lines = []
                for entry in (s.strip() for s in body if s.strip()):
                    image = IMAGE_RE.match(entry)
                    if image:
                        attrs["src"] = image.group(1).rsplit("/", 1)[-1]
                    else:
                        caption_lines.append(entry)
                blocks.append(Block(kind="figure", text=" ".join(caption_lines).strip(),
                                    attrs=attrs))
            elif name == "refs":
                entries = [s.strip() for s in body if s.strip()]
                blocks.append(Block(kind="refs", items=entries))
            else:
                blocks.append(Block(kind="callout", items=[s.strip() for s in body if s.strip()],
                                    attrs={"type": name}))
            continue

        # headings
        heading = HEADING_RE.match(line)
        if heading:
            flush_para()
            depth = len(heading.group(1))
            title = heading.group(2).strip()
            numbered = True
            if title.endswith("{-}"):
                numbered = False
                title = title[:-3].strip()
            kind = {1: "part", 2: "chapter", 3: "section", 4: "subsection"}[depth]
            blocks.append(Block(kind=kind, text=title, attrs={"numbered": numbered}))
            i += 1
            continue

        # horizontal rule
        if RULE_RE.match(stripped):
            flush_para()
            blocks.append(Block(kind="rule"))
            i += 1
            continue

        # tables
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1].strip()):
            flush_para()
            header = _split_row(lines[i])
            aligns = _parse_aligns(lines[i + 1], len(header))
            i += 2
            rows = [header]
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = _split_row(lines[i])
                while len(cells) < len(header):
                    cells.append("")
                rows.append(cells[: len(header)])
                i += 1
            blocks.append(Block(kind="table", rows=rows, aligns=aligns))
            continue

        # blockquote -> callout
        if stripped.startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            paras: list[str] = []
            buf: list[str] = []
            for q in quote:
                if q.strip():
                    buf.append(q.strip())
                elif buf:
                    paras.append(" ".join(buf))
                    buf = []
            if buf:
                paras.append(" ".join(buf))
            blocks.append(Block(kind="callout", items=paras, attrs={"type": "quote"}))
            continue

        # lists
        bullet = BULLET_RE.match(line)
        ordered = ORDERED_RE.match(line)
        if bullet or ordered:
            flush_para()
            items: list[tuple[int, str, str]] = []
            list_kind = "bullets" if bullet else "numbers"
            same_type = BULLET_RE if list_kind == "bullets" else ORDERED_RE
            while i < len(lines):
                cur = lines[i]
                if not cur.strip():
                    # A blank line may sit inside a list, but only if the next
                    # line continues the *same* kind of list; otherwise a
                    # following ordered list would be absorbed as bullets.
                    if i + 1 < len(lines) and same_type.match(lines[i + 1]):
                        i += 1
                        continue
                    break
                b = BULLET_RE.match(cur) if list_kind == "bullets" else None
                o = ORDERED_RE.match(cur) if list_kind == "numbers" else None
                if b:
                    level = 1 if len(b.group(1)) >= 2 else 0
                    items.append((level, "", b.group(2).strip()))
                    i += 1
                elif o:
                    level = 1 if len(o.group(1)) >= 2 else 0
                    items.append((level, o.group(2), o.group(3).strip()))
                    i += 1
                elif cur.startswith(("    ", "\t")) and items:
                    level, marker, body_text = items[-1]
                    items[-1] = (level, marker, body_text + " " + cur.strip())
                    i += 1
                else:
                    break
            blocks.append(Block(kind=list_kind, items=items))
            continue

        para.append(line)
        i += 1

    flush_para()
    return meta, blocks
