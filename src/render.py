"""
PDF renderer for the book: draws the puzzle pages, answer keys and the
front/back matter at 8.5 x 11 in with embedded fonts (KDP wants embedded
fonts in print-ready interiors).
"""

from __future__ import annotations

import os

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = letter                    # 612 x 792 pt
WORDS = {12: "Twelve", 15: "Fifteen"}
MARGIN = 0.55 * 72
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

INK = HexColor("#1b1b1d")
SOFT = HexColor("#6b6b73")
LINE = HexColor("#c9c9cf")
ACCENT = HexColor("#a4243b")               # oxblood
PAPER = HexColor("#ffffff")
CELL_BG = HexColor("#f2f2f4")


def register_fonts():
    pdfmetrics.registerFont(TTFont("Body", f"{FONT_DIR}/DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", f"{FONT_DIR}/DejaVuSerif-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Head", f"{FONT_DIR}/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("Head-Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Mono", f"{FONT_DIR}/DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-Bold", f"{FONT_DIR}/DejaVuSansMono-Bold.ttf"))


def wrap(text, font, size, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if pdfmetrics.stringWidth(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# front matter
# ---------------------------------------------------------------------------
def title_page(c, meta):
    """Interior title page. Print interiors stay on white, no bleed."""
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.rect(MARGIN, PAGE_H - 2.35 * 72, PAGE_W - 2 * MARGIN, 0.11 * 72,
           stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 14)
    c.drawString(MARGIN, PAGE_H - 1.75 * 72, "THE")

    c.setFillColor(INK)
    c.setFont("Head-Bold", 66)
    c.drawString(MARGIN, PAGE_H - 2.75 * 72, "EX-FILES")

    c.setFillColor(SOFT)
    c.setFont("Body", 15)
    c.drawString(MARGIN, PAGE_H - 3.15 * 72,
                 "A Crossword Book for Men Who Are Absolutely Fine")

    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(MARGIN, PAGE_H - 3.55 * 72, PAGE_W - MARGIN, PAGE_H - 3.55 * 72)

    lines = [
        (("Body"), 12.5, f"{WORDS[meta['puzzle_count']]} puzzles. One ex-girlfriend. Zero closure.", 0),
        ("", 0, "", 14),
        ("Body", 12.5, "Somewhere in here are the things you said out loud at two in the", 0),
        ("Body", 12.5, "morning, written down as clues so you can finally get them out of", 0),
        ("Body", 12.5, "your system.", 0),
        ("", 0, "", 14),
        ("Body-Bold", 13, "You are not sad. You are themed.", 0),
    ]
    y = PAGE_H - 4.05 * 72
    for font, size, text, pad in lines:
        if font:
            c.setFillColor(INK if "Bold" in font else SOFT)
            c.setFont(font, size)
            c.drawString(MARGIN, y, text)
        y -= (size + 6 + pad)

    # little crossword motif
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    cell = 26
    x0, y0 = MARGIN, MARGIN + 60
    pattern = [".#.", "###", ".#."]
    for r in range(3):
        for col in range(3):
            x, yy = x0 + col * cell, y0 - r * cell
            if pattern[r][col] == "#":
                c.setFillColor(INK)
                c.rect(x, yy, cell, cell, stroke=0, fill=1)
            else:
                c.rect(x, yy, cell, cell, stroke=1, fill=0)

    c.setFillColor(SOFT)
    c.setFont("Head", 10.5)
    c.drawString(MARGIN, MARGIN + 10,
                 f"{meta['puzzle_count']} PUZZLES   ·   FULL ANSWER KEY   ·   LARGE 8.5 x 11 PAGES")
    c.showPage()


def copyright_page(c, meta):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Head-Bold", 17)
    c.drawString(MARGIN, PAGE_H - MARGIN - 22, "Before we begin")

    text_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN - 58

    def para(text, font="Body", size=11.5, leading=17, gap=8):
        nonlocal y
        c.setFont(font, size)
        c.setFillColor(INK)
        for ln in wrap(text, font, size, text_w):
            c.drawString(MARGIN, y, ln)
            y -= leading
        y -= gap

    para("This book is a joke. It is also a real crossword book. It can be both.")
    para("Every grid in here was built by hand-writing a themed answer list and then "
         "weaving the words together until they interlocked, so every letter you see "
         "in a square is doing a job. If a clue makes you laugh and then immediately "
         "feel something, that is the intended effect, and you should not worry about it.")
    para("The tone is adult: there is swearing, there is drinking, and there is one "
         "clue about the group chat that will hit too close to home. If you are buying "
         "this for somebody's birthday, congratulations, you have excellent taste and "
         "no supervision.")

    y -= 6
    c.setFont("Head-Bold", 12.5)
    c.drawString(MARGIN, y, "How the puzzles work")
    y -= 24
    para("These are freeform crosswords. Words run across and down, and they cross "
         "wherever they happen to share a letter.", leading=16, gap=3)
    para("That means some squares are crossed by two words and some are not. Start "
         "with the words that cross something, then work outward, the way you would "
         "with any crossword.", leading=16, gap=3)
    para("Every answer is a real word between 3 and 8 letters, and every one of them "
         "is checked against the grid before the book is printed. The theme never "
         "changes: her, him, the dog, the group chat, and your ongoing recovery.",
         leading=16, gap=3)
    para("Numbers in the top-left corner of a word's first square send you to the "
         "ACROSS and DOWN lists printed under each grid.", leading=16, gap=3)
    para("Stuck? Every answer is in the back. Try not to go there in the first hour.",
         leading=16, gap=3)
    para(f"If you finish all {WORDS.get(meta['puzzle_count'], meta['puzzle_count']).lower()} "
         f"puzzles, you have officially processed the breakup and may now talk about "
         f"something else at parties.", leading=16, gap=3)

    y -= 14
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 18
    c.setFont("Head", 8.5)
    c.setFillColor(SOFT)
    for ln in [
        "All contents copyright (c) 2026. All rights reserved. No part of this book may be reproduced",
        "or distributed in any form without written permission from the publisher, except for brief",
        "quotations in a review. Names, characters and events are the product of the author's very",
        "active imagination and several people's group chats. For entertainment purposes only.",
    ]:
        c.drawString(MARGIN, y, ln)
        y -= 13
    c.showPage()


def section_page(c, kicker, title, blurb_lines):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 11)
    c.drawString(MARGIN, PAGE_H - MARGIN - 16, kicker.upper())
    c.setFillColor(INK)
    c.setFont("Head-Bold", 34)
    c.drawString(MARGIN, PAGE_H - MARGIN - 62, title)
    c.setStrokeColor(INK)
    c.setLineWidth(2)
    c.line(MARGIN, PAGE_H - MARGIN - 78, MARGIN + 1.4 * 72, PAGE_H - MARGIN - 78)
    y = PAGE_H - MARGIN - 116
    for ln in blurb_lines:
        if ln == "":
            y -= 10
            continue
        bold = ln.startswith("**")
        text = ln.replace("**", "")
        font = "Body-Bold" if bold else "Body"
        for wrapped in wrap(text, font, 11.5, PAGE_W - 2 * MARGIN):
            c.setFont(font, 11.5)
            c.setFillColor(INK)
            c.drawString(MARGIN, y, wrapped)
            y -= 18
        y -= 4
    c.showPage()


# ---------------------------------------------------------------------------
# puzzle page
# ---------------------------------------------------------------------------
def _grid_metrics(rows, cols, max_w=6.6 * 72, max_h=6.15 * 72):
    cell = min(max_w / cols, max_h / rows)
    w, h = cell * cols, cell * rows
    x = (PAGE_W - w) / 2
    return cell, x, w, h


def _grid_metrics_in(rows, cols, max_w, max_h):
    cell = min(max_w / cols, max_h / rows)
    return cell, cell * cols, cell * rows


def draw_grid(c, puzzle, top_y, letters=None, show_numbers=True,
              max_w=6.6 * 72, max_h=6.15 * 72):
    grid = puzzle["grid"]
    rows, cols = len(grid), len(grid[0])
    cell, x0, w, h = _grid_metrics(rows, cols, max_w, max_h)
    y_top = top_y
    y0 = y_top - h

    # cell backgrounds + fine lines
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] == "#":
                continue
            c.setFillColor(white)
            c.rect(x0 + col * cell, y_top - (r + 1) * cell, cell, cell,
                   stroke=0, fill=1)

    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    for r in range(rows + 1):
        c.line(x0, y_top - r * cell, x0 + w, y_top - r * cell)
    for col in range(cols + 1):
        c.line(x0 + col * cell, y_top, x0 + col * cell, y_top - h)

    # black squares
    c.setFillColor(INK)
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] == "#":
                c.rect(x0 + col * cell, y_top - (r + 1) * cell, cell, cell,
                       stroke=0, fill=1)

    # numbers
    if show_numbers:
        c.setFillColor(INK)
        c.setFont("Head", max(5.2, cell * 0.26))
        for r in range(rows):
            for col in range(cols):
                num = puzzle["numbers"].get(f"{r},{col}")
                if num and grid[r][col] != "#":
                    c.drawString(x0 + col * cell + cell * 0.09,
                                 y_top - (r + 1) * cell + cell * 0.70, str(num))

    # letters (answer key)
    if letters is not None:
        c.setFillColor(ACCENT)
        c.setFont("Head-Bold", cell * 0.60)
        for r in range(rows):
            for col in range(cols):
                ch = letters.get((r, col))
                if ch and grid[r][col] != "#":
                    tw = pdfmetrics.stringWidth(ch, "Head-Bold", cell * 0.60)
                    c.drawString(x0 + col * cell + (cell - tw) / 2,
                                 y_top - (r + 1) * cell + cell * 0.33, ch)

    # outer frame
    c.setStrokeColor(INK)
    c.setLineWidth(1.6)
    c.rect(x0, y0, w, h, stroke=1, fill=0)
    return y0


def _draw_clue_column(c, entries, x, top_y, width, font_size, leading,
                      header, min_y):
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 12.5)
    c.drawString(x, top_y, header)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.1)
    c.line(x, top_y - 6, x + width, top_y - 6)
    y = top_y - 21
    c.setFillColor(INK)
    for e in entries:
        label = f"{e['num']}. "
        lw = pdfmetrics.stringWidth(label, "Head-Bold", font_size)
        c.setFont("Head-Bold", font_size)
        c.drawString(x, y, label)
        c.setFont("Body", font_size)
        lines = wrap(e["clue"], "Body", font_size, width - lw)
        for i, ln in enumerate(lines):
            c.drawString(x + (lw if i == 0 else lw), y, ln)
            y -= leading
        y -= leading * 0.30
        if y < min_y:
            return None
    return y


