#!/usr/bin/env python3
"""
Builds "TIJUANA BIRRIA: A Short, Illustrated Field Guide" (PDF, 8 x 10 in, ~18 pages).

python3 build_book.py
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

from fpdf import FPDF
from fpdf.enums import MethodReturnValue

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
JPG = os.path.join(HERE, "art_jpg")
FONTS = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- page metrics
W, H = 576.0, 720.0          # 8 x 10 inches @ 72pt
M = 48.0                     # side margin
CW = W - 2 * M               # content width = 472
TOP = 48.0
BOT = H - 56.0

# ------------------------------------------------------------------ palette
PAPER = (253, 248, 238)
CREAM = (247, 238, 220)
INK = (42, 32, 27)
INK2 = (86, 70, 58)
RED = (166, 46, 30)
RED_L = (198, 74, 52)
OCHRE = (184, 122, 42)
GOLD = (214, 168, 90)
GREEN = (104, 118, 62)
MUTED = (132, 114, 98)
LINE = (214, 198, 172)

FONT_DIR = FONTS


# ------------------------------------------------------------------ image prep
def prep_images():
    """Downscale + JPEG-encode the artwork once, cache in art_jpg/."""
    os.makedirs(JPG, exist_ok=True)
    out = {}
    for name in sorted(os.listdir(ART)):
        if not name.lower().endswith(".png"):
            continue
        src = os.path.join(ART, name)
        dst = os.path.join(JPG, name.replace(".png", ".jpg"))
        if not os.path.exists(dst):
            im = Image.open(src).convert("RGB")
            if im.width > 1500:
                im = im.resize((1500, round(im.height * 1500 / im.width)),
                               Image.LANCZOS)
            im.save(dst, "JPEG", quality=86, optimize=True)
        out[name.replace(".png", "")] = dst
    # square centre-crop of the cover art for the title page
    src = os.path.join(ART, "cover.png")
    dst = os.path.join(JPG, "cover_sq.jpg")
    if not os.path.exists(dst):
        im = Image.open(src).convert("RGB")
        side = min(im.size)
        im = im.crop(((im.width - side) // 2, (im.height - side) // 2,
                      (im.width + side) // 2, (im.height + side) // 2))
        if side > 1200:
            im = im.resize((1200, 1200), Image.LANCZOS)
        im.save(dst, "JPEG", quality=86, optimize=True)
    out["cover_sq"] = dst
    return out


IMAGES = prep_images()


def img_ratio(key):
    im = Image.open(IMAGES[key])
    return im.height / im.width


# ------------------------------------------------------------------ pdf class
class Book(FPDF):
    def __init__(self):
        super().__init__(unit="pt", format=(W, H))
        self.set_auto_page_break(False)
        self.set_margins(M, TOP, M)
        for fam, files in {
            "D": [("Playfair-Regular.ttf", ""), ("Playfair-Bold.ttf", "B"),
                  ("Playfair-Black.ttf", "BB"), ("Playfair-Italic.ttf", "I")],
            "B": [("Lora-Regular.ttf", ""), ("Lora-Bold.ttf", "B"),
                  ("Lora-Italic.ttf", "I")],
            "U": [("Archivo-Regular.ttf", ""), ("Archivo-Bold.ttf", "B"),
                  ("Archivo-ExtraBold.ttf", "BB")],
        }.items():
            for fn, style in files:
                self.add_font(fam, style, os.path.join(FONT_DIR, fn))
        self.cover_mode = True
        self.chapter = ""

    # ---- page furniture
    def header(self):
        if self.cover_mode:
            return
        self.set_fill_color(*PAPER)
        self.rect(0, 0, W, H, style="F")
        self.set_font("U", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(M + 2, 26)
        label = self.chapter.upper()
        self.cell(200, 9, label, align="L")
        self.set_font("U", "B", 7)
        self.set_xy(W - M - 120, 26)
        self.cell(120, 9, "TIJUANA BIRRIA", align="R")
        self.set_draw_color(*LINE)
        self.set_line_width(0.6)
        self.line(M, 38, W - M, 38)

    def footer(self):
        if self.cover_mode:
            return
        self.set_draw_color(*LINE)
        self.set_line_width(0.5)
        self.line(M, H - 54, W - M, H - 54)
        self.set_font("U", "B", 8)
        self.set_text_color(*MUTED)
        self.set_xy(M, H - 48)
        self.cell(CW, 12, str(self.page_no()), align="C")


pdf = Book()


# ------------------------------------------------------------------ utilities
def new_page(chapter=""):
    pdf.chapter = chapter
    pdf.add_page()
    pdf.set_y(TOP + 14)


def space(h):
    pdf.set_y(pdf.get_y() + h)


def ensure(h):
    """Page-break if h doesn't fit."""
    if pdf.get_y() + h > BOT:
        new_page(pdf.chapter)
        return True
    return False


def width_of(text, family="B", style="B", size=10.5):
    pdf.set_font(family, style, size)
    return pdf.get_string_width(text)


def para(text, size=10.3, leading=14.6, family="B", style="", color=INK,
         align="L", indent=0.0, gap_after=7.0):
    pdf.set_font(family, style, size)
    # measure first so long paragraphs never run off the page
    h = pdf.multi_cell(CW - indent, leading, text, align=align, markdown=True,
                       dry_run=True, output=MethodReturnValue.HEIGHT)
    if pdf.get_y() + h > BOT and h < (BOT - TOP):
        new_page(pdf.chapter)
    pdf.set_text_color(*color)
    pdf.set_x(M + indent)
    pdf.multi_cell(CW - indent, leading, text, align=align, markdown=True,
                   new_x="LEFT", new_y="NEXT")
    space(gap_after)


def lead(text, size=12.4, leading=18.6):
    para(text, size=size, leading=leading, family="B", style="",
         color=INK2, gap_after=10)


def h1(text):
    ensure(70)
    pdf.set_font("D", "BB", 27)
    pdf.set_text_color(*RED)
    pdf.set_x(M)
    pdf.multi_cell(CW, 30, text, new_x="LEFT", new_y="NEXT")
    space(2)
    rule(0.9, RED)
    space(11)


def h2(text, size=15, color=INK, before=10):
    space(before)
    ensure(46)
    pdf.set_font("D", "B", size)
    pdf.set_text_color(*color)
    pdf.set_x(M)
    pdf.multi_cell(CW, size + 6, text, new_x="LEFT", new_y="NEXT")
    space(3)


def h3(text, size=11.2, color=RED, before=6):
    space(before)
    ensure(34)
    pdf.set_font("U", "BB", size)
    pdf.set_text_color(*color)
    pdf.set_x(M)
    pdf.multi_cell(CW, 15, text, new_x="LEFT", new_y="NEXT")
    space(3)


def rule(width=0.7, color=LINE, x0=None, x1=None):
    pdf.set_draw_color(*color)
    pdf.set_line_width(width)
    pdf.line(M if x0 is None else x0, pdf.get_y(),
             W - M if x1 is None else x1, pdf.get_y())
    space(6)


def ornament(gap=9):
    """Small centered diamond divider."""
    space(gap)
    ensure(20)
    y = pdf.get_y() + 4
    cx = W / 2
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.6)
    pdf.line(M, y, cx - 22, y)
    pdf.line(cx + 22, y, W - M, y)
    pdf.set_fill_color(*RED)
    pdf.polygon([(cx, y - 4.5), (cx + 4.5, y), (cx, y + 4.5), (cx - 4.5, y)],
                style="F")
    space(gap + 8)


def bullet(text, size=10.3, leading=14.4, color=INK, marker="dash",
           indent=0.0, gap=4.6):
    pdf.set_font("B", "", size)
    lines = _wrap(text, CW - 18 - indent, size)
    ensure(len(lines) * leading + gap)
    for i, ln in enumerate(lines):
        if i:
            pdf.set_x(M + indent + 18)
        else:
            if marker == "dash":
                pdf.set_fill_color(*RED)
                pdf.rect(M + indent + 2, pdf.get_y() + size * 0.42, 8, 1.6, "F")
            elif marker == "dot":
                pdf.set_fill_color(*RED)
                pdf.ellipse(M + indent + 3, pdf.get_y() + size * 0.35, 3.2, 3.2, "F")
            elif marker == "chile":
                chile_icon(M + indent + 1, pdf.get_y() + 1, 11, RED)
            pdf.set_x(M + indent + 18)
        pdf.set_text_color(*color)
        pdf.multi_cell(CW - 18 - indent, leading, ln, markdown=True,
                       new_x="LEFT", new_y="NEXT")
    space(gap - 0.8)


def _wrap(text, w, size):
    """Very small wrapper that respects explicit \\n and **bold** markers."""
    raw = text.split("\n")
    plain = [r.replace("**", "").replace("*", "").replace("_", "") for r in raw]
    out = []
    for r, p in zip(raw, plain):
        words = p.split(" ")
        # re-align bold markers: operate on the raw string per line
        cur = ""
        cur_plain = ""
        tokens = r.split(" ")
        ptxt = p.split(" ")
        line = ""
        line_plain = ""
        for t, tp in zip(tokens, ptxt):
            trial = (line_plain + " " + tp).strip()
            if width_of(trial, "B", "", size) > w and line:
                out.append(line)
                line, line_plain = t, tp
            else:
                line = (line + " " + t).strip()
                line_plain = trial
        if line:
            out.append(line)
    return out or [""]


