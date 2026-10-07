"""Parser for the book manuscript written in lightweight Markdown-ish syntax.

Supported syntax
----------------
# Heading              -> chapter / part / appendix heading
## Heading             -> part subtitle (immediately after a PART heading)
### Heading            -> section subhead
Paragraph text, **bold**, *italic*
- item                 -> bullet list
- [ ] item             -> checkbox list
1. item                -> numbered list
> quoted line          -> quote / script block
%TITLEPAGE             -> title page marker
:::kind TITLE ... :::  -> callout / table / scorecard / page-break directive
| label | text         -> table row (only inside :::table and :::score)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Block:
    kind: str
    text: str = ""
    items: list = field(default_factory=list)      # list of rich-text strings
    rows: list = field(default_factory=list)       # list of (label, text) rich-text pairs
    children: list = field(default_factory=list)   # nested Blocks (inside boxes)
    title: str = ""
    level: int = 0
    number: int | None = None
    meta: dict = field(default_factory=dict)


SINGLE_LINE_DIRECTIVES = {"pagebreak"}

DIRECTIVE_KINDS = {
    "truth", "keypoints", "note", "check", "watch", "legal", "donow",
    "table", "script", "score", "pagebreak", "contents", "shots",
}

PART_RE = re.compile(r"^PART\s+(ONE|TWO|THREE|FOUR|FIVE|SIX)\b", re.I)
CHAPTER_RE = re.compile(r"^Chapter\s+(\d+)\s*[:\u2014-]\s*(.+)$", re.I)
APPENDIX_RE = re.compile(r"^Appendix\s+([A-Z]\d?)\s*[:\u2014-]\s*(.+)$", re.I)


def _split_row(line: str) -> tuple[str, str]:
    """Split a `label | text` table row, keeping bold markers intact."""
    parts = line.split("|")
    if len(parts) < 2:
        return "", line.strip()
    return parts[0].strip(), "|".join(parts[1:]).strip()


def parse_manuscript(paths) -> list[Block]:
    blocks: list[Block] = []
    for path in paths:
        raw = open(path, encoding="utf-8").read()
        blocks.extend(_parse_text(raw))
    return blocks


def _parse_text(raw: str) -> list[Block]:
    lines = raw.split("\n")
    blocks: list[Block] = []
    i = 0
    n = len(lines)

    def blank(j: int) -> bool:
        return j >= n or not lines[j].strip()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # ---- directives -------------------------------------------------
        if stripped.startswith(":::"):
            header = stripped[3:].strip()
            if not header:            # closing fence of a block-level directive
                i += 1
                continue
            parts = header.split(" ", 1)
            kind = parts[0].lower()
            title = parts[1].strip() if len(parts) > 1 else ""
            body: list[str] = []
            i += 1
            if kind in SINGLE_LINE_DIRECTIVES:
                pass
            else:
                while i < n and lines[i].strip() != ":::":
                    body.append(lines[i])
                    i += 1
                i += 1  # consume closing fence
            blocks.append(_make_directive(kind, title, body))
            continue

        if stripped == "%TITLEPAGE":
            blocks.append(Block(kind="titlepage"))
            i += 1
            continue

        # ---- headings ---------------------------------------------------
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            i += 1
            if level == 1:
                if PART_RE.match(text):
                    subtitle = ""
                    if i < n and lines[i].strip().startswith("## "):
                        subtitle = lines[i].strip()[3:].strip()
                        i += 1
                    blocks.append(Block(kind="part", text=text, title=subtitle))
                elif re.match(r"^APPENDIX\s+[A-D]$", text, re.I) or APPENDIX_RE.match(text):
                    subtitle = ""
                    if i < n and lines[i].strip().startswith("## "):
                        subtitle = lines[i].strip()[3:].strip()
                        i += 1
                    blocks.append(Block(kind="appendix_banner", text=text, title=subtitle))
                elif text.upper() == "CONTENTS":
                    blocks.append(Block(kind="contents"))
                else:
                    m = CHAPTER_RE.match(text)
                    if m:
                        blocks.append(Block(kind="chapter", text=m.group(2).strip(),
                                            number=int(m.group(1)), level=1))
                    else:
                        m = APPENDIX_RE.match(text)
                        if m:
                            blocks.append(Block(kind="chapter", text=m.group(2).strip(),
                                                title=f"APPENDIX {m.group(1)}", level=1))
                        else:
                            blocks.append(Block(kind="chapter", text=text, level=1))
            elif level == 2:
                blocks.append(Block(kind="h2", text=text))
            else:
                blocks.append(Block(kind="h3", text=text))
            continue

        # ---- blockquote -------------------------------------------------
        if stripped.startswith(">"):
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(Block(kind="quote", text=" ".join(quote)))
            continue

        # ---- lists ------------------------------------------------------
        if re.match(r"^[-*]\s+\[ \]", stripped) or re.match(r"^[-*]\s+\S", stripped):
            items, checks = [], []
            while i < n and re.match(r"^[-*]\s+\S", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                checked = item.startswith("[ ]")
                if checked:
                    item = item[3:].strip()
                items.append(item)
                checks.append(checked)
                i += 1
            ordered = [k for k in blocks if k.kind == "list"]
            blocks.append(Block(kind="list", items=items,
                                meta={"variant": "check" if all(checks) else "bullet",
                                      "checks": checks,
                                      "ordered": len(ordered) and False}))
            continue

        if re.match(r"^\d+\.\s+\S", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+\S", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append(Block(kind="list", items=items, meta={"variant": "num"}))
            continue

        # ---- paragraphs -------------------------------------------------
        para: list[str] = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(
                ("#", ":::", "%TITLEPAGE", ">")) and not re.match(
                r"^([-*]\s+\S|\d+\.\s+\S)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        blocks.append(Block(kind="p", text=" ".join(para)))

    return blocks


def _make_directive(kind: str, title: str, body: list[str]) -> Block:
    if kind == "pagebreak":
        return Block(kind="pagebreak")
    if kind == "contents":
        return Block(kind="contents_body")

    children: list[Block] = []
    rows: list[tuple[str, str]] = []
    items: list[str] = []
    quote: list[str] = []
    variant = "bullet"

    j = 0
    while j < len(body):
        line = body[j].strip()
        if not line:
            j += 1
            continue
        if "|" in line and kind in ("table", "score"):
            while j < len(body) and body[j].strip():
                rows.append(_split_row(body[j].strip()))
                j += 1
            continue
        if re.match(r"^[-*]\s+\S", line):
            while j < len(body) and re.match(r"^[-*]\s+\S", body[j].strip()):
                item = re.sub(r"^[-*]\s+", "", body[j].strip())
                if item.startswith("[ ]"):
                    item = item[3:].strip()
                    variant = "check"
                items.append(item)
                j += 1
            continue
        if line.startswith(">"):
            while j < len(body) and body[j].strip().startswith(">"):
                quote.append(body[j].strip()[1:].strip())
                j += 1
            continue
        para = [line]
        j += 1
        while j < len(body) and body[j].strip() and not re.match(
                r"^([-*]\s+\S|>)", body[j].strip()) and not (
                "|" in body[j] and kind in ("table", "score")):
            para.append(body[j].strip())
            j += 1
        children.append(Block(kind="p", text=" ".join(para)))

    if kind == "score":
        return Block(kind="score", title=title, rows=rows, children=children)
    if kind == "table":
        return Block(kind="table", title=title, rows=rows, children=children)
    if kind == "script":
        return Block(kind="script", title=title, text=" ".join(quote), children=children)
    if items:
        children.append(Block(kind="list", items=items, meta={"variant": variant}))
    return Block(kind="box", text=kind, title=title, children=children)