CLUE_SIZES = ((9.6, 12.2), (9.0, 11.5), (8.4, 10.8), (7.9, 10.2),
              (7.5, 9.7), (7.1, 9.2), (6.8, 8.8))

WARNINGS: list[str] = []


def _fit_clues(across, down, col_w, avail_h):
    """Pick the largest clue font whose two columns fit in avail_h."""
    for size, leading in CLUE_SIZES:
        need = max(_column_height(across, col_w, size, leading),
                   _column_height(down, col_w, size, leading))
        if need <= avail_h:
            return size, leading, need
    size, leading = CLUE_SIZES[-1]
    return size, leading, max(_column_height(across, col_w, size, leading),
                              _column_height(down, col_w, size, leading))


def puzzle_page(c, puzzle, meta):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    header_h = 58
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 10.5)
    c.drawString(MARGIN, PAGE_H - MARGIN - 10, f"PUZZLE {puzzle['index']} OF {meta['puzzle_count']}")
    c.setFillColor(SOFT)
    c.setFont("Head", 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 10,
                      f"THE EX-FILES  ·  {puzzle['theme_hint'].upper()}")
    c.setFillColor(INK)
    c.setFont("Head-Bold", 23)
    c.drawString(MARGIN, PAGE_H - MARGIN - 38, puzzle["title"])
    c.setStrokeColor(INK)
    c.setLineWidth(1.8)
    c.line(MARGIN, PAGE_H - MARGIN - 48, PAGE_W - MARGIN, PAGE_H - MARGIN - 48)

    across = sorted((e for e in puzzle["entries"] if e["dir"] == "A"),
                    key=lambda e: e["num"])
    down = sorted((e for e in puzzle["entries"] if e["dir"] == "D"),
                  key=lambda e: e["num"])

    col_gap = 26
    col_w = (PAGE_W - 2 * MARGIN - col_gap) / 2
    grid_top = PAGE_H - MARGIN - header_h
    clue_bottom = MARGIN + 18
    gap_above_clues = 18

    # the grid shrinks so the clues always fit on the page
    grid_budget = grid_top - gap_above_clues - clue_bottom
    size, leading, need = _fit_clues(across, down, col_w, grid_budget - 2.6 * 72)
    # give the clues 6pt of slack so the last line never kisses the footer
    grid_h = min(6.25 * 72, max(2.5 * 72, grid_budget - need - 6))
    rows, cols = len(puzzle["grid"]), len(puzzle["grid"][0])
    cell = min(6.6 * 72 / cols, grid_h / rows)
    grid_w = cell * cols
    grid_x = (PAGE_W - grid_w) / 2
    grid_bottom = grid_top - cell * rows

    clue_top = grid_bottom - gap_above_clues

    # hard check: text must never run off the bottom of the page
    if need > clue_top - clue_bottom:
        WARNINGS.append(
            f"puzzle {puzzle['index']}: clues need {need:.0f}pt but only "
            f"{clue_top - clue_bottom:.0f}pt available")
    if clue_top < clue_bottom + 40:
        WARNINGS.append(f"puzzle {puzzle['index']}: clue area collapsed")

    _grid_frame(c, puzzle, grid_x, grid_top, cell)
    _draw_clue_column(c, across, MARGIN, clue_top, col_w, size, leading,
                      "ACROSS", clue_bottom)
    _draw_clue_column(c, down, MARGIN + col_w + col_gap, clue_top, col_w, size,
                      leading, "DOWN", clue_bottom)

    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, MARGIN + 12, PAGE_W - MARGIN, MARGIN + 12)
    c.setFillColor(SOFT)
    c.setFont("Head", 8)
    c.drawCentredString(PAGE_W / 2, MARGIN, 
                        "Answers in the back. So are most of the feelings.")
    c.showPage()