def step(num, title, text, size=10.5, leading=15.2):
    """Numbered step with a red disc badge."""
    pdf.set_font("D", "B", 11.6)
    th = pdf.multi_cell(CW - 28, 15, title, dry_run=True,
                        output=MethodReturnValue.HEIGHT)
    pdf.set_font("B", "", size)
    bh = pdf.multi_cell(CW - 28, leading, text, markdown=True, dry_run=True,
                        output=MethodReturnValue.HEIGHT)
    if pdf.get_y() + th + 2.5 + bh + 9 > BOT and (th + bh + 12) < (BOT - TOP):
        new_page(pdf.chapter)
    y0 = pdf.get_y()
    r = 9.5
    pdf.set_fill_color(*RED)
    pdf.ellipse(M + 1, y0 + 1.5, 2 * r, 2 * r, "F")
    pdf.set_font("U", "BB", 10.5)
    pdf.set_text_color(*PAPER)
    pdf.set_xy(M + 1, y0 + 1.5 + (2 * r - 13) / 2)
    pdf.cell(2 * r, 13, str(num), align="C")
    pdf.set_font("D", "B", 11.6)
    pdf.set_text_color(*INK)
    pdf.set_xy(M + 2 * r + 9, y0)
    pdf.multi_cell(CW - 2 * r - 9, 15, title, new_x="LEFT", new_y="NEXT")
    space(2.5)
    pdf.set_font("B", "", size)
    pdf.set_text_color(*INK2)
    pdf.set_x(M + 2 * r + 9)
    pdf.multi_cell(CW - 2 * r - 9, leading, text, markdown=True,
                   new_x="LEFT", new_y="NEXT")
    space(7)


def ing(amount, item, note="", size=10.2, leading=14.4):
    """Ingredient row: item (bold) ... dotted leader ... amount (right)."""
    ensure(leading + 4)
    pdf.set_font("U", "B", 8.6)
    pdf.set_text_color(*RED)
    amt_w = max(pdf.get_string_width(amount) + 6, 40)
    pdf.set_font("B", "B", size)
    item_w = CW - amt_w - 20
    y0 = pdf.get_y()
    pdf.set_xy(M, y0)
    pdf.multi_cell(item_w, leading, item, markdown=True, new_x="LEFT",
                   new_y="NEXT")
    y1 = pdf.get_y()
    # dotted leader on the first line only
    used = min(pdf.get_string_width(item.replace("**", "")), item_w)
    lead_w = max(0.0, min(amt_w + 12, W - M - 4 - (M + used + 5)))
    pdf.set_font("U", "", 8.6)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(M + used + 5, y0)
    pdf.cell(lead_w, leading, ". . . . . . . . . . . . . . . . . . . . . . . ",
             align="L")
    pdf.set_font("U", "B", 8.6)
    pdf.set_text_color(*RED)
    pdf.set_xy(W - M - amt_w, y0)
    pdf.cell(amt_w, leading, amount, align="R")
    if note:
        pdf.set_font("B", "I", 9.2)
        pdf.set_text_color(*MUTED)
        pdf.set_x(M + 12)
        pdf.multi_cell(CW - 12, 12.6, note, new_x="LEFT", new_y="NEXT")
    pdf.set_y(y1)


def box(title, lines, tint=CREAM, edge=LINE, title_color=RED, size=10.0,
        leading=14.2, gap_before=7):
    space(gap_before)
    pad = 9
    inner = CW - 2 * pad
    pdf.set_font("B", "", size)
    # estimate height
    hlines = 0
    for ln in lines:
        hlines += len(_wrap(ln, inner, size))
    total = (18 if title else 6) + hlines * leading + 2 * pad
    ensure(min(total, BOT - TOP))
    y0 = pdf.get_y()
    pdf.set_fill_color(*tint)
    pdf.set_draw_color(*edge)
    pdf.set_line_width(0.8)
    pdf.rect(M, y0, CW, total, style="DF")
    y = y0 + pad
    if title:
        pdf.set_font("U", "BB", 9.4)
        pdf.set_text_color(*title_color)
        pdf.set_xy(M + pad, y)
        pdf.cell(inner, 12, title.upper())
        y += 17
    for ln in lines:
        for seg in _wrap(ln, inner, size):
            pdf.set_font("B", "", size)
            pdf.set_text_color(*INK2)
            pdf.set_xy(M + pad, y)
            pdf.multi_cell(inner, leading, seg, markdown=True, new_x="LEFT",
                           new_y="NEXT")
            y = pdf.get_y()
    pdf.set_y(y0 + total + 10)


def caption(text):
    pdf.set_font("B", "I", 8.6)
    pdf.set_text_color(*MUTED)
    pdf.set_x(M)
    pdf.multi_cell(CW, 11.6, text, align="C", new_x="LEFT", new_y="NEXT")
    space(7)


def image(key, width=CW, cap="", align="C", border=True, x=None):
    path = IMAGES[key]
    h = width * img_ratio(key)
    ensure(h + 22)
    x0 = M if x is None else x
    if align == "C":
        x0 = M + (CW - width) / 2
    elif align == "R":
        x0 = W - M - width
    if border:
        pdf.set_fill_color(*CREAM)
        pdf.rect(x0 - 5, pdf.get_y() - 5, width + 10, h + 10, style="F")
        pdf.set_draw_color(*LINE)
        pdf.set_line_width(0.8)
        pdf.rect(x0 - 5, pdf.get_y() - 5, width + 10, h + 10, style="D")
    pdf.image(path, x=x0, y=pdf.get_y(), w=width, h=h)
    pdf.set_y(pdf.get_y() + h + (8 if border else 0))
    if cap:
        caption(cap)


def duo(key_a, key_b, cap="", gap=14, w=None):
    """Two images side by side, equal width, equal height (cropped to fit)."""
    if w is None:
        w = (CW - gap) / 2
    ra, rb = img_ratio(key_a), img_ratio(key_b)
    h = w * max(ra, rb)
    ensure(h + 26)
    y0 = pdf.get_y()
    for i, (k, x) in enumerate(((key_a, M), (key_b, M + w + gap))):
        hh = w * img_ratio(k)
        yy = y0 + (h - hh) / 2
        pdf.set_fill_color(*CREAM)
        pdf.rect(x - 4, y0 - 4, w + 8, h + 8, style="F")
        pdf.set_draw_color(*LINE)
        pdf.set_line_width(0.8)
        pdf.rect(x - 4, y0 - 4, w + 8, h + 8, style="D")
        pdf.image(IMAGES[k], x=x, y=yy, w=w, h=hh)
    pdf.set_y(y0 + h + 14)
    if cap:
        caption(cap)


def contents_row(num, title, page):
    ensure(20)
    pdf.set_font("U", "B", 8.4)
    pdf.set_text_color(*RED)
    pdf.set_x(M)
    pdf.cell(20, 14, num, align="L")
    pdf.set_font("B", "", 10.6)
    pdf.set_text_color(*INK)
    pdf.set_xy(M + 22, pdf.get_y())
    tw = pdf.get_string_width(title)
    pdf.cell(tw + 6, 14, title, align="L")
    pdf.set_font("U", "", 8.6)
    pdf.set_text_color(*MUTED)
    x = M + 28 + tw
    pw = pdf.get_string_width(page) + 6
    pdf.set_xy(x, pdf.get_y())
    pdf.cell(max(0.0, W - M - 4 - x - pw), 14,
             ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ",
             align="L")
    pdf.set_font("U", "B", 9)
    pdf.set_text_color(*INK)
    pdf.set_xy(W - M - pw, pdf.get_y())
    pdf.cell(pw, 14, page, align="R")
    pdf.set_y(pdf.get_y() + 14)


# ------------------------------------------------------- vector illustrations
def chile_icon(x, y, length, color=RED, wid=3.4, curve=0.30, stem=True):
    """A little hand-drawn-looking chile pepper."""
    pts = []
    n = 16
    for i in range(n + 1):
        t = i / n
        sx = x + t * length
        sy = y + wid + curve * length * math.sin(math.pi * t) * 0.30
        w = wid * (math.sin(math.pi * (t * 0.86 + 0.07)) ** 0.55) * (1 - 0.35 * t)
        pts.append((sx, sy - w))
    for i in range(n, -1, -1):
        t = i / n
        sx = x + t * length
        sy = y + wid + curve * length * math.sin(math.pi * t) * 0.30
        w = wid * (math.sin(math.pi * (t * 0.86 + 0.07)) ** 0.55) * (1 - 0.35 * t)
        pts.append((sx, sy + w))
    pdf.set_fill_color(*color)
    pdf.polygon(pts, style="F")
    if stem:
        pdf.set_draw_color(*GREEN)
        pdf.set_line_width(1.5)
        pdf.line(x, y + wid, x - length * 0.13, y - wid * 0.5)


