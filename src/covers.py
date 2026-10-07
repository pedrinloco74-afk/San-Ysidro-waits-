"""Cover artwork: the Kindle ebook cover and the KDP paperback wrap."""

from __future__ import annotations

import os

from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

ACCENT = HexColor("#a4243b")
DARK = HexColor("#141418")
DARKER = HexColor("#0d0d10")
LIGHT = HexColor("#e8e8ec")
SOFT = HexColor("#8f8f98")


def _register():
    from render import register_fonts
    register_fonts()


def _title_block(c, cx, top_y, scale=1.0):
    """The wordmark: THE / EX-FILES / subtitle."""
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 18 * scale)
    c.drawCentredString(cx, top_y, "THE")
    c.setFillColor(white)
    c.setFont("Head-Bold", 92 * scale)
    c.drawCentredString(cx, top_y - 92 * scale, "EX-FILES")
    c.setFillColor(ACCENT)
    c.rect(cx - 190 * scale, top_y - 112 * scale, 380 * scale, 6 * scale,
           stroke=0, fill=1)
    c.setFillColor(LIGHT)
    c.setFont("Body", 20 * scale)
    c.drawCentredString(cx, top_y - 142 * scale,
                        "A Crossword Book for Men Who Are")
    c.drawCentredString(cx, top_y - 166 * scale, "Absolutely Fine")


def _mini_grid(c, x0, y0, cell, pattern):
    for r, row in enumerate(pattern):
        for col, ch in enumerate(row):
            x, y = x0 + col * cell, y0 - r * cell
            if ch == "#":
                c.setFillColor(ACCENT)
                c.rect(x, y, cell, cell, stroke=0, fill=1)
            elif ch == ".":
                c.setStrokeColor(SOFT)
                c.setLineWidth(0.7)
                c.rect(x, y, cell, cell, stroke=1, fill=0)


GRID_A = ["#..#..#", ".#.#.#.", "#..#..#", ".#.#.#.", "#..#..#", ".#.#.#.", "#..#..#"]
GRID_B = ["#.#.#", "..#..", "#.#.#", "..#..", "#.#.#"]


def ebook_cover(path, w_pt=432, h_pt=691.2):
    """1600 x 2560 px cover (the KDP ebook standard ratio)."""
    _register()
    c = canvas.Canvas(path, pagesize=(w_pt, h_pt), initialFontName="Body")
    c.setTitle("The Ex-Files - cover")

    c.setFillColor(DARK)
    c.rect(0, 0, w_pt, h_pt, stroke=0, fill=1)
    _title_block(c, w_pt / 2, h_pt - 92, scale=0.72)

    y = h_pt - 252
    for text, tone, font, size in [
        ("Fifteen puzzles. One ex-girlfriend. Zero closure.", "accent", "Body-Bold", 13.5),
        ("", "soft", "Body", 11),
        ("Themes include: the group chat, the dog she kept,", "light", "Body", 12.5),
        ("the playlist you must delete, and the speech you", "light", "Body", 12.5),
        ("gave at her brother's wedding.", "light", "Body", 12.5),
        ("", "soft", "Body", 11),
        ("Adult humour. Real crosswords. Suspiciously specific.", "accent", "Body-Bold", 13),
    ]:
        col = {"accent": ACCENT, "light": LIGHT, "soft": SOFT}[tone]
        c.setFillColor(col)
        c.setFont(font, size)
        c.drawCentredString(w_pt / 2, y, text)
        y -= 23

    cell = 16
    _mini_grid(c, w_pt / 2 - 2.5 * cell, 205, cell, GRID_B)

    c.setFillColor(SOFT)
    c.setFont("Head", 9.5)
    c.drawCentredString(w_pt / 2, 104, "15 PUZZLES  ·  FULL ANSWER KEY")
    c.drawCentredString(w_pt / 2, 88, "LARGE 8.5 x 11 PAGES  ·  FOR ADULTS")
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 10)
    c.drawCentredString(w_pt / 2, 62, "18+  ADULT HUMOUR")
    c.save()


