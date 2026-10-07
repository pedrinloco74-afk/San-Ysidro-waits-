"""
Cover design for THE EX-FILES.

The cover shows the product: a real crossword grid from the book, filled in,
with the funny breakup answers legible and two clue call-outs pointing at
marquee words (UNSENT, WHISKEY, CLOSURE...). Everything is drawn as vectors so
text stays razor sharp at any size and at KDP thumbnail scale.

Grid data is generated deterministically from the book's own themed word bank,
so the cover can never drift from the puzzles inside.
"""

from __future__ import annotations

import os
import random
import sys

from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bank import THEMED                      # noqa: E402
from weave import Bank, weave, to_grid       # noqa: E402

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

INK = HexColor("#131317")
PANEL = HexColor("#1b1b21")
PANEL_DARK = HexColor("#0e0e12")
ACCENT = HexColor("#c2263f")
ACCENT_DEEP = HexColor("#8c1c30")
LIGHT = HexColor("#ececed")
SOFT = HexColor("#9a9aa3")
GRIDLINE = HexColor("#4a4a52")

# The grid baked into the cover: big, funny, legible words only.
COVER_POOL = {w: c for w, c in THEMED.items()
              if 3 <= len(w) <= 8 and (len(w) >= 6 or
                                       w in ("DOG", "SAD", "GYM", "BAR", "MAD",
                                             "SOB", "DUO", "INK", "SEX", "ALE",
                                             "KEG", "NAG", "HUG"))}
COVER_SIZE = 10
COVER_SEED = 22

MARQUEE = ["UNSENT", "WHISKEY", "CLOSURE", "DIVORCE", "SWIPED", "DUMPED"]

# the three call-outs on the front cover, taken verbatim from the clue bank
CLUE_TEXT = {
    "UNSENT": THEMED["UNSENT"],
    "WHISKEY": THEMED["WHISKEY"],
    "CLOSURE": THEMED["CLOSURE"].split(",")[0] + ".",
}


def cover_grid():
    """Deterministic crossword for the cover artwork."""
    bank = Bank(COVER_POOL, set(COVER_POOL))
    result = weave(bank, COVER_SIZE, random.Random(COVER_SEED),
                   target_words=18, theme_quota=99)
    if result is None:
        raise RuntimeError("cover grid failed to build")
    letters, placed, _checked = result
    grid, shift = to_grid(letters)
    entries = []
    for p in placed:
        entries.append({
            "word": p.word,
            "dir": p.d,
            "cells": [(r - shift[0], c - shift[1]) for r, c in p.cells],
        })
    return grid, letters, shift, entries


