"""Builds the print-ready PDF of *Are They Cheating?*"""
from __future__ import annotations

import pathlib
import re
import sys
import zipfile

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mdparse
from cover import build_cover, W as COVER_W, H as COVER_H
from engine import (C, COL_BOTTOM, COL_H, COL_TOP, COL_W, FONT_FILES, GUTTER,
                    M_BOTTOM, M_LEFT, M_RIGHT, M_TOP, PAGE_H, PAGE_W, T,
                    AppendixBanner, Box, Bullets, Flow, FullPage, HRule, Heading,
                    Page, PageBreak, Paginator, Paragraph, PartBanner, Placement,
                    Spacer, SubHead, Table, draw_line, draw_tracked, plain,
                    register_fonts, tracked_width, wrap_text, wrap_tracked)

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANUSCRIPT = sorted((ROOT / "src" / "manuscript").glob("*.md"))
OUT = ROOT / "ebook" / "Are-They-Cheating.pdf"

TITLE = "ARE THEY CHEATING?"
SUBTITLE = "THE NO-NONSENSE FIELD GUIDE TO THE TRUTH, THE PROOF, AND THE WAY OUT"

PART_BLURBS = {
    "ONE": ["The 25 signs that matter", "The Red Flag Scorecard",
            "Why your gut is data, not drama"],
    "TWO": ["The Seven Rules", "The legal line", "The case file that holds up"],
    "THREE": ["Phones, money, time, and people", "The nine questions",
              "The 14-Day Proof Plan"],
    "FOUR": ["The five-sentence script", "The Cheater's Dictionary",
             "What to do if you were wrong"],
    "FIVE": ["The two roads", "Protect what matters", "The first ninety days"],
}


