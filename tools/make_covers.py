"""Build all cover assets: ebook cover PDF + JPG, and the paperback wrap PDF."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from reportlab.lib.colors import HexColor, white      # noqa: E402
from reportlab.pdfgen import canvas                   # noqa: E402

import cover_design as cd                             # noqa: E402

PAGES = 25
PER_PAGE_IN = 0.002252          # white paper, inches per page


def ebook_cover_pdf(path, w=432, h=691.2):
    """1600 x 2560 px equivalent, the ratio KDP asks for."""
    cd.register_fonts()
    c = canvas.Canvas(path, pagesize=(w, h), initialFontName="Body")
    c.setTitle("The Ex-Files - Kindle cover")
    c.setAuthor(cd.AUTHOR_NAME)
    cd.front_cover(c, w, h)
    c.save()


def wrap_pdf(path):
    cd.register_fonts()
    bleed = 0.125 * 72
    trim_w, trim_h = 8.5 * 72, 11 * 72
    spine = PAGES * PER_PAGE_IN * 72
    total_w = bleed * 2 + trim_w * 2 + spine
    total_h = bleed * 2 + trim_h

    c = canvas.Canvas(path, pagesize=(total_w, total_h), initialFontName="Body")
    c.setTitle("The Ex-Files - paperback cover wrap")
    c.setAuthor(cd.AUTHOR_NAME)

    # spine band first (drawn behind both panels)
    c.setFillColor(cd.PANEL_DARK)
    c.rect(0, 0, total_w, total_h, stroke=0, fill=1)
    c.setFillColor(cd.ACCENT_DEEP)
    c.rect(bleed + trim_w, 0, spine, total_h, stroke=0, fill=1)

    # back cover (left of the spine)
    c.saveState()
    c.translate(bleed, bleed)
    cd.back_cover(c, trim_w, trim_h)
    cd.barcode_panel(c, trim_w, trim_h)
    c.restoreState()

    # front cover (right of the spine)
    c.saveState()
    c.translate(bleed + trim_w + spine, bleed)
    cd.front_cover(c, trim_w, trim_h)
    c.restoreState()

    # spine text only if the spine is actually wide enough to hold it
    if spine >= 0.25 * 72:
        c.saveState()
        c.translate(bleed + trim_w + spine / 2, trim_h / 2 + bleed)
        c.rotate(90)
        c.setFillColor(white)
        c.setFont("Head-Bold", 15)
        c.drawCentredString(0, -5, "THE EX-FILES")
        c.setFillColor(HexColor("#e8c9cf"))
        c.setFont("Body", 10)
        c.drawCentredString(0, -22, "Crosswords for Men Who Are Absolutely Fine")
        c.restoreState()
    c.save()
    return spine, total_w, total_h


def jpg_from_pdf(pdf_path, jpg_path, width=1600):
    import pypdfium2 as pdfium
    from PIL import Image

    doc = pdfium.PdfDocument(pdf_path)
    page = doc[0]
    img = page.render(scale=width / page.get_width()).to_pil()
    target_h = round(width * page.get_height() / page.get_width())
    if img.size != (width, target_h):
        img = img.resize((width, target_h), Image.LANCZOS)
    img.convert("RGB").save(jpg_path, "JPEG", quality=94)
    return (width, target_h)


if __name__ == "__main__":
    out = os.path.join(ROOT, "cover")
    os.makedirs(out, exist_ok=True)

    eb = os.path.join(out, "The_Ex_Files_ebook_cover.pdf")
    ebook_cover_pdf(eb)
    size = jpg_from_pdf(eb, os.path.join(out, "The_Ex_Files_ebook_cover_1600x2560.jpg"))
    print(f"ebook cover: {eb}")
    print(f"ebook cover JPG: {size[0]}x{size[1]} px")

    wrap = os.path.join(out, "The_Ex_Files_paperback_wrap.pdf")
    spine, tw, th = wrap_pdf(wrap)
    print(f"paperback wrap: {wrap}")
    print(f"  spine {spine/72:.3f} in | total {tw/72:.3f} x {th/72:.3f} in")
    if spine < 0.25 * 72:
        print("  (spine left blank - too thin for text, per KDP guidance)")