def draw_pot(x, y, w, h):
    """Cross-section of a Dutch oven: fat cap, consomme, meat, bones."""
    lid_h = 16
    body_y = y + lid_h
    body_h = h - lid_h
    # pot body
    pdf.set_fill_color((62, 56, 52))
    pdf.set_draw_color((42, 32, 27))
    pdf.set_line_width(1.4)
    r = 16
    pdf.rect(x, body_y, w, body_h, style="F")  # base body
    # rounded bottom corners via ellipse fill
    pdf.set_fill_color((62, 56, 52))
    pdf.ellipse(x, body_y + body_h - r, 2 * r, 2 * r, "F")
    pdf.ellipse(x + w - 2 * r, body_y + body_h - r, 2 * r, 2 * r, "F")
    # liquid: consomme deep red
    liq_top = body_y + body_h * 0.16
    pdf.set_fill_color((150, 40, 28))
    pdf.set_draw_color((120, 30, 22))
    pdf.set_line_width(0.8)
    pdf.rect(x + 6, liq_top, w - 12, body_y + body_h - liq_top - 6, style="F")
    # fat cap (ochre-red layer floating on top)
    pdf.set_fill_color((214, 128, 52))
    pdf.rect(x + 6, liq_top, w - 12, 9, style="F")
    # meat chunks (irregular brown-red blobs)
    for cx, cy, rw, rh in [(0.22, 0.42, 34, 22), (0.47, 0.36, 40, 24),
                           (0.72, 0.44, 32, 21), (0.33, 0.62, 38, 23),
                           (0.60, 0.66, 36, 22), (0.86, 0.63, 26, 20)]:
        mx = x + 6 + (w - 12) * cx
        my = liq_top + 14 + (body_y + body_h - liq_top - 24) * cy
        pdf.set_fill_color((120, 58, 44))
        pdf.ellipse(mx - rw / 2, my - rh / 2, rw, rh, "F")
        pdf.set_fill_color((150, 76, 56))
        pdf.ellipse(mx - rw / 2 + 3, my - rh / 2 + 2.5, rw - 8, rh - 7, "F")
    # bones with marrow
    for bx, by, bwid in [(0.12, 0.78, 30), (0.50, 0.86, 34), (0.84, 0.84, 28)]:
        cx = x + 6 + (w - 12) * bx
        cy = liq_top + 14 + (body_y + body_h - liq_top - 24) * by
        pdf.set_fill_color((236, 226, 208))
        pdf.ellipse(cx - bwid / 2, cy - 8, bwid, 16, "F")
        pdf.set_fill_color((198, 90, 60))
        pdf.ellipse(cx - bwid / 2 + 4, cy - 4, bwid - 8, 8, "F")
    # lid
    pdf.set_fill_color((78, 70, 64))
    pdf.set_draw_color((42, 32, 27))
    pdf.set_line_width(1.2)
    pdf.rect(x - 8, y + 8, w + 16, 9, style="DF")
    pdf.ellipse(x + w / 2 - 13, y - 1, 26, 11, "F")
    # steam
    pdf.set_draw_color((190, 170, 150))
    pdf.set_line_width(1.1)
    for sx in (0.28, 0.5, 0.72):
        px = x + w * sx
        py = y - 2
        for k in range(3):
            pdf.line(px, py - k * 7, px + 5 * (1 if k % 2 == 0 else -1), py - k * 7 - 6)


def draw_pot_labels(x, y, w, h):
    """Leader-line labels for the cross-section."""
    items = [
        (0.055, "**Fat cap** — the red-orange oil that rises. Skim it; this is what you griddle the tortillas in."),
        (0.22, "**Consomme** — the broth. Season it boldly; it gets drunk as much as sipped."),
        (0.50, "**Meat** — 3/4 submerged so the top browns and concentrates."),
        (0.78, "**Bones** — shank, oxtail or short rib. Gelatin = body."),
    ]
    pdf.set_font("B", "", 9.2)
    for frac, txt in items:
        ty = y + h * frac
        pdf.set_draw_color(*MUTED)
        pdf.set_line_width(0.7)
        pdf.line(x + w + 4, ty, x + w + 16, ty)
        pdf.set_fill_color(*INK)
        pdf.ellipse(x + w + 2, ty - 1.6, 3.2, 3.2, "F")
        pdf.set_xy(x + w + 20, ty - 6)
        pdf.set_text_color(*INK2)
        pdf.multi_cell(CW - (x + w + 20 - M), 12.4, txt, markdown=True,
                       new_x="LEFT", new_y="NEXT")


def heat_meter(x, y, w, rows, maxv=30000):
    pdf.set_font("U", "B", 8.4)
    rowh = 21
    ensure(len(rows) * rowh + 24)
    for label, val, note in rows:
        pdf.set_xy(x, y)
        pdf.set_text_color(*INK)
        pdf.set_font("B", "B", 9.6)
        pdf.cell(96, 12, label)
        bar_x = x + 100
        bar_w = w - 100 - 62
        frac = min(val / maxv, 1.0)
        pdf.set_fill_color((238, 226, 204))
        pdf.rect(bar_x, y + 2.5, bar_w, 8, "F")
        # gradient-ish: draw segments
        segs = 26
        for i in range(segs):
            if i / segs > frac:
                break
            t = i / segs
            col = (int(214 - 40 * t), int(150 - 100 * t), int(60 - 30 * t))
            pdf.set_fill_color(*col)
            pdf.rect(bar_x + i * (bar_w / segs), y + 2.5, bar_w / segs + 0.6, 8, "F")
        pdf.set_font("U", "", 8.2)
        pdf.set_text_color(*MUTED)
        pdf.set_xy(x + w - 58, y)
        pdf.cell(58, 12, note, align="R")
        y += rowh
    pdf.set_y(y + 2)


def fold_panel(x, y, s, kind, num):
    """One panel of the quesabirria assembly sequence."""
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.9)
    pdf.set_fill_color((250, 244, 232))
    pdf.rect(x, y, s, s, style="DF")
    cx, cy = x + s / 2, y + s / 2 + 2
    r = s * 0.33
    if kind in ("tortilla", "cheese", "meat", "fold"):
        pdf.set_fill_color((226, 190, 128))
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, "F")
        pdf.set_draw_color((198, 158, 96))
        pdf.set_line_width(0.7)
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, "D")
        for i in range(4):
            a = i * 0.9 + 0.4
            pdf.set_fill_color((206, 166, 104))
            pdf.ellipse(cx + math.cos(a) * r * 0.45 - 3,
                        cy + math.sin(a) * r * 0.5 - 2.5, 6, 5, "F")
    if kind in ("cheese", "meat", "fold", "griddle"):
        pdf.set_fill_color((242, 226, 176))
        pdf.rect(cx - r * 0.9, cy - r * 0.42, r * 1.8, r * 0.84, "F")
    if kind in ("meat", "fold", "griddle"):
        pdf.set_fill_color((138, 52, 40))
        for dx, dy, rr in [(-0.45, -0.1, 9), (0.0, -0.2, 11), (0.45, -0.05, 8),
                           (-0.2, 0.12, 8), (0.3, 0.14, 9), (0.05, 0.02, 10)]:
            pdf.ellipse(cx + dx * r - rr / 2, cy + dy * r - rr / 2, rr, rr * 0.8, "F")
    if kind == "fold":
        pdf.set_fill_color((250, 244, 232))
        pdf.rect(cx, y + 2, s / 2, s - 4, "F")
        pdf.set_fill_color((226, 160, 96))
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, "F")
        pdf.set_draw_color((186, 106, 62))
        pdf.set_line_width(1.3)
        # crease along the fold (vertical diameter of the tortilla)
        pdf.line(cx, cy - r, cx, cy + r)
        pdf.set_fill_color((242, 226, 176))
        pdf.rect(cx - r * 0.9, cy - r * 0.42, r * 0.9, r * 0.84, "F")
        pdf.set_fill_color((138, 52, 40))
        for dx, dy, rr in [(-0.62, -0.1, 8), (-0.3, -0.2, 9), (-0.05, 0.0, 8)]:
            pdf.ellipse(cx + dx * r - rr / 2, cy + dy * r - rr / 2, rr, rr * 0.8, "F")
        pdf.set_fill_color((250, 244, 232))
    if kind == "griddle":
        pdf.set_fill_color((176, 96, 58))
        pdf.ellipse(x + s * 0.18, y + s - 12, s * 0.64, 12, "F")
        pdf.set_draw_color(*RED)
        pdf.set_line_width(1.2)
        for i in range(3):
            pdf.line(x + s * 0.3 + i * s * 0.2, y + s - 14,
                     x + s * 0.3 + i * s * 0.2 + 4, y + s - 22)
    # number badge
    pdf.set_fill_color(*RED)
    pdf.ellipse(x + 5, y + 5, 15, 15, "F")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*PAPER)
    pdf.set_xy(x + 5, y + 5)
    pdf.cell(15, 15, str(num), align="C")


def timeline(x, y, w, rows):
    """Horizontal bars: method vs. hours (unattended cook)."""
    lab_w = 108
    bar_w = w - lab_w - 54
    maxv = max(v for _, v, _ in rows)
    pdf.set_font("B", "B", 9.4)
    rowh = 20
    ensure(len(rows) * rowh + 22)
    for label, val, note in rows:
        pdf.set_xy(x, y)
        pdf.set_text_color(*INK)
        pdf.cell(lab_w, 13, label)
        bx = x + lab_w
        frac = val / maxv
        pdf.set_fill_color((238, 226, 204))
        pdf.rect(bx, y + 3, bar_w, 9, "F")
        segs = int(bar_w / 5)
        for i in range(segs):
            if i / segs > frac:
                break
            t = i / segs
            pdf.set_fill_color((int(198 - 40 * t), int(96 - 40 * t), int(56 - 20 * t)))
            pdf.rect(bx + i * 5, y + 3, 5.6, 9, "F")
        pdf.set_font("U", "B", 8.6)
        pdf.set_text_color(*RED)
        pdf.set_xy(x + w - 50, y)
        pdf.cell(50, 13, note, align="R")
        y += rowh
    pdf.set_y(y + 2)


