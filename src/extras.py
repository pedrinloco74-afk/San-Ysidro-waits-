"""Extra content pages: the jokes between the puzzles."""

from __future__ import annotations

from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics

PAGE_W, PAGE_H = 612, 792
MARGIN = 0.55 * 72
INK = HexColor("#1b1b1d")
SOFT = HexColor("#6b6b73")
LINE = HexColor("#c9c9cf")
ACCENT = HexColor("#a4243b")
BOX = HexColor("#8b8b93")


def _head(c, kicker, title):
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 10.5)
    c.drawString(MARGIN, PAGE_H - MARGIN - 10, kicker.upper())
    c.setFillColor(INK)
    c.setFont("Head-Bold", 26)
    c.drawString(MARGIN, PAGE_H - MARGIN - 44, title)
    c.setStrokeColor(INK)
    c.setLineWidth(1.8)
    c.line(MARGIN, PAGE_H - MARGIN - 56, PAGE_W - MARGIN, PAGE_H - MARGIN - 56)
    return PAGE_H - MARGIN - 84


def numbered_list(c, kicker, title, items, sub=None, start_size=11.5):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    y = _head(c, kicker, title)
    if sub:
        c.setFillColor(SOFT)
        c.setFont("Body", 11)
        for ln in sub:
            c.drawString(MARGIN, y, ln)
            y -= 16
        y -= 10
    for i, item in enumerate(items, 1):
        c.setFillColor(ACCENT)
        c.setFont("Head-Bold", start_size + 1.5)
        c.drawString(MARGIN, y, f"{i}.")
        c.setFillColor(INK)
        c.setFont("Body", start_size)
        x = MARGIN + 24
        from reportlab.pdfbase.pdfmetrics import stringWidth
        words, line = item.split(), ""
        for w in words:
            trial = f"{line} {w}".strip()
            if stringWidth(trial, "Body", start_size) <= PAGE_W - MARGIN - x:
                line = trial
            else:
                c.drawString(x, y, line)
                y -= 15
                line = w
        if line:
            c.drawString(x, y, line)
        y -= 24
    c.showPage()


def glossary(c, kicker, title, sub, terms):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    y = _head(c, kicker, title)
    c.setFillColor(SOFT)
    c.setFont("Body", 11)
    for ln in sub:
        c.drawString(MARGIN, y, ln)
        y -= 16
    y -= 14
    from reportlab.pdfbase.pdfmetrics import stringWidth
    for term, meaning in terms:
        c.setFillColor(ACCENT)
        c.setFont("Mono-Bold", 10.5)
        c.drawString(MARGIN, y, term)
        y -= 15
        c.setFillColor(INK)
        c.setFont("Body", 11)
        words, line = meaning.split(), ""
        for w in words:
            trial = f"{line} {w}".strip()
            if stringWidth(trial, "Body", 11) <= PAGE_W - 2 * MARGIN - 14:
                line = trial
            else:
                c.drawString(MARGIN + 14, y, line)
                y -= 15
                line = w
        if line:
            c.drawString(MARGIN + 14, y, line)
        y -= 24
    c.showPage()


def checklist(c, kicker, title, sub, items, columns=1, boxes_w=13):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    y = _head(c, kicker, title)
    c.setFillColor(SOFT)
    c.setFont("Body", 11)
    for ln in sub:
        c.drawString(MARGIN, y, ln)
        y -= 16
    y -= 16
    from reportlab.pdfbase.pdfmetrics import stringWidth
    for item in items:
        c.setStrokeColor(BOX)
        c.setLineWidth(0.9)
        c.rect(MARGIN, y - 1, boxes_w, boxes_w, stroke=1, fill=0)
        c.setFillColor(INK)
        c.setFont("Body", 11)
        words, line = item.split(), ""
        x = MARGIN + boxes_w + 12
        for w in words:
            trial = f"{line} {w}".strip()
            if stringWidth(trial, "Body", 11) <= PAGE_W - MARGIN - x:
                line = trial
            else:
                c.drawString(x, y + 2, line)
                y -= 16
                line = w
        if line:
            c.drawString(x, y + 2, line)
        y -= 27
    c.showPage()


def scorecard(c, kicker, title, sub, rows, footer):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    y = _head(c, kicker, title)
    c.setFillColor(SOFT)
    c.setFont("Body", 11)
    for ln in sub:
        c.drawString(MARGIN, y, ln)
        y -= 16
    y -= 18
    col_x = PAGE_W - MARGIN - 96
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    for label, hint in rows:
        c.setFillColor(INK)
        c.setFont("Body", 11)
        c.drawString(MARGIN, y, label)
        c.setFillColor(SOFT)
        c.setFont("Body", 9)
        c.drawString(MARGIN, y - 12, hint)
        c.setFillColor(SOFT)
        c.setFont("Mono", 11)
        c.drawCentredString(col_x + 46, y, "____ /  ____")
        c.setStrokeColor(LINE)
        c.line(MARGIN, y - 20, PAGE_W - MARGIN, y - 20)
        y -= 40
    y -= 6
    c.setFillColor(INK)
    c.setFont("Body-Bold", 12)
    c.drawString(MARGIN, y, footer)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.2)
    c.line(MARGIN + 4, y - 8, PAGE_W - MARGIN - 260, y - 8)
    c.showPage()


def notes_page(c, kicker, title, sub, lines=26):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    y = _head(c, kicker, title)
    c.setFillColor(SOFT)
    c.setFont("Body", 11)
    for ln in sub:
        c.drawString(MARGIN, y, ln)
        y -= 16
    y -= 16
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    for _ in range(lines):
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= 24
    c.showPage()


def part_page(c, kicker, title, blurb):
    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 11)
    c.drawString(MARGIN, PAGE_H - 3.2 * 72, kicker.upper())
    c.setFillColor(INK)
    c.setFont("Head-Bold", 40)
    c.drawString(MARGIN, PAGE_H - 3.85 * 72, title)
    c.setStrokeColor(INK)
    c.setLineWidth(2.2)
    c.line(MARGIN, PAGE_H - 4.05 * 72, PAGE_W - MARGIN, PAGE_H - 4.05 * 72)
    c.setFillColor(SOFT)
    c.setFont("Body", 12)
    y = PAGE_H - 4.45 * 72
    for ln in blurb:
        c.drawString(MARGIN, y, ln)
        y -= 19
    c.showPage()