def wrap_cover(path, pages=29, paper="white"):
    """Full paperback wrap: back + spine + front, with 0.125in bleed."""
    _register()
    bleed = 0.125 * 72
    trim_w, trim_h = 8.5 * 72, 11 * 72
    per_page = 0.002252 * 72 if paper == "white" else 0.0025 * 72
    spine = max(0.03 * 72, pages * per_page)
    total_w = bleed * 2 + trim_w * 2 + spine
    total_h = bleed * 2 + trim_h

    c = canvas.Canvas(path, pagesize=(total_w, total_h), initialFontName="Body")
    c.setTitle("The Ex-Files - paperback cover wrap")

    c.setFillColor(DARK)
    c.rect(0, 0, total_w, total_h, stroke=0, fill=1)

    # ---- front cover (right panel) ----
    fx = bleed + trim_w + spine
    c.saveState()
    c.translate(fx, bleed)
    c.setFillColor(DARK)
    c.rect(0, 0, trim_w, trim_h, stroke=0, fill=1)
    _title_block(c, trim_w / 2, trim_h - 150, scale=1.0)
    y = trim_h - 344
    for text, tone, font, size in [
        ("Fifteen puzzles. One ex-girlfriend. Zero closure.", "accent", "Body-Bold", 14),
        ("", "soft", "Body", 11),
        ("Themes include: the group chat, the dog she kept,", "light", "Body", 13),
        ("the playlist you must delete, and the speech you", "light", "Body", 13),
        ("gave at her brother's wedding.", "light", "Body", 13),
        ("", "soft", "Body", 11),
        ("Adult humour. Real crosswords. Suspiciously specific.", "accent", "Body-Bold", 13.5),
    ]:
        col = {"accent": ACCENT, "light": LIGHT, "soft": SOFT}[tone]
        c.setFillColor(col)
        c.setFont(font, size)
        c.drawCentredString(trim_w / 2, y, text)
        y -= 26
    cell = 21
    _mini_grid(c, trim_w / 2 - 2.5 * cell, 205, cell, GRID_B)
    c.setFillColor(SOFT)
    c.setFont("Head", 10)
    c.drawCentredString(trim_w / 2, 104, "15 PUZZLES  ·  FULL ANSWER KEY")
    c.drawCentredString(trim_w / 2, 87, "LARGE 8.5 x 11 PAGES  ·  FOR ADULTS")
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 10.5)
    c.drawCentredString(trim_w / 2, 60, "18+  ADULT HUMOUR")
    c.restoreState()

    # ---- spine ----
    if spine > 0.08 * 72:
        c.setFillColor(DARKER)
        c.rect(bleed + trim_w, bleed, spine, trim_h, stroke=0, fill=1)
        c.saveState()
        c.translate(bleed + trim_w + spine / 2, trim_h / 2 + bleed)
        c.rotate(90)
        c.setFillColor(white)
        c.setFont("Head-Bold", 15)
        c.drawCentredString(0, -5, "THE EX-FILES")
        c.setFillColor(SOFT)
        c.setFont("Body", 10)
        c.drawCentredString(0, -22, "Crosswords for Men Who Are Absolutely Fine")
        c.setFillColor(ACCENT)
        c.setFont("Head", 9)
        c.drawCentredString(0, 10, "ADULT HUMOUR")
        c.restoreState()

    # ---- back cover ----
    c.saveState()
    c.translate(bleed, bleed)
    c.setFillColor(DARKER)
    c.rect(0, 0, trim_w, trim_h, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 13)
    c.drawString(60, trim_h - 96, "SHE KEPT THE DOG. YOU KEPT THE WORDS.")
    c.setFillColor(LIGHT)
    c.setFont("Body", 12.5)
    y = trim_h - 140
    for para in [
        "This is a crossword book for the man who is doing fine. Completely",
        "fine. So fine that he has written fifteen crossword puzzles about it,",
        "and every single clue is about her.",
        "",
        "Inside: fifteen large-print grids built around the language of the",
        "modern breakup, the group chat that keeps you upright, and the dog",
        "you still refer to as ours.",
        "",
        "Written for adults. Contains drinking, swearing, and one clue about",
        "the playlist that will go straight through you.",
        "",
        "A perfect gift for a friend who says he does not want to talk about it.",
        "He will laugh. He will finish it. He will absolutely not mention",
        "puzzle eleven to anyone.",
    ]:
        c.drawString(60, y, para)
        y -= 20

    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 12)
    y -= 12
    c.drawString(60, y, "15 PUZZLES  |  FULL ANSWER KEY  |  LARGE 8.5 x 11 PAGES")
    c.setFillColor(SOFT)
    c.setFont("Head", 9.5)
    c.drawString(60, y - 18, "ADULT HUMOUR  ·  NOT FOR CHILDREN  ·  FOR MEN WHO ARE ABSOLUTELY FINE")

    # barcode clear zone, lower right of the back cover
    bw, bh = 2 * 72, 1.2 * 72
    c.setFillColor(white)
    c.rect(trim_w - bw - 0.25 * 72, 0.25 * 72, bw, bh, stroke=0, fill=1)
    c.setFillColor(HexColor("#c0c0c6"))
    c.setFont("Head", 7.5)
    c.drawCentredString(trim_w - bw / 2 - 0.25 * 72, 0.25 * 72 + bh / 2 - 3,
                        "BARCODE AREA — LEAVE BLANK")
    c.restoreState()
    c.save()


if __name__ == "__main__":
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ebook_cover(os.path.join(root, "cover", "The_Ex_Files_ebook_cover.pdf"))
    wrap_cover(os.path.join(root, "cover", "The_Ex_Files_paperback_wrap.pdf"))
    print("covers written")