# ============================================================================
#                                  THE BOOK
# ============================================================================

# ------------------------------------------------------------------- 1. COVER
def build_cover():
    pdf.cover_mode = True
    pdf.add_page()
    pdf.set_fill_color(*PAPER)
    pdf.rect(0, 0, W, H, style="F")

    # outer frame
    pdf.set_draw_color(*RED)
    pdf.set_line_width(2.2)
    pdf.rect(24, 24, W - 48, H - 48, style="D")
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.7)
    pdf.rect(31, 31, W - 62, H - 62, style="D")

    # kicker
    y = 58
    pdf.set_font("U", "BB", 8.6)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(M, y)
    pdf.cell(CW, 12, "A SHORT, ILLUSTRATED FIELD GUIDE", align="C")

    # cover art, framed
    iw = 342
    ih = iw  # square crop
    x0 = (W - iw) / 2
    y0 = 80
    pdf.set_fill_color(*CREAM)
    pdf.rect(x0 - 9, y0 - 9, iw + 18, ih + 18, style="F")
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(1.0)
    pdf.rect(x0 - 9, y0 - 9, iw + 18, ih + 18, style="D")
    pdf.image(IMAGES["cover_sq"], x=x0, y=y0, w=iw, h=ih)

    y = y0 + ih + 34
    pdf.set_font("D", "BB", 46)
    pdf.set_text_color(*RED)
    pdf.set_xy(M - 6, y)
    pdf.cell(CW + 12, 46, "Tijuana Birria", align="C")
    y += 50
    pdf.set_font("D", "I", 14)
    pdf.set_text_color(*INK2)
    pdf.set_xy(M, y)
    pdf.cell(CW, 19, "Red tacos, consomme, and the meat that makes them",
             align="C")

    # ornament
    y += 32
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.9)
    pdf.line(M + 60, y, W / 2 - 26, y)
    pdf.line(W / 2 + 26, y, W - M - 60, y)
    pdf.set_fill_color(*RED)
    for cx, s in ((W / 2 - 12, 5), (W / 2, 7), (W / 2 + 12, 5)):
        pdf.polygon([(cx, y - s), (cx + s, y), (cx, y + s), (cx - s, y)],
                    style="F")

    y += 26
    pdf.set_font("U", "B", 8.8)
    pdf.set_text_color(*INK)
    pdf.set_xy(M, y)
    pdf.cell(CW, 13, "THE CUTS  -  THE CHILES  -  THE BRAISE  -  THE TACOS",
             align="C")

    # chile row along the bottom
    yb = H - 108
    total = 5 * 46
    sx = (W - total) / 2 + 6
    cols = [(166, 46, 30), (150, 62, 34), (138, 52, 40), (196, 92, 40),
            (166, 46, 30)]
    for i, c in enumerate(cols):
        chile_icon(sx + i * 46 - 14, yb, 34, c, wid=4.2)
    pdf.set_font("B", "I", 8.6)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(M, H - 78)
    pdf.cell(CW, 12, "19 pages  -  10 painted plates  -  one very long nap",
             align="C")
    pdf.cover_mode = False


# --------------------------------------------------------------- 2. CONTENTS
def build_contents():
    new_page("Contents")
    pdf.set_font("D", "BB", 30)
    pdf.set_text_color(*INK)
    pdf.set_xy(M, TOP + 4)
    pdf.cell(CW, 34, "Contents", align="L")
    space(24)
    rule(1.0, RED)
    space(12)
    rows = [
        ("1.", "What Tijuana birria is (and isn't)", "3"),
        ("2.", "The meat: the cuts that matter", "4"),
        ("3.", "Chiles, spices and aromatics", "6"),
        ("4.", "Where to buy it", "8"),
        ("5.", "Equipment", "10"),
        ("6.", "Master recipe: birria de res", "11"),
        ("7.", "Quesabirria: how to build one", "15"),
        ("8.", "Salsa, toppings, sides", "16"),
        ("9.", "The day after", "17"),
        ("10.", "Troubleshooting", "18"),
        ("11.", "Numbers and notes", "19"),
    ]
    for n, t, p in rows:
        contents_row(n, t, p)
    space(10)
    box("Read this first", [
        "Birria is a braise, not a race. Everything in this book hangs on three things: **dried chiles you toast yourself**, **at least one bone-in cut**, and **salt added at the end, not the start**. Get those right and the rest is negotiable.",
        "Every recipe is written for **5 lb (2.3 kg) of beef**, which feeds 6-8 people as tacos with consomme, or 4 people with heroic leftovers.",
    ])


# -------------------------------------------------------- 3. WHAT IT IS
def build_intro():
    new_page("What it is")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER ONE")
    space(22)
    h1("What Tijuana birria is\n(and isn't)")
    lead("Birria was born in Jalisco, and it was born with **goat**. A whole "
         "chivo rubbed in chile adobo and slow-cooked until it gives up. "
         "Tijuana kept the adobo and changed the animal.")
    para("Up north, goat is expensive and hard to get in volume, so Tijuana "
         "birrierias went to **beef** - birria de res - built around chuck, "
         "shank and bone. Around 2009, the food writer Bill Esparza started "
         "seeing that birria folded into tacos at a Tijuana truck called "
         "**Tacos Aaron**. Other trucks added cheese. Tijuana taqueros carried "
         "the style to Los Angeles around 2016, and Instagram turned it into "
         "the most photographed taco on earth.")
    h3("THE FOUR RULES OF TIJUANA BIRRIA", before=6)
    bullet("**Beef, in two parts.** One fatty working cut (chuck) plus one "
           "bone-in, collagen-heavy cut (shank, oxtail, short rib). The first "
           "feeds you; the second makes the consomme.", marker="chile")
    bullet("**A guajillo-forward adobo.** Brick red, toasted, tangy with "
           "vinegar, warm with canela and clove. It is not smoky and it is not "
           "a chipotle braise.", marker="chile")
    bullet("**Cooked in its own broth.** Birria makes two products: the meat "
           "and the consomme. One without the other is just shredded beef.",
           marker="chile")
    bullet("**Served on a griddled tortilla** dipped in the red fat off the "
           "braise, with cheese melted in and a cup of consomme for dunking.",
           marker="chile")
    ornament()
    box("The three things that matter most", [
        "**1. Toast your own chiles.** Pre-ground powder is dull. Twenty seconds in a dry pan is the biggest flavour upgrade available to you.",
        "**2. Buy bones.** Shank, oxtail, short ribs. Gelatin is what makes the consomme coat a spoon.",
        "**3. Season at the end.** Reduce, then salt. A braise that tastes right before reducing will taste like seawater after.",
    ], tint=(250, 238, 224))