# --------------------------------------------------------------------- cover --
def draw_cover(c, cover_png):
    c.setFillColor(C.NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    img = ImageReader(str(cover_png))
    x, y, w, h = 0, 0, PAGE_W, PAGE_H
    c.drawImage(img, x, y, w, h, preserveAspectRatio=False, anchor="c", mask=None)


def draw_title_page(c):
    """Clean typeset title page that mirrors the cover."""
    c.setFillColor(C.NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(C.GOLD)
    c.rect(0, PAGE_H - 8, PAGE_W, 8, stroke=0, fill=1)

    x = M_LEFT + 6
    w = PAGE_W - 2 * x
    draw_tracked(c, "THE NO-NONSENSE FIELD GUIDE TO THE TRUTH",
                 "Sans-Bd", 8.4, x, PAGE_H - 190, 2.4)

    c.setFillColor(C.WHITE)
    y = PAGE_H - 300
    for font, text, size, lead in [("Display", "ARE THEY", 62, 58),
                                   ("Display", "CHEATING?", 62, 62)]:
        f = _fit_display(text, size, w)
        for ln in wrap_tracked(text, "Display", f, w, 1.4):
            draw_tracked(c, ln, "Display", f, x, y, 1.4)
            y -= lead
    c.setFillColor(C.RED)
    c.rect(x, y - 34, 100, 4, stroke=0, fill=1)

    y -= 92
    c.setFillColor(C.WHITE)
    for ln in wrap_tracked("EVERY ANSWER YOU NEED. THE TRUTH. THE PROOF. THE DECISION.",
                           "Sans-Md", 13.2, w, 1.6):
        draw_tracked(c, ln, "Sans-Md", 13.2, x, y, 1.6)
        y -= 21
    y -= 8
    c.setFillColor(HexColor("#C6D2E0"))
    for ln in wrap_tracked("A 14-DAY SYSTEM FOR FINDING OUT — QUIETLY, LEGALLY, "
                           "AND WITHOUT LOSING YOURSELF.", "Sans", 10.6, w, 0.8):
        draw_tracked(c, ln, "Sans", 10.6, x, y, 0.8)
        y -= 16

    inner = [
        "The 25 signs that actually matter — and the three traps that ruin the list",
        "The Seven Rules: how not to blow up your own case in week one",
        "Where investigation ends and a criminal charge begins",
        "The 14-Day Proof Plan, day by day, with nothing to install",
        "The confrontation script — five sentences, word for word",
        "The Cheater's Dictionary: 25 lines you will hear, translated",
        "The Red Flag Scorecard, the Evidence Log, and the One-Page Summary",
    ]

    bx, by, bw = x, 250, w
    bh = 62 + len(inner) * 19
    c.setFillColor(HexColor("#16233A"))
    c.rect(bx, by, bw, bh, stroke=0, fill=1)
    c.setFillColor(C.RED)
    c.rect(bx, by, 4, bh, stroke=0, fill=1)
    ty = by + bh - 26
    draw_tracked(c, "INSIDE THIS GUIDE", "Sans-Bd", 8.4, bx + 24, ty, 2.2)
    ty -= 26
    for item in inner:
        c.setFillColor(C.GOLD)
        c.circle(bx + 27, ty + 3.4, 1.9, stroke=0, fill=1)
        c.setFillColor(HexColor("#D7DFE9"))
        for ln in wrap_text(item, "sans", 9.2, bw - 60):
            draw_line(c, ln, bx + 38, ty, bw - 60, "sans", 9.2,
                      HexColor("#D7DFE9"), "left", False)
            ty -= 13
        ty -= 6

    c.setFillColor(HexColor("#7E90A6"))
    draw_tracked(c, "SAN YSIDRO PRESS  ·  FIELD GUIDE NO. 1", "Sans-Md", 8.2,
                 x, 190, 2.2)


def _fit_display(text, size, width):
    while size > 12 and tracked_width(text, "Display", size, 1.4) > width:
        size -= 1
    return size


def draw_copyright(c):
    x = M_LEFT
    w = PAGE_W - 2 * x
    y = PAGE_H - 190
    c.setFillColor(C.INK)
    draw_tracked(c, "ARE THEY CHEATING?", "Display", 17, x, y, 1.2)
    y -= 30
    for ln in wrap_text("The No-Nonsense Field Guide to the Truth, the Proof, "
                        "and the Way Out", "sans", 10.4, w, 0, 0):
        draw_line(c, ln, x, y, w, "sans", 10.4, C.MUTED, "left", False)
        y -= 15
    y -= 24
    blocks = [
        ("Copyright © 2026 San Ysidro Press. All rights reserved.", True),
        ("First edition. Field Guide No. 1.", False),
        ("", False),
        ("This book is educational material. It is not legal advice, medical advice, "
         "psychological treatment, or a substitute for any of them. Laws about "
         "surveillance, recording, privacy, and evidence differ by state, province, "
         "and country, and they change. Nothing here authorizes you to break a law "
         "where you live.", False),
        ("", False),
        ("If you are in danger, contact emergency services or a domestic violence "
         "hotline before doing anything else in this book. See Appendix C.", False),
        ("", False),
        ("No part of this publication may be reproduced, distributed, or transmitted "
         "in any form without prior written permission, except brief quotations in a "
         "review. The advice in this book is general; every relationship, every "
         "jurisdiction, and every person is specific.", False),
        ("", False),
        ("Interior set in Source Serif and Inter. Display type in Anton. "
         "Cover design by San Ysidro Press.", False),
    ]
    for text, _bold in blocks:
        if not text:
            y -= 8
            continue
        for ln in wrap_text(text, "sans", 9.0, w, 0, 0):
            draw_line(c, ln, x, y, w, "sans", 9.0, C.MUTED, "left", False)
            y -= 12.6
        y -= 6


def make_contents_renderer(paginator):
    def render_contents(c):
        draw_contents(c, paginator)
    return render_contents


def draw_contents(c, paginator):
    """Draw the table of contents using the page numbers recorded during pagination."""
    c.setFillColor(C.NAVY)
    c.rect(0, PAGE_H - 118, PAGE_W, 118, stroke=0, fill=1)
    c.setFillColor(C.GOLD)
    c.rect(0, PAGE_H - 118, PAGE_W, 4, stroke=0, fill=1)
    draw_tracked(c, "CONTENTS", "Display", 30, M_LEFT, PAGE_H - 78, 1.2)
    c.setFillColor(HexColor("#93A6BC"))
    draw_tracked(c, "READ WHAT YOU NEED — THIS IS A WORKBOOK, NOT A NOVEL",
                 "Sans", 7.4, M_LEFT, PAGE_H - 100, 1.4)

    entries = []
    for label, kind, pidx in paginator.sections:
        if kind == "part":
            entries.append((label.upper(), pidx + 1, "part"))
        elif kind == "chapter":
            entries.append((label, pidx + 1, "chap"))
        elif kind == "appendix":
            entries.append((label.upper(), pidx + 1, "appendix"))

    top = PAGE_H - 160
    bottom = M_BOTTOM + 26
    avail = top - bottom
    # balance the two columns
    heights = [(16.5 if k in ("part", "appendix") else 13.2)
               + (5 if i and entries[i - 1][2] in ("part", "appendix") else 0)
               for i, (_, _, k) in enumerate(entries)]
    total = sum(heights)
    split, run = len(entries), 0.0
    for i, h in enumerate(heights):
        run += h
        if run > total / 2:
            split = i + 1
            break
    cols = [(0, split), (split, len(entries))]
    for ci, (a, bnd) in enumerate(cols):
        x = M_LEFT + ci * (COL_W + GUTTER)
        y = top
        for i in range(a, bnd):
            label, page, kind = entries[i]
            if i and entries[i - 1][2] in ("part", "appendix"):
                y -= 5
            if kind in ("part", "appendix"):
                c.setFillColor(C.ACCENT if kind == "part" else C.LEGAL)
                shown = label
                while (tracked_width(shown, "Sans-Bd", 8.6, 1.6) > COL_W - 24
                       and len(shown) > 10):
                    shown = shown[:-2]
                if shown != label:
                    shown = shown.rstrip(" ,-·") + "…"
                draw_tracked(c, shown, "Sans-Bd", 8.6, x, y - 9, 1.6)
                c.setFont("Sans-Md", 8.0)
                c.setFillColor(C.INK)
                c.drawRightString(x + COL_W, y - 9, str(page))
                y -= 16.5
            else:
                shown = label
                c.setFont("Serif", 9.4)
                while (pdfmetrics.stringWidth(shown, "Serif", 9.4)
                       > COL_W - 26 and len(shown) > 8):
                    shown = shown[:-2]
                if shown != label:
                    shown = shown.rstrip(" ,-") + "…"
                c.setFillColor(C.BODY)
                c.drawString(x + 8, y - 9, shown)
                c.setFillColor(C.FAINT)
                c.setLineWidth(0.5)
                c.setDash(1, 2)
                lx = x + 8 + pdfmetrics.stringWidth(shown, "Serif", 9.4) + 4
                c.line(lx, y - 6.4, x + COL_W - 14, y - 6.4)
                c.setDash()
                c.setFillColor(C.INK)
                c.setFont("Sans-Md", 8.2)
                c.drawRightString(x + COL_W, y - 9, str(page))
                y -= 13.2
    # ---- fastest-route panel, filling the lower half of the page
    panel_y = M_BOTTOM + 40
    panel_h = 168
    c.setFillColor(C.GREY_BG)
    c.rect(M_LEFT, panel_y, PAGE_W - M_LEFT - M_RIGHT, panel_h, stroke=0, fill=1)
    c.setFillColor(C.NAVY)
    c.rect(M_LEFT, panel_y, PAGE_W - M_LEFT - M_RIGHT, 3, stroke=0, fill=1)
    draw_tracked(c, "THE FASTEST ROUTE TO AN ANSWER", "Sans-Bd", 8.6,
                 M_LEFT + 20, panel_y + panel_h - 24, 1.8)
    routes = [
        ("I have ten minutes.", "Score yourself on page 9, then read Why Your Gut "
                                "Is Not the Problem (page 6)."),
        ("I want to start watching tonight.", "The Seven Rules (page 10) and the "
                                              "case file (page 11)."),
        ("I want a plan with dates on it.", "The 14-Day Proof Plan, page 19."),
        ("Something happened. I need to act now.", "The Script (page 21) and The "
                                                   "Cheater's Dictionary (page 22)."),
        ("I am scared of my partner.", "Chapter 18, page 25 — before anything else."),
    ]
    ry = panel_y + panel_h - 52
    for lead, rest in routes:
        c.setFillColor(C.ACCENT)
        c.circle(M_LEFT + 23, ry + 3.6, 1.9, stroke=0, fill=1)
        w = c.setFont("Sans-Bd", 8.8) or 0
        x = M_LEFT + 34
        c.setFont("Sans-Bd", 8.8)
        c.setFillColor(C.INK)
        c.drawString(x, ry, lead)
        x += pdfmetrics.stringWidth(lead, "Sans-Bd", 8.8) + 4
        c.setFillColor(C.MUTED)
        for ln in wrap_text(rest, "sans", 8.8, PAGE_W - M_LEFT - M_RIGHT - (x - M_LEFT) - 24):
            draw_line(c, ln, x, ry, PAGE_W - M_LEFT - M_RIGHT - (x - M_LEFT) - 24,
                      "sans", 8.8, C.MUTED, "left", False)
            ry -= 11.4
            x = M_LEFT + 34
        ry -= 13.6


def toc_appendix_label(text, subtitle):
    """TOC/outline label for the four top-level appendices (A1-A4 are skipped)."""
    upper = text.strip().upper()
    if upper == "APPENDIX A":
        return "Appendix A · " + (subtitle or "The Toolkit")
    m = re.match(r"^APPENDIX\s+([BCD])\s*[:\u2014-]\s*(.+)$", upper)
    if m:
        return f"Appendix {m.group(1)} · " + m.group(2).strip().title()
    return None


# ------------------------------------------------------------ flow builders --
def build_flows(blocks, paginator):
    flows = []
    page_break_pending = False
    first_chapter = True

    def entry_tag(kind, label):
        return (kind, label)

    for bi, b in enumerate(blocks):
        nxt = blocks[bi + 1] if bi + 1 < len(blocks) else None

        if b.kind == "titlepage":
            # a FullPage always starts a fresh page, so no explicit PageBreak here
            flows.append(FullPage(draw_cover_from_marker, key="cover"))
            flows.append(FullPage(draw_title_page))
            flows.append(FullPage(draw_copyright))
            continue

        if b.kind == "pagebreak":
            flows.append(PageBreak())
            continue

        if b.kind == "part":
            label = b.text
            flows.append(PageBreak())
            banner = PartBanner(label, b.title,
                                PART_BLURBS.get(label.split()[-1], []))
            banner.entry = ("part", b.text)
            banner.anchor = b.text
            banner.running = b.text + " · " + b.title
            flows.append(banner)
            first_chapter = True
            continue

        if b.kind == "chapter":
            f = Heading(b.text, kicker=(b.title or ""), size=21.5,
                        space_before=5 if first_chapter else 15, space_after=7.5)
            f.entry = ("chapter", b.text)
            f.anchor = b.text
            f.running = b.text
            key = (b.title or "") + " " + b.text
            flows.append(f)
            first_chapter = False
            continue

        if b.kind == "appendix_banner":
            f = AppendixBanner(b.text, b.title)
            label = toc_appendix_label(b.text, b.title)
            if label:
                f.entry = ("appendix", label)
                f.anchor = label
                f.running = b.text
            flows.append(f)
            continue

        if b.kind == "h2":
            flows.append(SubHead(b.text, size=10.8, space_before=11, space_after=4.2))
            continue
        if b.kind == "h3":
            flows.append(SubHead(b.text, size=10.0, space_before=8.5, space_after=3.4))
            continue

        if b.kind == "p":
            flows.append(Paragraph(b.text, space_after=3.5))
            continue

        if b.kind == "list":
            flows.append(Bullets(b.items, b.meta.get("variant", "bullet"),
                                 space_before=1.5, space_after=4.0))
            continue

        if b.kind == "quote":
            flows.append(Box([Paragraph(b.text, font_key="body", size=9.4,
                                        lead=12.4, space_after=0)],
                             title="", style="script", space_before=5, space_after=6))
            continue

        if b.kind == "score":
            flows.append(Table(b.rows, kind="score", space_before=4.5, space_after=5.5))
            continue
        if b.kind == "table":
            flows.append(Table(b.rows, kind="table", title=b.title,
                               space_before=5, space_after=5.8))
            continue
        if b.kind == "script":
            kids = [Paragraph(b.text, size=9.5, lead=12.6, space_after=0,
                              color=C.INK)] if b.text else []
            for ch in b.children:
                if ch.kind == "p":
                    kids.append(Paragraph(ch.text, size=9.0, lead=12.2,
                                          space_after=3.2))
                elif ch.kind == "list":
                    kids.append(Bullets(ch.items, ch.meta.get("variant", "bullet"),
                                        size=8.7, lead=11.3, boxed=True,
                                        space_before=0, space_after=2.6))
            flows.append(Box(kids, title=b.title or "Script", style="script",
                             space_before=7, space_after=8))
            continue

        if b.kind == "box":
            flows.append(make_box(b))
            continue

        if b.kind == "contents" and not any(
                isinstance(f, FullPage) and getattr(f, "key", None) == "contents"
                for f in flows):
            toc = FullPage(make_contents_renderer(paginator), key="contents")
            flows.append(toc)
            continue
        if b.kind == "contents_body":
            continue

    return flows


COVER_RENDER = {"fn": None}


def draw_cover_from_marker(c):
    COVER_RENDER["fn"](c)


def make_box(b):
    kind = b.text
    styles = {
        "truth": ("truth", "THE BOTTOM LINE", None),
        "keypoints": ("keypoints", "KEY POINTS", None),
        "note": ("note", "NOTE", None),
        "check": ("check", "CHECKLIST", None),
        "watch": ("watch", b.title or "WATCH OUT", None),
        "legal": ("legal", "THE LEGAL LINE", None),
        "donow": ("donow", b.title or "DO IT NOW", None),
    }
    style, default_title, _ = styles.get(kind, ("keypoints", b.title, None))
    title = b.title or default_title
    title = title.replace("THE SHORT VERSION", "THE BOTTOM LINE")
    size = T.box_size if kind != "truth" else 9.5
    lead = T.box_lead if kind != "truth" else 12.6
    kids = []
    light = kind == "truth"
    body_color = HexColor("#E8EDF4") if light else None
    for ch in b.children:
        if ch.kind == "p":
            kids.append(Paragraph(ch.text, size=size, lead=lead,
                                  color=body_color, space_after=3.4))
        elif ch.kind == "list":
            kids.append(Bullets(ch.items, ch.meta.get("variant", "bullet"),
                                size=size - 0.3, lead=lead - 0.5, boxed=True,
                                color=body_color, space_before=0, space_after=2.6))
    if not kids:
        return Spacer(0)
    if light:
        for k in kids:
            if isinstance(k, Bullets):
                k.marker_color = C.GOLD
    return Box(kids, title=title, style=style, space_before=7.5, space_after=9)


# ------------------------------------------------------------------ renderer --
def render(pages, paginator, path):
    c = rl_canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Are They Cheating? The No-Nonsense Field Guide to the Truth, "
               "the Proof, and the Way Out")
    c.setAuthor("San Ysidro Press")
    c.setSubject("Infidelity investigation, evidence, and recovery — a 14-day plan")
    c.setKeywords("infidelity, cheating, evidence, marriage, divorce, 14-day plan")

    # ---- outline bookmarks, grouped by the page they belong to
    by_page: dict[int, list] = {}
    for label, kind, pidx in sorted(paginator.sections, key=lambda s: s[2]):
        by_page.setdefault(pidx, []).append((label, kind))
    seen_part = False

    for pg in pages:
        for label, kind in by_page.get(pg.index, []):
            c.bookmarkPage(label, fit="XYZ", top=PAGE_H, bottom=0, left=0, right=PAGE_W)
            if kind == "part":
                seen_part = True
                level = 0
            else:
                level = 1 if seen_part else 0
            c.addOutlineEntry(label, label, level=level, closed=False)
        full = pg.full
        if not full:
            draw_running_head(c, pg)
            c.setStrokeColor(C.GREY_BD)
            c.setLineWidth(0.5)
            c.line(PAGE_W / 2, COL_BOTTOM - 9, PAGE_W / 2, COL_TOP + 6)
        for pl in pg.placements:
            pl.flow.draw(c, pl.x, pl.top, pl.width)
        if pg.index > 0:
            draw_footer(c, pg)
        c.showPage()

    c.save()
    return path


def draw_running_head(c, pg):
    c.setFillColor(C.MUTED)
    left = pg.running_head or TITLE
    draw_tracked(c, left.upper()[:70], "Sans-Md", 7.2, M_LEFT, COL_TOP + 26, 1.5)
    right = "ARE THEY CHEATING?"
    w = tracked_width(right, "Sans", 7.2, 1.5)
    c.setFillColor(C.FAINT)
    draw_tracked(c, right, "Sans", 7.2, PAGE_W - M_RIGHT - w, COL_TOP + 26, 1.5)
    c.setFillColor(C.ACCENT)
    c.rect(M_LEFT, COL_TOP + 17, 18, 1.6, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#E4E7EB"))
    c.setLineWidth(0.6)
    c.line(M_LEFT, COL_TOP + 12, PAGE_W - M_RIGHT, COL_TOP + 12)


def draw_footer(c, pg):
    n = pg.index + 1
    c.setFillColor(C.MUTED)
    c.setFont("Sans-Md", 7.6)
    label = "SAN YSIDRO PRESS"
    c.drawCentredString(PAGE_W / 2, M_BOTTOM - 12, f"{n}")
    c.setFillColor(C.FAINT)
    draw_tracked(c, label, "Sans", 6.6, M_LEFT, M_BOTTOM - 12, 1.4)
    right = "FIELD GUIDE NO. 1"
    w = tracked_width(right, "Sans", 6.6, 1.4)
    draw_tracked(c, right, "Sans", 6.6, PAGE_W - M_RIGHT - w, M_BOTTOM - 12, 1.4)
    c.setStrokeColor(C.FAINT)
    c.setLineWidth(0.6)
    c.line(M_LEFT, M_BOTTOM - 2, PAGE_W - M_RIGHT, M_BOTTOM - 2)


def main():
    register_fonts(ROOT / "assets" / "fonts")
    cover_png = build_cover()
    COVER_RENDER["fn"] = lambda c: draw_cover(c, cover_png)

    blocks = mdparse.parse_manuscript(MANUSCRIPT)
    paginator = Paginator()
    flows = build_flows(blocks, paginator)
    paginator.paginate(flows)

    n = len(paginator.pages)
    print(f"pages: {n}")
    if paginator.warnings:
        for w in paginator.warnings[:12]:
            print("  warning:", w)
    render(paginator.pages, paginator, OUT)
    print("wrote", OUT, f"{OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