def register_fonts():
    pdfmetrics.registerFont(TTFont("Body", f"{FONT_DIR}/DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", f"{FONT_DIR}/DejaVuSerif-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Head", f"{FONT_DIR}/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("Head-Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Mono", f"{FONT_DIR}/DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-Bold", f"{FONT_DIR}/DejaVuSansMono-Bold.ttf"))


# ---------------------------------------------------------------------------
# the crossword artwork
# ---------------------------------------------------------------------------
def draw_grid(c, x0, y_top, cell, grid, letters, shift, highlight, numbers):
    """Draw the filled crossword. `highlight` is a set of (r, c) cells."""
    rows, cols = grid.rows, grid.cols

    def fill_cell(r, col, colour):
        c.setFillColor(colour)
        c.rect(x0 + col * cell, y_top - (r + 1) * cell, cell, cell,
               stroke=0, fill=1)

    # white squares
    for r in range(rows):
        for col in range(cols):
            if not grid.cells[r][col]:
                fill_cell(r, col, white)

    # hairline grid
    c.setStrokeColor(GRIDLINE)
    c.setLineWidth(0.35)
    for r in range(rows + 1):
        c.line(x0, y_top - r * cell, x0 + cols * cell, y_top - r * cell)
    for col in range(cols + 1):
        c.line(x0 + col * cell, y_top, x0 + col * cell, y_top - rows * cell)

    # black squares
    for r in range(rows):
        for col in range(cols):
            if grid.cells[r][col]:
                fill_cell(r, col, INK)

    # numbers, kept small and tucked into the corner so they never touch the
    # centred answer letter
    num_size = cell * 0.185
    c.setFont("Head", num_size)
    for (r, col), num in numbers.items():
        if not grid.cells[r][col]:
            c.setFillColor(HexColor("#8a8a92"))
            c.drawString(x0 + col * cell + cell * 0.045,
                         y_top - (r + 1) * cell + cell * 0.735, str(num))

    # letters
    for r in range(rows):
        for col in range(cols):
            if grid.cells[r][col]:
                continue
            ch = letters.get((r + shift[0], col + shift[1]))
            if not ch:
                continue
            hot = (r, col) in highlight
            size = cell * (0.56 if hot else 0.50)
            font = "Head-Bold" if hot else "Head"
            c.setFont(font, size)
            c.setFillColor(ACCENT if hot else INK)
            tw = pdfmetrics.stringWidth(ch, font, size)
            # sit the letter below the number's band
            c.drawString(x0 + col * cell + (cell - tw) / 2,
                         y_top - (r + 1) * cell + cell * 0.20, ch)

    # frame
    c.setStrokeColor(INK)
    c.setLineWidth(1.6)
    c.rect(x0, y_top - rows * cell, cols * cell, rows * cell, stroke=1, fill=0)


def pick_numbers(entries):
    """Standard crossword numbering, only for the cells we draw."""
    by_start = {}
    for e in entries:
        by_start.setdefault(tuple(e["cells"]), e)
    numbers = {}
    ordered = sorted(by_start.items(), key=lambda kv: (kv[0][0][0], kv[0][0][1]))
    for i, (_cells, _e) in enumerate(ordered, start=1):
        pass
    # real numbering: number every cell that starts an across or down entry
    starts = sorted({cells[0] for cells, _e in by_start.items()}, key=lambda rc: (rc[0], rc[1]))
    num = 0
    for rc in starts:
        num += 1
        numbers[rc] = num
    return numbers


# ---------------------------------------------------------------------------
# front cover artwork
# ---------------------------------------------------------------------------
def front_cover(c, w, h):
    """Front cover: the crossword is the hero.

    The tagline sits *under* the grid and the clue call-outs are one line each,
    which frees the middle of the page so the grid renders at close to full
    width. Every position comes from real glyph metrics, so nothing can collide.
    """
    c.setFillColor(PANEL_DARK)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(PANEL)
    c.rect(0, h * 0.056, w, h * 0.944, stroke=0, fill=1)

    m = w * 0.072
    cx = w / 2
    inner = w - 2 * m

    grid, letters, shift, entries = cover_grid()
    rows, cols = grid.rows, grid.cols

    def asc(font, size):
        return pdfmetrics.getAscent(font, size)

    def desc(font, size):
        # reportlab reports descent as a negative number; we want the
        # magnitude, because every caller subtracts it to move downward
        return abs(pdfmetrics.getDescent(font, size))

    def centred(text, font, size, baseline, colour):
        c.setFillColor(colour)
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)

    def fit_one_line(text, font, size, limit):
        while size > 6 and pdfmetrics.stringWidth(text, font, size) > limit:
            size -= 0.25
        return size

    # ================= top block =================
    y = h - h * 0.048

    the_size = min(w * 0.030, inner / 8.0)
    y -= asc("Head-Bold", the_size)
    centred("THE", "Head-Bold", the_size, y, ACCENT)
    y -= desc("Head-Bold", the_size) + h * 0.010

    title_size = min(w * 0.152, inner / 4.62)
    y -= asc("Head-Bold", title_size)
    title_baseline = y
    centred("EX-FILES", "Head-Bold", title_size, y, LIGHT)

    # the panel edge must sit above the top of the title, never on it
    if title_baseline + asc("Head-Bold", title_size) > h * 0.948:
        raise RuntimeError("wordmark would cross the panel edge")

    y -= desc("Head-Bold", title_size) + h * 0.014
    c.setFillColor(ACCENT)
    c.rect(cx - w * 0.30, y, w * 0.60, h * 0.0048, stroke=0, fill=1)
    # clear the rule, then give the subtitle its full ascender space
    y -= h * 0.034

    subtitle = "A Crossword Book for Men Who Are Absolutely Fine"
    sub_size = fit_one_line(subtitle, "Body", w * 0.042, inner)
    y -= asc("Body", sub_size)
    centred(subtitle, "Body", sub_size, y, LIGHT)
    y -= desc("Body", sub_size) + h * 0.012

    top_block_bottom = y - h * 0.010

    # ================= bottom stack, measured upward =================
    foot_size = w * 0.030
    footer_baseline = h * 0.030

    badges = ["15 PUZZLES", "FULL ANSWER KEY", "18+ ADULT HUMOUR"]
    gap = w * 0.009
    bw = (inner - 2 * gap) / 3
    bh = h * 0.029
    badge_size = min(h * 0.0126, bw / 11.5)
    badge_bottom = footer_baseline + asc("Body", foot_size) * 0.5 + h * 0.016

    callouts = []
    for word in ("UNSENT", "WHISKEY", "CLOSURE"):
        for e in entries:
            if e["word"] == word:
                callouts.append((e, CLUE_TEXT[word]))
                break

    call_size = min(w * 0.0305, inner / 24.0)
    call_lead = call_size * 1.55
    call_bottom = badge_bottom + bh + h * 0.020
    call_top = call_bottom + call_lead * len(callouts)

    # tagline sits between the grid and the call-outs: build it bottom-up so the
    # block occupies exactly [tag_bottom, tag_top] and cannot reach the call-outs
    tag_lines = ["Fifteen puzzles about her, the dog, and the group chat",
                 "that held you together."]
    tag_size = w * 0.0355
    while tag_size > w * 0.022 and any(
            pdfmetrics.stringWidth(t, "Body-Bold", tag_size) > inner
            for t in tag_lines):
        tag_size -= 0.25
    tag_lead = tag_size * 1.34
    tag_asc = asc("Body-Bold", tag_size)
    tag_desc = desc("Body-Bold", tag_size)
    tag_block = tag_asc + tag_lead * (len(tag_lines) - 1) + tag_desc
    tag_bottom = call_top + h * 0.034
    tag_top = tag_bottom + tag_block

    # ================= the grid fills the remaining band =================
    card_pad = w * 0.017
    band_top = top_block_bottom
    band_bottom = tag_top + h * 0.016
    cell = min(inner / cols, (band_top - band_bottom - 2 * card_pad) / rows)
    if cell * rows + 2 * card_pad > band_top - band_bottom:
        raise RuntimeError("cover grid does not fit its band")
    gw = cell * cols
    gx = cx - gw / 2
    card_h = cell * rows + 2 * card_pad
    card_top = band_top
    grid_top = card_top - card_pad

    c.setFillColor(HexColor("#f7f7f8"))
    c.rect(gx - card_pad, card_top - card_h, gw + 2 * card_pad, card_h,
           stroke=0, fill=1)

    highlight = set()
    for e in entries:
        if e["word"] in ("UNSENT", "WHISKEY", "CLOSURE", "DIVORCE", "SWIPED",
                         "DUMPED"):
            highlight.update(e["cells"])

    draw_grid(c, gx, grid_top, cell, grid, letters, shift, highlight,
              pick_numbers(entries))

    # ================= tagline under the grid =================
    ty = tag_top
    for text in tag_lines:
        ty -= tag_asc
        centred(text, "Body-Bold", tag_size, ty, ACCENT)
        ty -= tag_lead

    # ================= clue call-outs, one line each =================
    box = w * 0.019
    cy = call_top
    for e, text in callouts:
        cy -= asc("Mono-Bold", call_size)
        c.setFillColor(ACCENT)
        c.rect(m, cy + call_size * 0.14, box, box, stroke=0, fill=1)
        key = f"{e['dir']}  {e['word']}   "
        c.setFillColor(ACCENT)
        c.setFont("Mono-Bold", call_size)
        c.drawString(m + box * 1.7, cy, key)
        kw = pdfmetrics.stringWidth(key, "Mono-Bold", call_size)
        c.setFillColor(LIGHT)
        c.setFont("Body", call_size)
        # shift the serif clue text a touch so its baseline matches the mono label
        c.drawString(m + box * 1.7 + kw, cy - call_size * 0.06, text)
        cy -= call_lead

    # ================= badges and footer =================
    bx = m
    for b in badges:
        c.setStrokeColor(ACCENT_DEEP)
        c.setLineWidth(1)
        c.rect(bx, badge_bottom, bw, bh, stroke=1, fill=0)
        c.setFillColor(LIGHT)
        c.setFont("Head-Bold", badge_size)
        tw = pdfmetrics.stringWidth(b, "Head-Bold", badge_size)
        c.drawString(bx + (bw - tw) / 2,
                     badge_bottom + bh / 2 - asc("Head-Bold", badge_size) * 0.34,
                     b)
        bx += bw + gap

    c.setFillColor(SOFT)
    c.setFont("Body", foot_size)
    c.drawCentredString(cx, footer_baseline,
                        "The gift for the man who says he is fine.")


# ---------------------------------------------------------------------------
# back cover artwork
# ---------------------------------------------------------------------------
def back_cover(c, w, h):
    """Back cover. Every line is width-fitted to the trim, because a line that
    overflows spills across the spine onto the front cover when the wrap is
    imposed for print."""
    BLOCKS = [
        ("body", "He says he is fine. He is not fine, and you both know it,"),
        ("body", "so do not ask him again \u2014 hand him this instead."),
        ("gap", ""),
        ("body", "Fifteen original crossword puzzles built out of the only"),
        ("body", "thing a man actually wants to talk about after a breakup:"),
        ("body", "her, the dog, the group chat, and the playlist he has been"),
        ("body", "told twice to delete."),
        ("gap", ""),
        ("body", "Every grid is packed with answers you will recognise:"),
        ("mono", "UNSENT    the texts you composed and never sent"),
        ("mono", "WHISKEY   coping, with a label and a story"),
        ("mono", "CLOSURE   not available from an app"),
        ("mono", "DUMPED    your status, legally and socially"),
        ("mono", "SWIPED    what you did on the app while in a queue"),
        ("gap", ""),
        ("body", "Also inside: the Ground Rules of the Breakup, a translation"),
        ("body", "of the ten messages the group chat will send you next month,"),
        ("body", "a promises page you will fail, and a scorecard you should"),
        ("body", "not fill in honestly."),
        ("gap", ""),
        ("body", "No advice. No journaling prompts. Just proper crosswords,"),
        ("body", "fifteen of them, with a full answer key and jokes between"),
        ("body", "the puzzles."),
    ]

    m = w * 0.09
    limit = w - 2 * m
    top = h - h * 0.205
    bottom = h * 0.150          # clear of the barcode panel

    def widths_ok(body, mono):
        for kind, text in BLOCKS:
            if kind == "body" and pdfmetrics.stringWidth(text, "Body", body) > limit:
                return False
            if kind == "mono" and pdfmetrics.stringWidth(text, "Mono-Bold", mono) > limit:
                return False
        return True

    def block_height(body, mono):
        total = 0.0
        for kind, _text in BLOCKS:
            if kind == "gap":
                total += body * 0.55
            elif kind == "body":
                total += body * 1.34
            else:
                total += mono * 1.50
        return total

    body = w * 0.0335
    mono = w * 0.0305
    while body > w * 0.020 and (block_height(body, mono) > top - bottom
                                or not widths_ok(body, mono)):
        body -= 0.25
        mono = body * 0.93

    if not widths_ok(body, mono):
        raise RuntimeError("back cover copy cannot be fitted to the trim")

    c.setFillColor(PANEL_DARK)
    c.rect(0, 0, w, h, stroke=0, fill=1)

    head = w * 0.040
    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", head)
    c.drawString(m, h - h * 0.110, "SHE KEPT THE DOG.")
    c.drawString(m, h - h * 0.110 - head * 1.35, "YOU KEPT THE WORDS.")

    y = top
    for kind, text in BLOCKS:
        if kind == "gap":
            y -= body * 0.55
            continue
        size = body if kind == "body" else mono
        c.setFillColor(LIGHT if kind == "body" else ACCENT)
        c.setFont("Body" if kind == "body" else "Mono-Bold", size)
        c.drawString(m, y, text)
        y -= size * (1.34 if kind == "body" else 1.50)

    # ---- footer: both lines shrunk until they fit the trim exactly ----
    y -= body * 0.90
    line1 = "15 PUZZLES  |  FULL ANSWER KEY  |  8.5 x 11 LARGE PRINT"
    line2 = "ADULT HUMOUR \u00b7 NOT FOR CHILDREN \u00b7 FOR MEN WHO ARE ABSOLUTELY FINE"
    s1 = w * 0.032
    while s1 > 6 and pdfmetrics.stringWidth(line1, "Head-Bold", s1) > limit:
        s1 -= 0.25
    s2 = w * 0.025
    while s2 > 5 and pdfmetrics.stringWidth(line2, "Head", s2) > limit:
        s2 -= 0.25

    c.setFillColor(ACCENT)
    c.setFont("Head-Bold", s1)
    c.drawString(m, y, line1)
    y -= s1 * 1.55
    c.setFillColor(SOFT)
    c.setFont("Head", s2)
    c.drawString(m, y, line2)
    return y


def barcode_panel(c, trim_w, trim_h):
    """KDP reserves the lower-right of the back cover for the barcode."""
    bw, bh = 2 * 72, 1.2 * 72
    c.setFillColor(white)
    c.rect(trim_w - bw - 0.25 * 72, 0.25 * 72, bw, bh, stroke=0, fill=1)
    c.setFillColor(HexColor("#c0c0c6"))
    c.setFont("Head", 7)
    c.drawCentredString(trim_w - bw / 2 - 0.25 * 72, 0.25 * 72 + bh / 2 - 3,
                        "BARCODE AREA \u2014 LEAVE BLANK")