def _grid_frame(c, puzzle, x0, top_y, cell):
    grid = puzzle["grid"]
    rows, cols = len(grid), len(grid[0])
    h, w = cell * rows, cell * cols
    c.setFillColor(white)
    c.rect(x0, top_y - h, w, h, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    for r in range(rows + 1):
        c.line(x0, top_y - r * cell, x0 + w, top_y - r * cell)
    for col in range(cols + 1):
        c.line(x0 + col * cell, top_y, x0 + col * cell, top_y - h)
    c.setFillColor(INK)
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] == "#":
                c.rect(x0 + col * cell, top_y - (r + 1) * cell, cell, cell,
                       stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Head", max(5.0, cell * 0.26))
    for r in range(rows):
        for col in range(cols):
            num = puzzle["numbers"].get(f"{r},{col}")
            if num and grid[r][col] != "#":
                c.drawString(x0 + col * cell + cell * 0.09,
                             top_y - (r + 1) * cell + cell * 0.68, str(num))
    c.setStrokeColor(INK)
    c.setLineWidth(1.6)
    c.rect(x0, top_y - h, w, h, stroke=1, fill=0)


def _column_height(entries, width, size, leading):
    total = 21
    for e in entries:
        label = f"{e['num']}. "
        lw = pdfmetrics.stringWidth(label, "Head-Bold", size)
        lines = wrap(e["clue"], "Body", size, width - lw)
        total += len(lines) * leading + leading * 0.30
    return total


# ---------------------------------------------------------------------------
# answer key
# ---------------------------------------------------------------------------
def answer_page(c, puzzles, page_no, meta):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 10.5)
    c.drawString(MARGIN, PAGE_H - MARGIN - 10, "ANSWER KEY")
    c.setFillColor(SOFT)
    c.setFont("Head", 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 10,
                      "NOBODY SAW YOU TURN TO THIS PAGE")
    c.setFillColor(INK)
    c.setFont("Head-Bold", 22)
    c.drawString(MARGIN, PAGE_H - MARGIN - 38, "The Answers, Admitted")
    c.setStrokeColor(INK)
    c.setLineWidth(1.8)
    c.line(MARGIN, PAGE_H - MARGIN - 48, PAGE_W - MARGIN, PAGE_H - MARGIN - 48)

    top = PAGE_H - MARGIN - 56
    bottom = MARGIN + 16
    slot = (top - bottom) / len(puzzles)
    for i, pz in enumerate(puzzles):
        slot_top = top - i * slot
        c.setFillColor(INK)
        c.setFont("Head-Bold", 11.5)
        c.drawString(MARGIN, slot_top - 10,
                     f"PUZZLE {pz['index']}  —  {pz['title']}")
        rows, cols = len(pz["grid"]), len(pz["grid"][0])
        avail_h = slot - 20
        avail_w = 4.6 * 72
        cell, gw, gh = _grid_metrics_in(rows, cols, avail_w, avail_h)
        letters = {(int(k.split(",")[0]), int(k.split(",")[1])): v
                   for k, v in pz["answer"].items()}
        _grid_at(c, pz, (PAGE_W - gw) / 2, slot_top - 16, cell, letters)
    c.setFillColor(SOFT)
    c.setFont("Head", 8.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 2, str(page_no))
    c.showPage()