# ------------------------------------------------------------ 4-5. THE MEAT
# ------------------------------------------------------------ 4-5. THE MEAT
def build_meat():
    new_page("The meat")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER TWO")
    space(20)
    h1("The meat")
    lead("**The formula: 60% meaty, fatty cut + 40% bone-in, collagen-heavy "
         "cut.** The meat is dinner; the bones are the consomme. Buy both.")
    image("cuts", 300, "The working five: chuck, cross-cut shank, bone-in "
          "short ribs, oxtail, beef cheek. Ask for them by the Spanish name "
          "and the butcher takes you seriously.")
    cuts = [
        ("Beef chuck roast", "aguja / diezmillo",
         "The backbone of the braise: marbled, collagen-rich, shreds juicy. "
         "Buy a whole roast and cut 3-4 in chunks yourself - pre-cut 'stew "
         "meat' is a lottery.",
         "Cheapest at Costco, Smart & Final, WinCo, Food 4 Less."),
        ("Beef shank, cross-cut", "chamorro / chambarete",
         "The most important cut for the consomme: rounds about 1.5 in thick, "
         "each with a ring of bone and a plug of marrow. Do not skip it.",
         "Any carniceria; H-E-B, Northgate, Vallarta, Walmart."),
        ("Beef short ribs, bone-in", "costillas de res",
         "The splurge: English-cut (thick, on the bone), not flanken. Fat, "
         "bone and a deeper, beef-tea flavour.",
         "Costco and Sam's, cheap in cryovac packs."),
        ("Oxtail", "rabo / cola de res",
         "Old-school consomme booster: almost no meat, enormous gelatin. One "
         "pound changes the mouthfeel of the whole pot.",
         "99 Ranch, H Mart, Mexican markets (often frozen)."),
        ("Beef cheeks", "cachete de res",
         "What many Tijuana birrierias actually use: silky, collagen-dense, "
         "stays moist longer than chuck. You have to ask for it.",
         "Carnicerias only: 'Tiene cachete de res?'"),
    ]
    for name, es, why, where in cuts:
        ensure(74)
        pdf.set_font("D", "B", 11.2)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW - 150, 13.5, name)
        pdf.set_font("B", "I", 9.3)
        pdf.set_text_color(*MUTED)
        pdf.set_xy(W - M - 150, pdf.get_y())
        pdf.cell(150, 13.5, es, align="R")
        space(13.8)
        para(why, size=9.9, leading=13.8, color=INK2, gap_after=2.5)
        pdf.set_font("U", "B", 8.2)
        pdf.set_text_color(*GREEN)
        pdf.set_x(M)
        pdf.cell(CW, 10.5, "WHERE: " + where)
        space(10)

    new_page("The meat")
    h2("Good to excellent, optional", size=13.5)
    bullet("**Brisket point (pecho).** Fatty and forgiving; shreds like a "
           "dream. The point, not the flat, or it dries out.", marker="dot")
    bullet("**Goat (chivo).** The Jalisco original: shoulder and ribs, same "
           "adobo, gamier and leaner. Order from a Mexican or Halal butcher "
           "a week ahead.", marker="dot")
    bullet("**Lamb shoulder (borrego).** The middle road - richer than beef, "
           "milder than goat.", marker="dot")
    bullet("**Beef fat trimmings (grasa de res).** Ask for a handful; many "
           "carnicerias hand them over. Render them and you have unlimited "
           "taco fat.", marker="dot")
    space(3)
    box("Do not buy these for birria", [
        "**Pre-cut 'stew meat'** - round and trim scraps, cut small; dries out before it tenderises.",
        "**Eye of round, top round, rump, sirloin** - lean, no collagen, no marrow. Tough at hour one, dry at hour four.",
        "**Anything pre-seasoned** - you're about to marinate it yourself for eight hours.",
    ], tint=(250, 232, 226), title_color=(150, 40, 28))
    space(2)
    h2("How to order it, in Spanish", size=13.5)
    para("You need four sentences and a smile. Carniceros will cut shank to "
         "order and save you cheeks if you ask nicely.", size=9.9, leading=13.8,
         color=INK2, gap_after=5)
    for s, t in [
        ("\"Un trozo de aguja de tres libras, por favor.\"",
         "A three-pound piece of chuck roast, please."),
        ("\"Dos libras de chamorro, cortado para cocido.\"",
         "Two pounds of shank, cross-cut for stew."),
        ("\"Tiene cachete de res?\"", "Do you have beef cheeks?"),
        ("\"Me regala un poco de grasa de res?\"",
         "Could you give me a little beef fat?"),
    ]:
        ensure(28)
        pdf.set_font("B", "B", 10)
        pdf.set_text_color(*INK)
        pdf.set_x(M)
        pdf.multi_cell(CW, 13.5, s, new_x="LEFT", new_y="NEXT")
        pdf.set_font("B", "I", 9.3)
        pdf.set_text_color(*MUTED)
        pdf.set_x(M)
        pdf.multi_cell(CW, 12, t, new_x="LEFT", new_y="NEXT")
        space(2.5)


# ------------------------------------------------------------ 6. THE CHILES
def build_chiles():
    new_page("The chiles")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER THREE")
    space(20)
    h1("The chiles")
    lead("Birria is red because of **guajillo**. House ratio: **6 guajillo : "
         "2 ancho : 1 pasilla** plus 3-6 arbol - by weight, 50 / 20 / 10 / 3 "
         "g. Weight never lies.")
    image("chiles", 224, "Left to right: guajillo (bright, smooth, the "
          "workhorse), ancho (dark, wrinkled, raisiny), pasilla (long, almost "
          "black) and chile de arbol (small and hot).")
    ch = [
        ("Guajillo", "Thin-walled, glossy, brick red, faintly sour and "
         "tea-like. Gives birria its colour and brightness. Flat, brown "
         "birria = too little guajillo."),
        ("Ancho", "A dried poblano: wide, wrinkled, mahogany. Prunes, "
         "tobacco, a little cocoa. The roundness and 'stewed-all-day' depth."),
        ("Pasilla / chile negro", "Long, thin, near-black. Deep and "
         "slightly bitter, like dark chocolate. One gives a long finish; "
         "three turns medicinal."),
        ("Chile de arbol", "Small, slender, genuinely hot. Your heat dial "
         "and the only one to turn. Three = family. Six = Tijuana truck."),
        ("Morita / chipotle", "Smoked. One at most, or skip it. Tijuana "
         "birria is bright and tangy, not smoky."),
    ]
    for n, d in ch:
        ensure(50)
        pdf.set_font("D", "B", 11)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW, 13.5, n)
        space(13.8)
        para(d, size=9.9, leading=13.8, color=INK2, indent=10, gap_after=4.5)
    space(1)
    box("Buying dried chiles like a taquero", [
        "**They should bend, not snap** - brittle chiles are old and taste like paper. Look for glossy pods; smell the bag: raisins, tea, dried fruit. Nothing smelling like nothing tastes like something.",
        "**Buy whole, never pre-ground**, and by the pound at a Mexican market - a third of the supermarket price and far fresher.",
    ])

    # ---- continuation page: spices and aromatics
    new_page("The chiles")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER THREE  -  CONTINUED")
    space(20)
    h1("Spices and aromatics")
    para("The paste is the voice; these are the backing band. Whole spices "
         "get 30-60 seconds in a dry pan until they smell loud.", size=10,
         leading=14, color=INK2, gap_after=3)
    duo("aromatics", "spices",
        "Fresh aromatics: garlic, onion, tomato, ginger.  /  Toasted whole "
        "spices: cumin, pepper, cloves, canela, oregano.", w=172)
    sp = [
        ("Canela (Mexican cinnamon), 1 stick",
         "Softer and more floral than cassia - the background warmth of the "
         "pot. Don't leave it out; don't double it."),
        ("Whole cloves, 4-6",
         "Clove plus canela is the smell nobody can place. Four is a "
         "whisper; ten is mulled wine."),
        ("Cumin seed, 1 tsp + peppercorns, 1 tsp, toasted",
         "Birria is cumin-forward, not cumin-dominated - that's the "
         "difference between birria and chili."),
        ("Mexican oregano, 2 tsp",
         "Not Mediterranean - citrusy, grassy, verbena family. Crush it in "
         "your palm."),
        ("Dried thyme, 1 tsp + marjoram, 1/2 tsp + 4 bay leaves",
         "The herbal backbone. Bay: two into the paste, two into the pot - "
         "fish them out before serving."),
        ("Dried ginger, 1/2 tsp",
         "Almost nobody lists it; every good birrieria uses it - the high "
         "note that keeps a heavy braise from tasting flat."),
        ("Vinegar, 1/4 cup cider or white",
         "The Tijuana signature - the tang that cuts the fat. Into the soak "
         "water; a splash more at the end if needed."),
    ]
    for s, d in sp:
        ensure(42)
        pdf.set_font("D", "B", 10.6)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW, 13, s)
        space(13.2)
        para(d, size=9.7, leading=13.4, color=INK2, indent=10, gap_after=3)

    h3("THE AROMATICS", before=3)
    bullet("**Garlic, 8-10 cloves, unpeeled.** Char until the skins "
           "blacken in spots, then peel - charred is sweet, raw is sharp.")
    bullet("**White onion, 1.** Half into the paste raw, half diced for "
           "topping. Never yellow in the paste - too sweet.")
    bullet("**Roma tomatoes, 3.** Charred until blistered - body, sweetness, "
           "acid. Crushed canned tomato works in a pinch.")


