"""A small, purpose-built typesetting engine for the ebook.

It gives us full control over a two-column workbook layout: measured text
wrapping with inline bold/italic, callout boxes that can split across columns,
tables, scorecards, running heads, page numbers, clickable contents and PDF
bookmarks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

# ---------------------------------------------------------------- geometry --
PAGE_W, PAGE_H = LETTER                     # 612 x 792 pt
M_LEFT = M_RIGHT = 44
M_TOP = 38
M_BOTTOM = 36
GUTTER = 18
RUNNING_HEAD_GAP = 17
FOOTER_GAP = 17
COL_W = (PAGE_W - M_LEFT - M_RIGHT - GUTTER) / 2.0     # ~246pt (3.4in)
COL_TOP = PAGE_H - M_TOP - RUNNING_HEAD_GAP
COL_BOTTOM = M_BOTTOM + FOOTER_GAP
COL_H = COL_TOP - COL_BOTTOM


class C:
    INK = HexColor("#15191E")
    BODY = HexColor("#1F242B")
    MUTED = HexColor("#6E7681")
    FAINT = HexColor("#B6BCC4")
    ACCENT = HexColor("#BE3222")
    RED = HexColor("#BE3222")
    NAVY = HexColor("#132234")
    NAVY_SOFT = HexColor("#EDF1F6")
    GREY_BG = HexColor("#F4F5F7")
    GREY_BD = HexColor("#D8DCE1")
    CREAM = HexColor("#FDF6E7")
    CREAM_BD = HexColor("#E3CD9C")
    LEGAL = HexColor("#1C3E63")
    LEGAL_BG = HexColor("#F5F8FC")
    WATCH_BG = HexColor("#FDF2F0")
    WHITE = HexColor("#FFFFFF")
    GOLD = HexColor("#C79A3A")


FONT_FILES = {
    "Serif": "SourceSerif-Regular.ttf",
    "Serif-It": "SourceSerif-Italic.ttf",
    "Serif-Sb": "SourceSerif-SemiBold.ttf",
    "Serif-Bd": "SourceSerif-Bold.ttf",
    "Serif-BdIt": "SourceSerif-BoldItalic.ttf",
    "Sans": "Inter-Regular.ttf",
    "Sans-It": "Inter-Italic.ttf",
    "Sans-Md": "Inter-SemiBold.ttf",
    "Sans-Bd": "Inter-Bold.ttf",
    "Sans-Blk": "Inter-Black.ttf",
    "Display": "Anton-Regular.ttf",
}

STYLE_FONT = {
    ("body", "n"): "Serif", ("body", "b"): "Serif-Bd",
    ("body", "i"): "Serif-It", ("body", "bi"): "Serif-BdIt",
    ("sans", "n"): "Sans", ("sans", "b"): "Sans-Md",
    ("sans", "i"): "Sans-It", ("sans", "bi"): "Sans-Md",
}


def register_fonts(font_dir):
    import pathlib
    d = pathlib.Path(font_dir)
    for name, fname in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, str(d / fname)))
    pdfmetrics.registerFontFamily(
        "Serif", normal="Serif", bold="Serif-Bd", italic="Serif-It", boldItalic="Serif-BdIt")
    pdfmetrics.registerFontFamily(
        "Sans", normal="Sans", bold="Sans-Md", italic="Sans-It", boldItalic="Sans-Md")


# ------------------------------------------------------------------- config --
@dataclass
class Typo:
    body_size: float = 9.05
    body_lead: float = 11.3
    box_size: float = 8.5
    box_lead: float = 10.7
    list_lead: float = 11.0
    mini_size: float = 7.5
    cap_size: float = 8.2


T = Typo()


# --------------------------------------------------------------- rich text ---
_TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*)", re.S)


def plain(text: str) -> str:
    return text.replace("**", "").replace("*", "")


def runs(text: str) -> list[tuple[str, str]]:
    """Split inline markup into (text, style) runs where style in n/b/i/bi."""
    out: list[tuple[str, str]] = []
    for chunk in _TOKEN_RE.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            out.append((chunk[2:-2], "b"))
        elif chunk.startswith("*") and chunk.endswith("*") and len(chunk) > 2:
            out.append((chunk[1:-1], "i"))
        else:
            out.append((chunk, "n"))
    # merge italic+bold neighbours that came from ***x***
    merged: list[tuple[str, str]] = []
    for txt, st in out:
        if merged and merged[-1][1] in ("i", "bi") and st in ("b", "bi") and not txt.strip():
            pass
        if merged and merged[-1][1] == "i" and st == "b" and False:
            pass
        merged.append((txt, st))
    return merged


@dataclass
class Line:
    words: list[tuple[str, str]]
    natural: float
    indent: float
    last: bool = False


def _word_tokens(text: str, base: str):
    toks: list[tuple[str, str]] = []
    for chunk, st in runs(text):
        for k, word in enumerate(chunk.split(" ")):
            if word == "":
                continue
            toks.append((word, st))
    return toks


def wrap_text(text: str, font_key: str, size: float, width: float,
              indent_first: float = 0.0, indent_rest: float = 0.0) -> list[Line]:
    toks = _word_tokens(text, font_key)
    lines: list[Line] = []
    cur: list[tuple[str, str]] = []
    curw = 0.0
    indent = indent_first
    avail = width - indent_first
    for word, st in toks:
        fname = STYLE_FONT[(font_key, st)]
        ww = pdfmetrics.stringWidth(word, fname, size)
        sw = pdfmetrics.stringWidth(" ", fname, size)
        add = ww if not cur else sw + ww
        if cur and curw + add > avail + 0.01:
            lines.append(Line(cur, curw, indent))
            cur = [(word, st)]
            curw = ww
            indent = indent_rest
            avail = width - indent_rest
        else:
            cur.append((word, st))
            curw += add
    if cur:
        lines.append(Line(cur, curw, indent))
    if lines:
        lines[-1].last = True
    return lines


def draw_line(c: rl_canvas.Canvas, line: Line, x: float, y: float, width: float,
              font_key: str, size: float, color: Color, align: str = "left",
              justify: bool = False) -> None:
    avail = width - line.indent
    extra = 0.0
    if justify and not line.last and len(line.words) > 1:
        extra = max(0.0, (avail - line.natural) / (len(line.words) - 1))
    elif align == "center":
        pass
    cx = x + line.indent
    if align == "center":
        cx = x + (width - line.natural) / 2.0
    c.setFillColor(color)
    for i, (word, st) in enumerate(line.words):
        fname = STYLE_FONT[(font_key, st)]
        c.setFont(fname, size)
        c.drawString(cx, y, word)
        cx += pdfmetrics.stringWidth(word, fname, size)
        if i < len(line.words) - 1:
            sw = pdfmetrics.stringWidth(" ", fname, size)
            cx += sw + extra


def draw_tracked(c, text: str, font: str, size: float, x: float, y: float,
                 tracking: float = 0.9) -> float:
    c.setFont(font, size)
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + tracking
    return x


def tracked_width(text: str, font: str, size: float, tracking: float = 0.9) -> float:
    return sum(pdfmetrics.stringWidth(ch, font, size) + tracking for ch in text) - tracking


def wrap_tracked(text: str, font: str, size: float, width: float, tracking: float = 0.9):
    """Wrap uppercase tracked display text into lines."""
    words = text.split()
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if cur and tracked_width(trial, font, size, tracking) > width:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


# ------------------------------------------------------------------- flows ---
class Flow:
    space_before = 0.0
    space_after = 0.0
    keep_next = False

    def wrap(self, width: float) -> float:
        raise NotImplementedError

    def draw(self, c, x, top, width):
        raise NotImplementedError

    def split(self, max_h: float):
        return None


class Paragraph(Flow):
    def __init__(self, text, size=None, lead=None, font_key="body", align="justify",
                 space_before=0.0, space_after=4.2, color=None, indent_first=0.0,
                 indent_rest=0.0, justify=True, bold_all=False):
        self.text = text
        self.size = size or T.body_size
        self.lead = lead or T.body_lead
        self.font_key = font_key
        self.align = align
        self.justify = justify
        self.space_before = space_before
        self.space_after = space_after
        self.color = color or C.BODY
        self.indent_first = indent_first
        self.indent_rest = indent_rest
        self.lines: list[Line] = []
        self.bold_all = bold_all

    def wrap(self, width):
        text = f"**{self.text}**" if self.bold_all else self.text
        self.lines = wrap_text(text, self.font_key, self.size, width,
                               self.indent_first, self.indent_rest)
        return len(self.lines) * self.lead

    @property
    def h(self):
        return len(self.lines) * self.lead

    def draw(self, c, x, top, width):
        y = top - self.size
        for ln in self.lines:
            draw_line(c, ln, x, y, width, self.font_key, self.size, self.color,
                      self.align, self.justify)
            y -= self.lead
        return top - self.h

    def split(self, max_h):
        keep = int(max_h // self.lead)
        if keep >= 2 and len(self.lines) - keep >= 2:
            head = Paragraph(self.text, self.size, self.lead, self.font_key, self.align,
                             0, self.space_after, self.color, 0, self.indent_rest,
                             self.justify, self.bold_all)
            tail = Paragraph(self.text, self.size, self.lead, self.font_key, self.align,
                             self.space_before, self.space_after, self.color, 0,
                             self.indent_rest, self.justify, self.bold_all)
            body = self.lines
            head.lines = [Line(l.words, l.natural, l.indent) for l in body[:keep]]
            head.lines[0].indent = self.indent_first
            head.lines[-1].last = True
            tail.lines = [Line(l.words, l.natural, l.indent) for l in body[keep:]]
            tail.lines[-1].last = True
            return head, tail
        return None


class Heading(Flow):
    def __init__(self, text, kicker="", size=21, space_before=26, space_after=9,
                 color=None, accent=True, tracked_kicker=1.0):
        self.text = text
        self.kicker = kicker
        self.size = size
        self.space_before = space_before
        self.space_after = space_after
        self.color = color or C.INK
        self.accent = accent
        self.tracked_kicker = tracked_kicker
        self.lines: list[str] = []
        self.lead = size * 1.06
        self.keep_next = True

    def wrap(self, width):
        self.width = width
        self.lines = wrap_tracked(self.text.upper(), "Display", self.size, width - 2)
        h = 0.0
        if self.kicker:
            h += self.size * 0.62
        h += len(self.lines) * self.lead
        h += 9
        self._h = h
        return h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        y = top
        if self.kicker:
            c.setFillColor(C.ACCENT)
            draw_tracked(c, self.kicker.upper(), "Sans-Bd", 7.8, x, y - 8, 1.5)
            y -= self.size * 0.62
        c.setFillColor(self.color)
        for ln in self.lines:
            draw_tracked(c, ln, "Display", self.size, x, y - self.size * 0.92, 0.6)
            y -= self.lead
        if self.accent:
            c.setFillColor(C.ACCENT)
            c.rect(x, y - 8, 34, 2.1, stroke=0, fill=1)
        return top - self._h


class SubHead(Flow):
    def __init__(self, text, size=11.6, space_before=12, space_after=4.6, kicker=False):
        self.text = text
        self.size = size
        self.space_before = space_before
        self.space_after = space_after
        self.lead = size * 1.18
        self.kicker = kicker
        self.keep_next = True

    def wrap(self, width):
        self.lines = wrap_text(self.text, "sans", self.size, width)
        self._h = len(self.lines) * self.lead
        return self._h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        y = top - self.size
        for ln in self.lines:
            draw_line(c, ln, x, y, width, "sans", self.size, C.INK, "left", False)
            y -= self.lead
        return top - self._h


class Bullets(Flow):
    def __init__(self, items, variant="bullet", size=None, lead=None, space_before=2,
                 space_after=4.5, indent=13.5, color=None, boxed=False):
        self.items = items
        self.variant = variant
        self.size = size or T.body_size
        self.lead = lead or T.list_lead
        self.space_before = space_before
        self.space_after = space_after
        self.indent = indent
        self.color = color or C.BODY
        self.boxed = boxed
        self.marker_color = None
        self.wrapped: list[list[Line]] = []

    def wrap(self, width):
        self.width = width
        self.wrapped = []
        total = 0.0
        for item in self.items:
            w = width - self.indent
            lines = wrap_text(item, "body", self.size, w, 0, 0)
            self.wrapped.append(lines)
            total += len(lines) * self.lead + 2.6
        self._h = total
        return total

    @property
    def h(self):
        return self._h

    def _marker(self, c, x, y, i):
        accent = self.marker_color or C.ACCENT
        if self.variant == "check":
            c.setStrokeColor(HexColor("#B9C0C8"))
            c.setLineWidth(0.8)
            c.setFillColor(C.WHITE)
            c.rect(x + 0.6, y + 1.2, 7.4, 7.4, stroke=1, fill=1)
        elif self.variant == "num":
            c.setFillColor(accent)
            c.setFont("Sans-Bd", self.size - 0.8)
            c.drawString(x, y, f"{i}.")
        else:
            c.setFillColor(accent)
            c.rect(x + 1.2, y + 2.6, 3.1, 3.1, stroke=0, fill=1)

    def draw(self, c, x, top, width):
        y = top
        for i, lines in enumerate(self.wrapped, start=1):
            for k, ln in enumerate(lines):
                if k == 0:
                    self._marker(c, x, y - self.size, i)
                draw_line(c, ln, x + self.indent, y - self.size, width - self.indent,
                          "body", self.size, self.color, "left",
                          justify=not self.boxed)
                y -= self.lead
            y -= 2.6
        return top - self._h

    def split(self, max_h):
        keep, used = 0, 0.0
        for lines in self.wrapped:
            need = len(lines) * self.lead + 2.6
            if used + need > max_h:
                break
            used += need
            keep += 1
        if keep >= 1 and len(self.items) - keep >= 1:
            a = Bullets(self.items[:keep], self.variant, self.size, self.lead, 0,
                        self.space_after, self.indent, self.color, self.boxed)
            b = Bullets(self.items[keep:], self.variant, self.size, self.lead, 0,
                        self.space_after, self.indent, self.color, self.boxed)
            b.space_before = self.space_before
            return a, b
        return None


class HRule(Flow):
    def __init__(self, space_before=6, space_after=6, color=None, thickness=0.6):
        self.space_before = space_before
        self.space_after = space_after
        self.color = color or C.FAINT
        self.thickness = thickness

    def wrap(self, width):
        self._h = 0.0
        return 0.0

    @property
    def h(self):
        return 0.0

    def draw(self, c, x, top, width):
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        c.line(x, top, x + width, top)
        return top


class Spacer(Flow):
    def __init__(self, h=6):
        self._h = h
        self.space_before = 0
        self.space_after = 0

    def wrap(self, width):
        return self._h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        return top - self._h


class Table(Flow):
    KEY_LABEL = ("table", "score")

    def __init__(self, rows, kind="table", title="", size=None, lead=None,
                 space_before=6, space_after=7, label_w=0.36):
        self.rows = rows
        self.kind = kind
        self.title = title
        self.size = size or T.mini_size
        self.lead = lead or self.size * 1.32
        self.space_before = space_before
        self.space_after = space_after
        self.label_w = label_w
        self.wrapped = []
        self.keep_next = False

    def wrap(self, width):
        self.width = width
        base = self.size
        pad = 4.4
        self.wrapped = []
        total = 0.0
        for label, text in self.rows:
            y = 0.0
            lab_lines = []
            txt_lines = []
            lw = 0.0
            if self.kind == "score":
                lab_lines = wrap_tracked(label, "Display", base + 1.6, width - 2)
                txt_lines = wrap_text(text, "body", base + 0.3, width - 34)
                h = max(len(txt_lines) * self.lead + 4.4,
                        len(lab_lines) * (base + 3) + 3.4)
            else:
                lw = min(max(width * self.label_w, 46), width * 0.42)
                txt_lines = wrap_text(text, "body", base + 0.2,
                                      width - lw - 4 * pad if label else width - 2 * pad)
                lab_lines = (wrap_text(label, "sans", base, max(lw - 2 * pad, 10), 0, 0)
                             if label else [])
                h = max(len(txt_lines) * self.lead,
                        len(lab_lines) * self.lead) + 4.0
            h = max(h, 14.5)
            self.wrapped.append(((label, text), lab_lines, txt_lines, h, lw if label else 0))
            total += h
        if self.title:
            total += 15
        self._pad = pad
        self._h = total + 6
        return self._h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        y = top
        pad = self._pad
        if self.title:
            c.setFillColor(C.ACCENT)
            draw_tracked(c, self.title.upper(), "Sans-Bd", 7.6, x, y - 8.6, 1.2)
            y -= 15
            c.setStrokeColor(C.ACCENT)
            c.setLineWidth(1.4)
            c.line(x, y + 3.2, x + width, y + 3.2)
        for i, ((label, text), lab_lines, txt_lines, h, lw) in enumerate(self.wrapped):
            y -= h
            if i % 2 == 1:
                c.setFillColor(HexColor("#F6F7F9"))
                c.rect(x, y, width, h, stroke=0, fill=1)
            if self.kind == "score":
                c.setFillColor(C.ACCENT)
                c.setFont("Display", self.size + 2.4)
                c.drawString(x + 1, y + h - self.size - 3.4, label)
                c.setStrokeColor(HexColor("#C9CFD6"))
                c.setLineWidth(0.7)
                c.rect(x + width - 12.5, y + h / 2 - 4.6, 9, 9, stroke=1, fill=0)
                ty = y + h - 4.4
                for ln in txt_lines:
                    draw_line(c, ln, x + 19, ty - self.size, width - 33,
                              "body", self.size + 0.3, C.BODY, "left", False)
                    ty -= self.lead
            else:
                ly = y + h - 4.4
                for ln in lab_lines:
                    draw_line(c, ln, x + 1, ly - self.size, lw, "sans", self.size,
                              C.INK, "left", False)
                    ly -= self.lead
                ty = y + h - 4.4
                tx = x + (lw + pad * 0.8 if lw else pad)
                tw = width - (lw + pad * 0.8 if lw else pad) - pad
                for ln in txt_lines:
                    draw_line(c, ln, tx, ty - self.size, tw, "body", self.size + 0.2,
                              C.BODY, "left", False)
                    ty -= self.lead
            c.setStrokeColor(HexColor("#E4E7EB"))
            c.setLineWidth(0.4)
            c.line(x, y, x + width, y)
        return top - self._h

    def split(self, max_h):
        if not self.wrapped:
            return None
        used, keep = 0.0, 0
        for row in self.wrapped:
            if used + row[3] > max_h - (14 if self.title else 4):
                break
            used += row[3]
            keep += 1
        if keep >= 1 and len(self.wrapped) - keep >= 1:
            a = Table(self.rows[:keep], self.kind, self.title, self.size, self.lead,
                      0, self.space_after, self.label_w)
            b = Table(self.rows[keep:], self.kind,
                      (self.title + "  CONT'D" if self.title else ""), self.size,
                      self.lead, 0, self.space_after, self.label_w)
            b.space_before = self.space_before
            return a, b
        return None


class Box(Flow):
    """A callout with a background, optional title and nested flows."""
    def __init__(self, children, title="", style="keypoints", space_before=7,
                 space_after=8, size=None, lead=None, font_key="body", icon=None):
        self.children = [c for c in children if c is not None]
        self.title = title
        self.style = style
        self.size = size or T.box_size
        self.lead = lead or T.box_lead
        self.font_key = font_key
        self.space_before = space_before
        self.space_after = space_after
        self.icon = icon
        self.pad = 9.0
        self.hidden_title = False

    # -- geometry ---------------------------------------------------------
    def _inner_width(self, width):
        side = 2.5 if self.style in ("watch", "legal", "script") else 1.0
        return width - 2 * self.pad - side

    def wrap(self, width):
        self.width = width
        inner = self._inner_width(width)
        self.title_h = 0.0
        if self.title and not self.hidden_title:
            self.title_h = self.size * 1.5 + 3
        self.heights = []
        total = self.title_h
        for ch in self.children:
            h = ch.wrap(inner)
            self.heights.append(h)
            total += h + 3.0
        self._h = total + 2 * self.pad - (2 if self.children else 0) + 4
        return self._h

    @property
    def h(self):
        return self._h

    def _colors(self):
        return {
            "truth": (C.NAVY, C.NAVY, C.WHITE),
            "keypoints": (C.GREY_BG, C.GREY_BD, C.INK),
            "check": (C.GREY_BG, C.GREY_BD, C.INK),
            "note": (C.WHITE, C.INK, C.INK),
            "watch": (C.WATCH_BG, C.ACCENT, C.INK),
            "legal": (C.LEGAL_BG, C.LEGAL, C.INK),
            "donow": (C.CREAM, C.CREAM_BD, C.INK),
            "script": (HexColor("#F7F8FA"), C.NAVY, C.INK),
            "shots": (C.NAVY_SOFT, C.NAVY, C.INK),
        }[self.style]

    def _title_color(self):
        if self.style == "truth":
            return C.GOLD
        if self.style == "legal":
            return C.LEGAL
        if self.style == "script":
            return C.NAVY
        return C.ACCENT

    def draw(self, c, x, top, width):
        bg, bd, fg = self._colors()
        h = self._h
        c.setFillColor(bg)
        c.setStrokeColor(bd)
        if self.style == "truth":
            c.rect(x, top - h, width, h, stroke=0, fill=1)
            c.setFillColor(C.GOLD)
            c.rect(x, top - 3.4, width, 3.4, stroke=0, fill=1)
        elif self.style == "legal":
            c.setLineWidth(0.9)
            c.rect(x, top - h, width, h, stroke=1, fill=1)
            c.setFillColor(C.LEGAL)
            c.rect(x, top - h, 3.0, h, stroke=0, fill=1)
        elif self.style == "watch":
            c.rect(x, top - h, width, h, stroke=0, fill=1)
            c.setFillColor(C.ACCENT)
            c.rect(x, top - h, 3.4, h, stroke=0, fill=1)
        elif self.style == "script":
            c.rect(x, top - h, width, h, stroke=0, fill=1)
            c.setFillColor(C.NAVY)
            c.rect(x, top - h, 2.6, h, stroke=0, fill=1)
        elif self.style == "note":
            c.setLineWidth(0.7)
            c.setDash(2, 2)
            c.rect(x, top - h, width, h, stroke=1, fill=1)
            c.setDash()
        else:
            c.rect(x, top - h, width, h, stroke=0, fill=1)

        y = top - self.pad
        if self.title and not self.hidden_title:
            c.setFillColor(self._title_color())
            tx = x + self.pad
            if self.icon:
                c.setFont("Sans-Bd", 8.4)
                c.drawString(tx, y - 8.4, self.icon)
                tx += 12
            lines = wrap_tracked(self.title.upper(), "Sans-Bd", 8.0,
                                 width - self.pad - (tx - x) - 4, 1.1)
            for ln in lines:
                draw_tracked(c, ln, "Sans-Bd", 8.0, tx, y - 8.4, 1.1)
                y -= 10.4
            y -= 2.2
        else:
            y -= 1
        inner_x = x + self.pad + (1.6 if self.style in ("legal", "watch") else 0)
        inner_w = self._inner_width(width)
        for ch, hh in zip(self.children, self.heights):
            ch.draw(c, inner_x, y, inner_w)
            y -= hh + 3.0
        return top - self._h

    def split(self, max_h):
        if max_h < 66:
            return None
        avail = max_h - self.pad - self.title_h
        used, keep = 0.0, 0
        for hh in self.heights:
            if used + hh + 3 > avail:
                break
            used += hh + 3
            keep += 1
        if keep >= 1 and len(self.children) - keep >= 1:
            a = Box(self.children[:keep], self.title, self.style, 0, self.space_after,
                    self.size, self.lead, self.font_key, self.icon)
            b = Box(self.children[keep:],
                    (self.title + "  CONT'D") if self.title else "",
                    self.style, 0, self.space_after, self.size, self.lead,
                    self.font_key, None)
            b.hidden_title = self.hidden_title
            b.space_before = self.space_before
            return a, b
        # try splitting the next child so the box can keep filling this column
        if keep >= 1 and keep < len(self.children) and \
                self.children[keep].split(avail - used - 3):
            head_child, tail_child = self.children[keep].split(avail - used - 3)
            a = Box(self.children[:keep] + [head_child], self.title, self.style, 0,
                    self.space_after, self.size, self.lead, self.font_key, self.icon)
            b = Box([tail_child] + self.children[keep + 1:],
                    (self.title + " (continued)") if self.title else "", self.style, 0,
                    self.space_after, self.size, self.lead, self.font_key, None)
            b.hidden_title = self.hidden_title
            b.space_before = self.space_before
            return a, b
        return None


class PartBanner(Flow):
    def __init__(self, label, title, lines, space_before=24, space_after=12):
        self.label = label
        self.title = title
        self.lines = lines
        self.space_before = space_before
        self.space_after = space_after
        self.keep_next = True

    def wrap(self, width):
        self.width = width
        self.label_lines = wrap_tracked(self.label.upper(), "Display", 26, width - 20)
        self.title_lines = wrap_text(self.title.upper(), "sans", 11.6, width - 24)
        h = 16 + len(self.label_lines) * 27 + 6 + len(self.title_lines) * 15 + 10
        if self.lines:
            h += 8 + len(self.lines) * 12.4
        self._h = h
        return h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        h = self._h
        c.setFillColor(C.NAVY)
        c.rect(x, top - h, width, h, stroke=0, fill=1)
        c.setFillColor(C.GOLD)
        c.rect(x, top - h, width, 2.6, stroke=0, fill=1)
        y = top - 12
        c.setFillColor(C.WHITE)
        for ln in self.label_lines:
            draw_tracked(c, ln, "Display", 26, x + 12, y - 22, 0.8)
            y -= 27
        y -= 2
        c.setFillColor(C.GOLD)
        for ln in self.title_lines:
            draw_line(c, ln, x + 12, y - 11, width - 24, "sans", 11.6, C.GOLD,
                      "left", False)
            y -= 15
        if self.lines:
            y -= 4
            for ln in self.lines:
                c.setFillColor(HexColor("#9FB0C2"))
                c.circle(x + 14, y - 4.2, 1.7, stroke=0, fill=1)
                draw_line(c, Line([(w, "n") for w in ln.split()],
                                  pdfmetrics.stringWidth(ln, "Sans", 8.6), 0),
                          x + 22, y - 8.4, width - 34, "sans", 8.6,
                          HexColor("#DCE4EC"), "left", False)
                y -= 12.4
        return top - h


class AppendixBanner(Flow):
    def __init__(self, label, title, space_before=26, space_after=10):
        self.label = label
        self.title = title
        self.space_before = space_before
        self.space_after = space_after
        self.keep_next = True

    def wrap(self, width):
        self.width = width
        self.label_lines = wrap_tracked(self.label.upper(), "Display", 22, width - 6)
        self.title_lines = wrap_text(self.title.upper(), "sans", 10.6, width - 6)
        self._h = len(self.label_lines) * 23 + len(self.title_lines) * 14 + 22
        return self._h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        y = top
        c.setFillColor(C.ACCENT)
        c.rect(x, y - 3, width, 3, stroke=0, fill=1)
        y -= 15
        c.setFillColor(C.INK)
        for ln in self.label_lines:
            draw_tracked(c, ln, "Display", 22, x, y - 18, 0.6)
            y -= 23
        c.setFillColor(C.MUTED)
        for ln in self.title_lines:
            draw_line(c, ln, x, y - 11, width, "sans", 10.6, C.MUTED, "left", False)
            y -= 14
        return top - self._h


class PageBreak(Flow):
    def __init__(self):
        self.space_before = 0
        self.space_after = 0

    def wrap(self, width):
        return 0.0

    @property
    def h(self):
        return 0.0

    def draw(self, c, x, top, width):
        return top


class FullPage(Flow):
    """A flow that claims an entire page and draws itself."""
    def __init__(self, renderer, key=None):
        self.renderer = renderer
        self.key = key
        self.space_before = 0
        self.space_after = 0

    def wrap(self, width):
        self._h = COL_H
        return self._h

    @property
    def h(self):
        return self._h

    def draw(self, c, x, top, width):
        self.renderer(c)
        return top - self._h


# -------------------------------------------------------------- pagination ---
@dataclass
class Placement:
    flow: Flow
    x: float
    top: float
    width: float


@dataclass
class Page:
    index: int
    placements: list = field(default_factory=list)
    running_head: str = ""
    full: bool = False
    kind: str = "content"


class Paginator:
    """Lays flows into a two-column grid, splitting what needs splitting."""

    def __init__(self, log=None):
        self.pages: list[Page] = []
        self.anchors: dict[str, tuple[int, float]] = {}
        self.sections: list[tuple[str, str, int]] = []   # (label, kind, page index)
        self.warnings: list[str] = []
        self.log = log or (lambda *a: None)
        self.current_running = ""
        self.entry: dict | None = None
        self._col = 0
        self._rem_val = COL_H
        self._last_after = 0.0

    # -- page helpers -----------------------------------------------------
    def _new_page(self):
        pg = Page(len(self.pages))
        pg.running_head = self.current_running
        self.pages.append(pg)
        return pg

    def paginate(self, flows):
        self._new_page()
        i = 0
        while i < len(flows):
            flow = flows[i]
            nxt = flows[i + 1] if i + 1 < len(flows) else None
            if isinstance(flow, PageBreak):
                self._advance(break_page=True)
                i += 1
                continue
            if isinstance(flow, FullPage):
                self._place_full(flow)
                i += 1
                continue

            entry = getattr(flow, "entry", None)
            if entry:
                self.entry = entry
            running = getattr(flow, "running", None)
            if running:
                self.current_running = running
                if self.pages[-1].placements:
                    pass
            anchor = getattr(flow, "anchor", None)
            if anchor:
                self.anchors[anchor] = (len(self.pages) - 1, self._cursor_y(flow))

            h = flow.wrap(COL_W)
            gap = self._gap(flow)
            guard = 0
            while gap + h > self._rem() + 0.05 and guard < 40:
                guard += 1
                parts = flow.split(self._rem() - gap)
                if parts:
                    head, tail = parts
                    head.wrap(COL_W)
                    if head.h > 0.5 and head.h <= self._rem() - gap + 0.05:
                        self._place(head, gap)
                        flow = tail
                        h = flow.wrap(COL_W)
                        gap = 0.0
                        self._advance()
                        continue
                if h > COL_H - 4 and not parts:
                    self.warnings.append(
                        f"oversized flow ({h:.0f}pt) placed overflowing: "
                        f"{flow.__class__.__name__} {getattr(flow, 'text', '')[:40]!r}")
                    self._place(flow, gap)
                    self._advance()
                    break
                self._advance()
                gap = 0.0
            # keep-with-next: don't strand a heading at the bottom
            if flow.keep_next and nxt is not None and not isinstance(nxt, (PageBreak, FullPage)):
                nxt_h = nxt.wrap(COL_W)
                need = min(nxt_h, 2 * T.body_lead + 4.5)
                if gap + h + need > self._rem() + 0.05:
                    self._advance()
                    gap = 0.0
            self._place(flow, gap)
            self._remember_section(flow)
            i += 1
        return self.pages

    # -- internals --------------------------------------------------------
    def _cur(self):
        return self.pages[-1]

    def _rem(self):
        return self._rem_val

    def _gap(self, flow):
        return max(self._last_after, flow.space_before) if self._cur().placements else 0.0

    def _place(self, flow, gap):
        pg = self._cur()
        y = COL_TOP - (COL_H - self._rem_val) - gap
        pg.placements.append(Placement(flow, self._col_x(), y, COL_W))
        self._rem_val -= gap + flow.h
        self._last_after = flow.space_after
        if flow.keep_next is False:
            pass

    def _place_full(self, flow):
        if self._cur().placements:
            self._advance(break_page=True)
        flow.wrap(PAGE_W - M_LEFT - M_RIGHT)
        pg = self._cur()
        pg.full = True
        pg.placements.append(Placement(flow, M_LEFT, COL_TOP, PAGE_W - M_LEFT - M_RIGHT))
        if getattr(flow, "entry", None):
            self.entry = flow.entry
        if getattr(flow, "running", None):
            pg.running_head = flow.running
            self.current_running = flow.running
        if getattr(flow, "anchor", None):
            self.anchors[flow.anchor] = (pg.index, COL_TOP)
        self._advance(break_page=True)

    def _col_x(self):
        return M_LEFT + self._col * (COL_W + GUTTER)

    def _advance(self, break_page=False):
        if break_page and not self._cur().placements and self._col == 0:
            # already at the top of a fresh page — nothing to do
            return
        if self._cur().full or break_page:
            self._new_page()
            self._col = 0
            self._rem_val = COL_H
            self._last_after = 0.0
            return
        if self._col == 0:
            self._col = 1
            self._rem_val = COL_H
            self._last_after = 0.0
            return
        self._new_page()
        self._col = 0
        self._rem_val = COL_H
        self._last_after = 0.0

    def _cursor_y(self, flow):
        return COL_TOP - (COL_H - self._rem_val)

    def _remember_section(self, flow):
        entry = getattr(flow, "entry", None)
        if entry:
            kind, label = entry
            self.sections.append((label, kind, self._cur().index))