def _grid_at(c, puzzle, x0, y_top, cell, letters):
    grid = puzzle["grid"]
    rows, cols = len(grid), len(grid[0])
    h = cell * rows
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] != "#":
                c.setFillColor(white)
                c.rect(x0 + col * cell, y_top - (r + 1) * cell, cell, cell,
                       stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.3)
    for r in range(rows + 1):
        c.line(x0, y_top - r * cell, x0 + cols * cell, y_top - r * cell)
    for col in range(cols + 1):
        c.line(x0 + col * cell, y_top, x0 + col * cell, y_top - h)
    c.setFillColor(INK)
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] == "#":
                c.rect(x0 + col * cell, y_top - (r + 1) * cell, cell, cell,
                       stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", cell * 0.62)
    for r in range(rows):
        for col in range(cols):
            ch = letters.get((r, col))
            if ch and grid[r][col] != "#":
                tw = pdfmetrics.stringWidth(ch, "Head-Bold", cell * 0.62)
                c.drawString(x0 + col * cell + (cell - tw) / 2,
                             y_top - (r + 1) * cell + cell * 0.30, ch)
    c.setStrokeColor(INK)
    c.setLineWidth(1.2)
    c.rect(x0, y_top - h, cols * cell, h, stroke=1, fill=0)


def back_page(c, meta):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", 11)
    c.drawString(MARGIN, PAGE_H - MARGIN - 16, "ONE LAST THING")
    c.setFillColor(INK)
    c.setFont("Head-Bold", 30)
    c.drawString(MARGIN, PAGE_H - MARGIN - 58, "You finished it.")
    y = PAGE_H - MARGIN - 100
    for ln in [
        f"{WORDS[meta['puzzle_count']]} puzzles. You did them. You are, statistically, fine now.",
        "",
        "Somewhere around puzzle four you stopped thinking about her and started",
        "thinking about a four-letter word for 'the guy she told you not to worry",
        "about.' That is growth. That is practically a hobby.",
        "",
        "If you laughed even once, this book did its job. If you cried once, that",
        "was the postage, and nobody in the group chat needs to hear about it.",
        "",
        "Put it on a shelf. Buy a copy for a friend who is going through it.",
        "Tell him you found it in a store and thought of him, which is a lie,",
        "and also the nicest thing you will do all year.",
    ]:
        c.setFont("Body", 12 if ln else 6)
        c.drawString(MARGIN, y, ln)
        y -= 20 if ln else 8

    y -= 26
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.2)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 26
    c.setFont("Head-Bold", 13)
    c.drawString(MARGIN, y, "THE EX-FILES")
    y -= 18
    c.setFont("Head", 10.5)
    c.setFillColor(SOFT)
    c.drawString(MARGIN, y, "Crosswords for the recently single, the long recovered,")
    c.drawString(MARGIN + 0, y - 14, "and anyone who needs a gift for a man who is 'totally fine.'")
    c.showPage()
