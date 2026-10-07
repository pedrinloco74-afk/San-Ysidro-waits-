"""Check a cover PDF for text collisions and out-of-bounds text.

Renders nothing by hand: it reads the real glyph boxes out of the PDF and
reports any pair that overlaps, plus anything sitting outside the page.
"""
from __future__ import annotations

import sys
from itertools import combinations

import pypdfium2 as pdfium


def boxes(path, scale=1.0):
    doc = pdfium.PdfDocument(path)
    out = []
    for pno, page in enumerate(doc):
        tp = page.get_textpage()
        n = tp.count_chars()
        text = tp.get_text_range()
        i = 0
        while i < n:
            ch = text[i]
            if not ch.strip():
                i += 1
                continue
            left, bottom, right, top = tp.get_charbox(i)
            out.append({
                "page": pno, "char": ch,
                "x0": left, "y0": bottom, "x1": right, "y1": top,
            })
            i += 1
    return out, doc


def words(chars, gap=2.2):
    """Group characters into words: cluster by baseline first (glyph tops vary
    by a fraction of a point within one line), then join by horizontal gap."""
    # cluster baselines: same page and y0 within 2pt belong to the same line
    lines = []
    for c in sorted(chars, key=lambda c: (c["page"], c["y0"])):
        placed = False
        for ln in lines:
            if ln["page"] == c["page"] and abs(ln["y0"] - c["y0"]) <= 2.0:
                ln["chars"].append(c)
                ln["y0"] = min(ln["y0"], c["y0"])
                placed = True
                break
        if not placed:
            lines.append({"page": c["page"], "y0": c["y0"], "chars": [c]})

    rows = {(ln["page"], round(ln["y0"], 0)): ln["chars"] for ln in lines}
    out = []
    for (page, _y), group in rows.items():
        group.sort(key=lambda c: c["x0"])
        cur = None
        for c in group:
            if cur and c["x0"] - cur["x1"] <= gap:
                cur["text"] += c["char"]
                cur["x1"] = max(cur["x1"], c["x1"])
                cur["y0"] = min(cur["y0"], c["y0"])
                cur["y1"] = max(cur["y1"], c["y1"])
            else:
                if cur:
                    out.append(cur)
                cur = dict(c, text=c["char"])
        if cur:
            out.append(cur)
    return out


def overlaps(a, b, pad=0.0):
    return not (a["x1"] + pad <= b["x0"] or b["x1"] + pad <= a["x0"] or
                a["y1"] + pad <= b["y0"] or b["y1"] + pad <= a["y0"])


def report(path, page_w, page_h, name="cover"):
    chars, doc = boxes(path)
    ws = words(chars)
    problems = []

    # out of bounds (allow 0.5pt tolerance)
    for w in ws:
        if (w["x0"] < -0.5 or w["y0"] < -0.5 or
                w["x1"] > page_w + 0.5 or w["y1"] > page_h + 0.5):
            problems.append(
                f"OUT OF BOUNDS  '{w['text'][:28]}'  "
                f"x {w['x0']:.1f}..{w['x1']:.1f} (page {page_w:.0f})  "
                f"y {w['y0']:.1f}..{w['y1']:.1f} (page {page_h:.0f})")

    # collisions between words on different lines / blocks
    for a, b in combinations(ws, 2):
        if a["page"] != b["page"]:
            continue
        if a["text"] == b["text"]:
            continue
        if overlaps(a, b, pad=-0.6):
            # ignore touching characters of the same word
            problems.append(
                f"OVERLAP  '{a['text'][:22]}'  <->  '{b['text'][:22]}'  "
                f"at x~{max(a['x0'], b['x0']):.0f} y~{a['y0']:.0f}")

    print(f"--- {name}: {len(ws)} words, {len(chars)} glyphs, "
          f"{page_w:.0f}x{page_h:.0f} pt")
    if problems:
        for p in problems[:40]:
            print("   ", p)
        print(f"    {len(problems)} problem(s)")
    else:
        print("    clean: no overlapping or out-of-bounds text")
    return problems


if __name__ == "__main__":
    total = 0
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total += len(report(os.path.join(root, "cover", "The_Ex_Files_ebook_cover.pdf"),
                        432, 691.2, "ebook cover"))
    total += len(report(os.path.join(root, "cover", "The_Ex_Files_paperback_wrap.pdf"),
                        1246.7, 810, "paperback wrap"))
    raise SystemExit(1 if total else 0)