# ---------------------------------------------------------- 8-9. SHOPPING
def build_shopping():
    new_page("Where to buy it")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER FOUR")
    space(20)
    h1("Where to buy it")
    lead("You can make excellent birria from a single big-box supermarket. "
         "You'll make *better, cheaper* birria by buying chiles, bones and "
         "tortillas somewhere else. If it isn't out, ask - meat counters cut "
         "shank to order almost everywhere.")
    image("market", 205, "A carniceria counter is not intimidating once you "
          "know four words: aguja, chamorro, cachete, hueso.")
    h2("Big national chains", size=13.5)
    stores = [
        ("Costco / Sam's Club", "$",
         "Best price on chuck and short ribs; big bags of guajillo and "
         "ancho. No shank, oxtail or cheeks usually."),
        ("Walmart", "$",
         "The most complete one-stop: chuck, shank, short ribs, often oxtail, "
         "plus chiles, canela and tortillas in the Hispanic aisle."),
        ("Kroger family (Ralphs, Fred Meyer, Smith's...)", "$$",
         "Strong meat counters, reliable oxtail and short ribs, dried chiles "
         "in the international aisle."),
        ("Albertsons / Vons / Safeway / Jewel-Osco", "$$",
         "Butchers cut the shank; Goya chiles and Oaxaca cheese in many "
         "stores."),
        ("H-E-B / H-E-B Mi Tienda", "$",
         "The best big-chain birria store in America: in-house carniceria, "
         "pre-cut chamorro, oxtail, bulk chiles, own tortilleria."),
        ("Smart & Final", "$",
         "Underrated: 10 lb boxes of guajillo, cryovac chuck, oxtail, canela "
         "by the sleeve. Where small taquerias shop."),
        ("WinCo / Food 4 Less / Save A Lot", "$",
         "Cheapest chuck, onion and garlic; WinCo's bulk bins sell spices for "
         "pennies. Thin on chiles."),
        ("Trader Joe's / Sprouts / Whole Foods / Publix / Target", "$$-$$$",
         "TJ's and Target have no butcher counter but good tortillas, cheese "
         "and chiles; Sprouts, Whole Foods and Publix have great meat and "
         "spice bins, pricey chiles, special orders."),
    ]
    for name, price, note in stores:
        ensure(56)
        pdf.set_font("D", "B", 10.8)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW - 30, 13, name)
        pdf.set_font("U", "BB", 9)
        pdf.set_text_color(*GREEN)
        pdf.set_xy(W - M - 30, pdf.get_y())
        pdf.cell(30, 13, price, align="R")
        space(13.2)
        para(note, size=9.7, leading=13.4, color=INK2, indent=10, gap_after=3.5)

    new_page("Where to buy it")
    h2("Mexican and Latino markets: go if you have one", size=13.5)
    para("This is where birria actually gets bought. Chiles by the pound at a "
         "third of the price, shank already cross-cut, oxtail, cachete, free "
         "beef fat, tortillas made that morning.", size=9.9, leading=13.8,
         color=INK2, gap_after=4)
    bullet("**Northgate Market** (CA, TX): full carniceria, great chile wall, "
           "tortilleria in store.", marker="dot")
    bullet("**Vallarta, El Super, Cardenas, Superior Grocers, La Michoacana** "
           "(CA, NV, AZ, TX): the standard Southern California birria run.",
           marker="dot")
    bullet("**Fiesta Mart** (TX), **Sedano's** (FL), **Bravo, Compare "
           "Foods**: same idea, different coasts.", marker="dot")
    bullet("**99 Ranch, H Mart, Zion and other Asian markets**: the best "
           "oxtail in town - cheaper, thicker-cut, usually fresh not frozen.",
           marker="dot")
    space(2)
    h2("Cheese and tortillas", size=13.5)
    bullet("**Queso Oaxaca (quesillo)**: the ideal - stringy, mild, browns "
           "beautifully. Any Mexican market; most big chains now.",
           marker="dot")
    bullet("**Queso Chihuahua / menonita**: the northern alternative. Melts "
           "smoother, browns slower.", marker="dot")
    bullet("**Low-moisture whole-milk mozzarella**: what half the LA trucks "
           "actually use. Buy the block and shred it yourself - pre-shredded "
           "is coated in cellulose and will not stretch.", marker="dot")
    bullet("**Corn tortillas, taquera size (about 5 in)**, from a tortilleria "
           "if possible. Guerrero, Mission, La Banderita and El Milagro are "
           "the reliable bags. Warm the stack or they crack.", marker="dot")
    space(2)
    h2("Online, if there's nothing nearby", size=13.5)
    para("Dried chiles travel well and keep for months. Goya, Don Enrique and "
         "El Mexicano bags are on Amazon; MexGrocer and Zocalo Foods are the "
         "specialist grocers - a genuinely good route for guajillo, ancho, "
         "pasilla and canela.", size=9.9, leading=13.8, color=INK2)


# ---------------------------------------------------------- 10. EQUIPMENT
def build_equipment():
    new_page("Equipment")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER FIVE")
    space(20)
    h1("Equipment")
    para("You need one heavy pot and a blender - a $60 enameled Lodge will "
         "outlive you. Everything else is a convenience.", size=10,
         leading=14, color=INK2, gap_after=3)
    image("equipment", 182, "Dutch oven, blender, fine-mesh strainer, tongs, "
          "two forks, comal, ladle, knife.")
    h3("ESSENTIAL", before=2)
    bullet("**7-8 quart Dutch oven**, tight lid. Heavy is the whole point; "
           "a thin pot scorches the paste in the last hour.")
    bullet("**Blender** - a $30 one is fine, you're straining the paste "
           "anyway.")
    bullet("**Fine-mesh strainer** - non-negotiable: the difference "
           "between silky restaurant consomme and gritty home braise.")
    bullet("**A comal, cast-iron skillet or wide pan** for toasting and "
           "griddling - a comal is about $15 - plus tongs and two forks.")
    h3("NICE TO HAVE")
    bullet("**Pressure cooker / Instant Pot.** 45 minutes instead of 3.5 "
           "hours, texture just as good - the best shortcut in this book.")
    bullet("**Slow cooker.** 8-9 hours on low; boil the consomme down 15 "
           "minutes at the end.")
    bullet("**Digital scale, fat separator, mortar and pestle** - scale for "
           "chiles and salt, separator for the fat cap.")
    h3("TIMING, BY METHOD (5 LB OF MEAT)", before=4)
    timeline(M, pdf.get_y(), CW, [
        ("Pressure cooker", 45, "45 min"),
        ("Oven, 300 F", 200, "3 - 3.5 hr"),
        ("Stovetop, low", 220, "3.5 - 4 hr"),
        ("Slow cooker, low", 540, "8 - 9 hr"),
    ])
    caption("Unattended cook time only. Add 30 minutes of prep and 20 of "
            "finishing to every method.")


def ing2col(groups):
    """Two-column ingredient list."""
    colw = (CW - 26) / 2
    rows = []
    for gname, items in groups:
        rows.append(("head", gname, ""))
        for item, amt in items:
            rows.append(("row", item, amt))
    half = (len(rows) + 1) // 2
    cols = [rows[:half], rows[half:]]
    y_start = pdf.get_y()
    max_y = y_start
    for ci, col in enumerate(cols):
        pdf.set_y(y_start)
        x = M + ci * (colw + 26)
        for kind, a, b in col:
            if kind == "head":
                ensure(24)
                pdf.set_font("U", "BB", 8.6)
                pdf.set_text_color(*RED)
                pdf.set_x(x)
                pdf.cell(colw, 12, a.upper())
                space(15)
            else:
                ensure(26)
                pdf.set_font("B", "B", 9.8)
                pdf.set_text_color(*INK)
                pdf.set_x(x)
                pdf.multi_cell(colw, 12.6, a, markdown=True, new_x="LEFT",
                               new_y="NEXT")
                y_after = pdf.get_y()
                pdf.set_font("U", "B", 8.6)
                pdf.set_text_color(*MUTED)
                pdf.set_xy(x, pdf.get_y() - 12.6)
                pdf.cell(colw, 12.6, b, align="R")
                pdf.set_y(y_after)
                space(3.5)
        max_y = max(max_y, pdf.get_y())
    pdf.set_y(max_y)


def build_recipe():
    new_page("Master recipe")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SIX")
    space(22)
    h1("Birria de res")
    para("**Yield:** 12-16 quesabirrias plus about 8 cups of consomme.  "
         "**Active time:** 45 minutes.  **Braise:** 3.5-4 hours (or 45 "
         "minutes under pressure).  **Marinate:** 4 hours to overnight.  "
         "**Feeds:** 6-8.", size=10.2, leading=14.4)
    space(2)
    ing2col([
        ("The meat", [
            ("**Chuck roast** (aguja), in 3-4 in chunks", "3 lb"),
            ("**Beef shank**, cross-cut 1.5 in (chamorro)", "1.5 lb"),
            ("**Bone-in short ribs** or oxtail", "1 lb"),
        ]),
        ("The chiles", [
            ("**Guajillo**, stemmed and seeded", "6"),
            ("**Ancho**, stemmed and seeded", "2"),
            ("**Pasilla**, stemmed and seeded", "1"),
            ("**Chile de arbol**, to taste", "3-6"),
        ]),
        ("Aromatics and spices", [
            ("**Garlic cloves**, unpeeled", "8-10"),
            ("**Roma tomatoes**", "3"),
            ("**White onion**", "1"),
            ("**Canela** (Mexican cinnamon)", "1 stick"),
            ("**Whole cloves**", "4-6"),
            ("**Cumin seed** / **peppercorns**", "1 tsp each"),
            ("**Mexican oregano**", "2 tsp"),
            ("**Dried thyme** + **marjoram**", "1 + 1/2 tsp"),
            ("**Dried ginger**", "1/2 tsp"),
            ("**Bay leaves**", "4"),
            ("**Vinegar**, cider or white", "1/4 cup"),
            ("**Kosher salt**, plus more at the end", "1 tbsp"),
        ]),
        ("To finish and serve", [
            ("**Queso Oaxaca** or mozzarella block", "1 lb"),
            ("**Corn tortillas**, taquera size", "2 dozen"),
            ("**Onion** and **cilantro**, chopped", ""),
            ("**Limes** + **salsa de arbol** (p. 16)", ""),
        ]),
    ])
    space(4)
    box("How to read this recipe", [
        "Four pages: **the shopping list** (this page), **the chile paste**, **marinate and braise**, **consomme and shred**. The paste can be made a day ahead. Total time from nothing to tacos: about 5 hours, most of it unattended.",
    ], tint=(250, 238, 224))

    # ---- step 1
    new_page("Master recipe")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SIX  -  STEP ONE")
    space(22)
    h1("The chile paste")
    para("Thirty minutes of work, ninety percent of the flavour. Do it the "
         "night before to split the job in two.", size=10, leading=14,
         color=INK2, gap_after=3)
    duo("toast", "soak",
        "Toast until fragrant and pliable - never smoking.  /  Then soak "
        "25-30 minutes in hot water and vinegar.", w=168)
    step(1, "Clean the chiles",
         "Snap off the stems, split each chile down one side, shake out the "
         "seeds and pull out the pale veins. **The veins hold most of the "
         "heat** - all out for mild, a few left in for a truck bite.")
    step(2, "Toast them",
         "Dry comal over **medium**. Press each chile flat for **20-30 seconds "
         "a side** until it smells like raisins and warm bread. The moment "
         "you see smoke or a black blister, it's burnt and the pot will be "
         "bitter - throw it out and start again.")
    step(3, "Soak them",
         "Cover the chiles with **2 cups of very hot (not boiling) water** "
         "and the **1/4 cup vinegar**, weight with a plate, soak **25-30 "
         "minutes** until completely soft. Keep the soaking liquid.")
    step(4, "Char the aromatics",
         "On the same comal, blister the **tomatoes** and **unpeeled garlic** "
         "until blackened in spots and slumping, 8-10 minutes. Peel the "
         "garlic; toast the **cumin** for 30 seconds alongside.")
    step(5, "Blend it smooth",
         "Blender: drained chiles, charred tomatoes and garlic, **1 cup "
         "soaking liquid**, half the onion, the cumin, peppercorns, cloves, "
         "canela, oregano, thyme, marjoram, ginger, 2 bay leaves, **1 tbsp "
         "salt**. Blend on high a full **2-3 minutes** - a gritty paste "
         "stays gritty.")
    step(6, "Strain it",
         "Push the paste through a **fine-mesh strainer**, working it with a "
         "ladle. Skins, seeds and fibres stay behind. This feels fussy and it "
         "is the whole difference between home birria and taqueria birria.")

    # ---- step 2 and 3
    new_page("Master recipe")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SIX  -  STEPS TWO AND THREE")
    space(22)
    h1("Marinate, then braise")
    image("blend", 118, "The finished paste: thick, glossy, brick red.",
          align="R")
    h3("STEP TWO: MARINATE  (10 min + 4 hours to overnight)", before=0)
    step(7, "Coat the meat",
         "Pat the meat dry, season with the **1 tbsp salt**, and toss with the "
         "strained paste until every piece is heavily coated. Refrigerate "
         "**at least 4 hours**, ideally overnight, up to 24.")
    h3("STEP THREE: BRAISE  (3.5 to 4 hours)", before=4)
    step(8, "Sear, if you have the patience",
         "Brown the meat in batches in a little oil, 2 minutes a side, "
         "without crowding. Optional, but it adds a roasted depth you can "
         "taste. Skip it in a slow cooker.")
    step(9, "Build the pot",
         "Leftover marinade into the pot with the rest of the soaking liquid "
         "plus enough **water or broth to come three-quarters up the meat** "
         "(about 4 cups). Do not submerge it. Add the remaining bay leaves "
         "and every bone you have.")
    step(10, "Cook it",
         "Boil, skim the grey foam, cover tightly, then: **oven 300 F, 3-3.5 "
         "hr** / **stovetop, lowest simmer, 3.5-4 hr** / **pressure 45 min + "
         "15 min release** / **slow cooker, low, 8-9 hr**. The liquid should "
         "barely tremble, never bubble hard.")
    step(11, "Know when it's done",
         "A fork slides into the thickest piece with **zero resistance**. "
         "Temperature is not the test - **collagen melts at 180-195 F and "
         "needs *time* there**, not just arrival. Still firm means another "
         "30 minutes, not more heat.")

    # ---- step 4
    new_page("Master recipe")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SIX  -  STEP FOUR")
    space(22)
    h1("Consomme and shred")
    pot_w, pot_h = 158, 196
    cy = pdf.get_y()
    draw_pot(M, cy + 10, pot_w, pot_h)
    draw_pot_labels(M, cy + 10, pot_w, pot_h)
    pdf.set_y(cy + pot_h + 30)
    caption("What you're looking at when you lift the lid: a fat cap you want, "
            "a consomme you must season, and bones that did their job.")
    step(12, "Lift out the meat",
         "Meat out with tongs; discard the bones, bay leaves and cinnamon "
         "stick. Shred with two forks - **shredded but not stringy**, stop "
         "while it still has body. Or chop it roughly, like a lot of trucks "
         "do.")
    step(13, "Skim the fat - and keep it",
         "Let the broth settle 5 minutes, then ladle the **red-orange fat** "
         "into a bowl. This is the taco fat - what you dip the tortillas in. "
         "A 5 lb pot gives you 1/2 to 3/4 cup.")
    step(14, "Season the consomme hard",
         "It should be savoury, tangy and slightly **too salty** on its own, "
         "because a tortilla is about to soak it up. Fix in this order: "
         "**salt**, then a splash of **vinegar**, then half a **bouillon cube** "
         "or 1/2 tsp **MSG** if it tastes hollow. Thin? Boil it down 10-15 "
         "minutes.")
    step(15, "Crisp the meat before serving",
         "Keep meat and consomme separately. Right before eating, crisp the "
         "shredded meat in a hot pan with a ladle of the reserved fat until "
         "the edges catch - 3-4 minutes. This is the step that separates "
         "quesabirria from a bowl of stew.")


# ------------------------------------------------------ 15-16. QUESABIRRIA
def build_quesabirria():
    new_page("Quesabirria")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SEVEN")
    space(22)
    h1("Quesabirria")
    lead("A taco that went to quesadilla school: tortilla dipped in red fat, "
         "cheese, meat, folded, griddled until lacy and brick-coloured, "
         "consomme on the side for dunking.")

    # five-panel fold diagram
    s = 78
    gap = 11
    total = 5 * s + 4 * gap
    x0 = M + (CW - total) / 2
    ensure(s + 74)
    y0 = pdf.get_y()
    kinds = ["tortilla", "cheese", "meat", "fold", "griddle"]
    captions = ["Dip the tortilla", "Cheese on one half", "Meat over the cheese",
                "Fold to a half-moon", "Griddle until lacy"]
    for i, k in enumerate(kinds):
        fold_panel(x0 + i * (s + gap), y0, s, k, i + 1)
    pdf.set_y(y0 + s + 6)
    pdf.set_font("B", "I", 8.8)
    pdf.set_text_color(*MUTED)
    for i, c in enumerate(captions):
        pdf.set_xy(x0 + i * (s + gap) - 6, y0 + s + 6)
        pdf.multi_cell(s + 12, 11, c, align="C", new_x="LEFT", new_y="NEXT")
    pdf.set_y(y0 + s + 36)
    caption("The sequence, start to finish. All five panels happen in about "
            "ninety seconds per taco.")

    h2("Build it", size=13.5)
    step(1, "Heat the plancha",
         "Comal or wide skillet over **medium-high** with 2-3 tbsp of the "
         "reserved red fat. Not maximum - there's sugar in that chile paste "
         "and it will scorch.")
    step(2, "Dip the tortilla",
         "Drag a corn tortilla through the hot fat (or across the top of the "
         "consomme pot) so both sides stain red. One second a side. Lay it "
         "flat on the plancha.")
    step(3, "Cheese, then meat",
         "A generous handful of shredded **Oaxaca or mozzarella** (2-3 oz) on "
         "**one half**, then a big spoonful of crisped meat on top. Cheese "
         "down, meat up - the cheese against the tortilla is the glue.")
    step(4, "Fold and griddle",
         "Fold into a half-moon, press down, and cook **1-2 minutes** until "
         "the underside is deep red-brown and lacy at the edges. Flip, one "
         "more minute. You want audible crisping.")
    step(5, "Serve it in ninety seconds",
         "Straight to the plate with a cup of hot consomme, plus chopped "
         "onion, cilantro, lime and salsa on the table. These do not hold - "
         "cook and eat in batches.")

    # ---- page 16: fixes + salsa + toppings
    new_page("Quesabirria")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER SEVEN  -  CONTINUED")
    space(22)
    h1("Salsa, toppings, sides")
    box("Five things that go wrong", [
        "**Tortillas cracking:** cold or too thin. Warm the stack in a towel first; buy taquera-size.",
        "**Nothing sticks together:** not enough cheese, or it's pre-shredded. Buy the block.",
        "**Burnt outside, cold inside:** heat too high - medium, 30 more seconds a side.",
        "**Soggy, not crispy:** the dip was a soak, or the pan wasn't hot enough.",
        "**Not red enough:** thin fat cap or thin chile paste - more paste in the pan next time.",
    ], tint=(250, 232, 226), title_color=(150, 40, 28))

    h2("Salsa de chile de arbol", size=13.5)
    para("The one you actually want on a quesabirria: thin, sharp, hot, ten "
         "minutes. **8 arbol, stemmed  -  2 husked tomatillos  -  1 garlic "
         "clove, unpeeled  -  1 tbsp vinegar  -  1/2 tsp salt.**", size=9.9,
         leading=13.8, color=INK2, gap_after=4)
    para("Toast the chiles **30 seconds a side** - don't let them blacken or "
         "it turns bitter. Char the tomatillos and garlic until blistered, "
         "5 minutes. Blend with 1/2 cup hot water, the vinegar and salt until "
         "smooth, then thin until it pours like heavy cream. Keeps a week and "
         "gets hotter on day two.", size=9.9, leading=13.8, color=INK2,
         gap_after=5)

    h2("The plate, minus the taco", size=13.5)
    bullet("**Onion and cilantro**, chopped fine and mixed together. Not a "
           "garnish - a requirement.", marker="dot")
    bullet("**Lime wedges.** Birria is rich; acid is not optional.",
           marker="dot")
    bullet("**Pickled onions** - slice one thin, cover with the juice of 3 "
           "limes and a pinch of salt, wait 30 minutes. Or the classic jarred "
           "escabeche of carrots, onion and jalapeno.", marker="dot")
    bullet("**A cup of consomme** for every person, topped with onion, "
           "cilantro and lime. This is the whole point.", marker="dot")
    bullet("**To drink:** horchata, jamaica, a Mexican Coke in the bottle, or "
           "a cold lager with lime in the neck.", marker="dot")
    space(2)
    box("How to eat one without embarrassment", [
        "Hold it over the consomme. Dunk a corner, bite, dunk again. Crisp at the edges, soft where the broth got in. If cheese escapes, you have done it correctly.",
    ], tint=(250, 238, 224))


# -------------------------------------------------------- 17. LEFTOVERS
def build_dayafter():
    new_page("The day after")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER EIGHT")
    space(22)
    h1("The day after")
    lead("Make a double batch. Birria is at its best on day two, and the "
         "consomme is the most useful thing in your freezer.")
    for title, body in [
        ("Birria ramen",
         "The reason to double the recipe. Bring **2 cups of consomme** to a "
         "boil, drop in fresh ramen noodles, finish with shredded birria, "
         "corn, a soft-boiled egg, onion, cilantro, lime and a spoonful of "
         "salsa de arbol. Not traditional; completely correct."),
        ("Mulitas",
         "The quesabirria's simpler cousin: **two** tortillas, cheese and meat "
         "sandwiched between them, griddled in red fat, cut into quarters. "
         "More cheese-to-meat contact; structurally superior."),
        ("Vampiros",
         "Spread a **tostada** with red fat, crisp it on the comal, pile on "
         "cheese, meat, onion, cilantro, salsa and lime."),
        ("Chilaquiles rojos de birria",
         "Fry quartered tortillas until crisp, simmer in **consomme** for 2 "
         "minutes until half-soft, top with birria, crema, queso fresco and a "
         "fried egg. The best breakfast in this book."),
        ("Torta ahogada, birria style",
         "Split a **bolillo**, spread with refried beans, fill with birria and "
         "Oaxaca, and ladle hot consomme over the top. Eat it over a bowl "
         "with a fork and no dignity."),
        ("Consomme, on its own",
         "A mug with onion, cilantro, lime and a handful of meat is a "
         "legitimate meal - it's what half of Tijuana orders at 7 a.m. Freeze "
         "it in **ice cube trays** and you have instant flavour for rice, "
         "beans and soups for three months."),
    ]:
        ensure(64)
        pdf.set_font("D", "B", 11.6)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW, 15, title)
        space(15)
        para(body, size=10, leading=14, color=INK2, gap_after=6)
    space(2)
    box("Storage", [
        "**Fridge:** meat and consomme separately, up to 4 days. The consomme sets into jelly when cold - that's the collagen, and it means you did it right.",
        "**Freezer:** meat with a ladle of broth, 3 months. Consomme in pint containers - plus ice cube trays for emergencies.",
    ], tint=(250, 238, 224))





# ------------------------------------------------------ 18. TROUBLESHOOTING
def build_trouble():
    new_page("Troubleshooting")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER NINE")
    space(22)
    h1("Troubleshooting")
    issues = [
        ("It tastes bitter", "You burnt the chiles - even a few seconds of "
         "smoke does it.",
         "This batch: a teaspoon of sugar and a knob of butter, and a raw "
         "potato in the pot for 20 minutes. Next time: cooler pan, shorter "
         "toast, pull at the first smell of raisins."),
        ("The consomme is gritty", "The paste wasn't strained, or the blender "
         "didn't run long enough.",
         "Strain the consomme itself through a fine sieve into a clean pot. "
         "Next time: 3 minutes in the blender, then strain, no excuses."),
        ("It tastes flat and dull", "Usually under-salted, usually also "
         "missing acid.",
         "Salt first, a teaspoon at a time, tasting between. Then a splash of "
         "vinegar or lime. Then half a bouillon cube or 1/2 tsp MSG. Salt and "
         "acid, in that order, fix almost everything."),
        ("The meat is dry and stringy", "The cut was too lean, or it isn't "
         "actually done yet.",
         "'Dry' at hour three often means 'tight' - keep cooking, submerged, "
         "another 30-45 minutes; collagen needs time, not just heat. Next "
         "time: chuck plus bones, and never the round."),
        ("The consomme is thin", "Too much water, or no bones in the pot.",
         "Boil it down uncovered 10-20 minutes until it coats a spoon. Next "
         "time: shank or oxtail, and fill only three-quarters up the meat."),
        ("Way too spicy", "Arbol chiles, or you left the veins in.",
         "Stir in crema or butter per portion and serve with more lime. Next "
         "time: all veins out, 2 arbol."),
        ("The cheese won't stretch", "Pre-shredded cheese, or too dry a "
         "cheese.",
         "Buy Oaxaca or a block of low-moisture whole-milk mozzarella and "
         "shred it yourself. Pre-shredded is dusted in starch so it won't "
         "clump - or melt."),
        ("It smells like a barbecue", "Too much chipotle or morita.",
         "You've made a different, also-delicious thing. Next time: one "
         "morita at most. Tijuana birria is bright and tangy, not smoky."),
    ]
    for i, (prob, why, fix) in enumerate(issues):
        ensure(62)
        pdf.set_font("D", "B", 11.4)
        pdf.set_text_color(*RED)
        pdf.set_x(M)
        pdf.cell(CW, 15, prob)
        space(15.2)
        pdf.set_font("U", "B", 8.3)
        pdf.set_text_color(*MUTED)
        pdf.set_x(M)
        pdf.cell(CW, 11, "WHY: " + why)
        space(11.2)
        para(fix, size=9.9, leading=13.8, color=INK2, indent=10, gap_after=7)


# ------------------------------------------------------------ 19. BACK MATTER
def build_back():
    new_page("Numbers & notes")
    pdf.set_font("U", "BB", 9)
    pdf.set_text_color(*RED)
    pdf.set_xy(M, TOP)
    pdf.cell(CW, 12, "CHAPTER TEN")
    space(22)
    h1("Numbers and notes")
    para("**Temperatures:** 300 F / 150 C for the braise; collagen melts "
         "into gelatin at an internal 180-195 F / 82-90 C; 165 F is where "
         "most people panic, pull the meat, and ruin dinner. Keep going.",
         size=10, leading=14, color=INK2, gap_after=5)
    para("**Weights:** 1 lb = 454 g, 1 cup = 240 ml, 1 tbsp = 15 ml, 1 tsp = "
         "5 ml. The 5 lb (2.3 kg) this book is built around: **3 lb chuck + "
         "1.5 lb shank + 1 lb short rib or oxtail.** Chiles: **50 g guajillo, "
         "20 g ancho, 10 g pasilla, 3 g arbol.**", size=10, leading=14,
         color=INK2, gap_after=5)
    h2("Cheat sheet, one page", size=13.5)
    box("Pin this to the fridge", [
        "**Meat:** 3 lb chuck + 1.5 lb cross-cut shank + 1 lb short rib or oxtail.",
        "**Chiles:** 6 guajillo, 2 ancho, 1 pasilla, 3-6 arbol. Toast, soak 30 min, blend 3 min, strain.",
        "**Spice:** canela, 4 cloves, 1 tsp cumin, 1 tsp pepper, 2 tsp Mexican oregano, 1 tsp thyme, 1/2 tsp marjoram, 1/2 tsp ginger, 4 bay, 1/4 cup vinegar, 1 tbsp salt.",
        "**Cook:** 300 F covered, 3.5 hr (or 45 min at pressure). Liquid three-quarters up the meat.",
        "**Finish:** skim the red fat, shred, season the consomme with salt then vinegar, crisp the meat in the fat.",
        "**Serve:** dip tortilla in fat, cheese down, meat up, fold, griddle 2 min, consomme on the side.",
    ], tint=(250, 238, 224))
    h2("Your birria, your numbers", size=13.5)
    para("Write it down the moment you nail it, because you will not remember "
         "in three months.", size=9.8, leading=13.6, color=MUTED)
    for _ in range(5):
        ensure(22)
        y = pdf.get_y() + 6
        pdf.set_draw_color(*LINE)
        pdf.set_line_width(0.6)
        pdf.line(M, y, W - M, y)
        pdf.set_y(y + 13)
    ornament()
    para("Cook it for people. Make twice as much as you think you need. Keep "
         "the consomme.", size=11.4, leading=16.5, family="D", style="I",
         color=RED, align="C", gap_after=2)
    para("- THE END -", size=8.6, family="U", style="BB", color=MUTED,
         align="C")


def main():
    pdf.set_title("Tijuana Birria - A Short, Illustrated Field Guide")
    pdf.set_author("Arena Agent Mode")
    pdf.set_subject("Authentic Tijuana-style birria de res: cuts, chiles, "
                    "recipe and quesabirria")
    pdf.set_keywords("birria, Tijuana, quesabirria, birria de res, cookbook, "
                     "tacos, consomme")
    pdf.set_creator("build_book.py (fpdf2)")
    build_cover()
    build_contents()
    build_intro()
    build_meat()
    build_chiles()
    build_shopping()
    build_equipment()
    build_recipe()
    build_quesabirria()
    build_dayafter()
    build_trouble()
    build_back()
    out = os.path.join(HERE, "Tijuana-Birria-Cookbook.pdf")
    pdf.output(out)
    print("wrote", out, os.path.getsize(out) // 1024, "KB,", pdf.pages_count,
          "pages")


if __name__ == "__main__":
    main()
