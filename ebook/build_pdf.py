#!/usr/bin/env python3
"""Create a print-ready 6 x 9 inch PDF from the ebook manuscript.

Install the one optional dependency with `python3 -m pip install -r ebook/requirements-pdf.txt`.
"""
from __future__ import annotations

import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Flowable,
        Frame,
        HRFlowable,
        ListFlowable,
        ListItem,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
except ImportError as exc:  # make the setup requirement clear to the user
    raise SystemExit(
        "PDF generation needs ReportLab. Install it with: "
        "python3 -m pip install -r ebook/requirements-pdf.txt"
    ) from exc

import build_ebook

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "the-human-advantage.md"
OUTPUT = ROOT / "the-human-advantage.pdf"

PAGE_WIDTH, PAGE_HEIGHT = 6 * inch, 9 * inch
NAVY = colors.HexColor("#10263a")
DEEP = colors.HexColor("#0b1b2d")
TEAL = colors.HexColor("#167c80")
PALE_TEAL = colors.HexColor("#e7f3f1")
INK = colors.HexColor("#263849")
MUTED = colors.HexColor("#5b7080")
RULE = colors.HexColor("#d4e0e5")

REPORTLAB_FONT_DIR = Path(__import__("reportlab").__file__).resolve().parent / "fonts"
FONT_FILES = {
    "BookSans": REPORTLAB_FONT_DIR / "Vera.ttf",
    "BookSans-Bold": REPORTLAB_FONT_DIR / "VeraBd.ttf",
    "BookSans-Italic": REPORTLAB_FONT_DIR / "VeraIt.ttf",
    "BookSans-BoldItalic": REPORTLAB_FONT_DIR / "VeraBI.ttf",
}


def register_fonts() -> None:
    for name, path in FONT_FILES.items():
        if not path.is_file():
            raise FileNotFoundError(f"ReportLab font is missing: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "BookSans",
        normal="BookSans",
        bold="BookSans-Bold",
        italic="BookSans-Italic",
        boldItalic="BookSans-BoldItalic",
    )


def color_blend(a: str, b: str, amount: float) -> colors.Color:
    a_rgb = tuple(int(a[i : i + 2], 16) for i in (1, 3, 5))
    b_rgb = tuple(int(b[i : i + 2], 16) for i in (1, 3, 5))
    rgb = tuple(round(x + (y - x) * amount) for x, y in zip(a_rgb, b_rgb))
    return colors.Color(*(component / 255 for component in rgb))


def fit_text(canvas, text: str, x: float, y: float, max_width: float, font: str, size: float) -> None:
    current = size
    while current > 8 and pdfmetrics.stringWidth(text, font, current) > max_width:
        current -= 0.5
    canvas.setFont(font, current)
    canvas.drawString(x, y, text)


def draw_cover(canvas, doc, title: str, subtitle: str, author: str) -> None:
    canvas.saveState()
    width, height = doc.pagesize

    # A subtle vector gradient keeps the cover crisp at any print resolution.
    strips = 160
    strip_height = height / strips
    for i in range(strips):
        t = i / max(1, strips - 1)
        canvas.setFillColor(color_blend("#0b1b2d", "#123c4b", t))
        canvas.rect(0, i * strip_height, width, strip_height + 1, stroke=0, fill=1)

    # Orbit lines and a small network echo the EPUB cover's connected-systems motif.
    cx, cy = width * 0.73, height * 0.80
    try:
        canvas.setStrokeAlpha(0.19)
        canvas.setFillAlpha(0.88)
    except AttributeError:
        pass
    canvas.setStrokeColor(colors.HexColor("#85cfc3"))
    for radius in (0.78 * inch, 1.27 * inch, 1.77 * inch):
        canvas.setLineWidth(0.8)
        canvas.circle(cx, cy, radius, stroke=1, fill=0)
    nodes = [
        (cx, cy),
        (cx, cy + 1.18 * inch),
        (cx + 1.02 * inch, cy - 0.56 * inch),
        (cx - 1.12 * inch, cy - 0.52 * inch),
        (cx + 1.35 * inch, cy + 0.54 * inch),
        (cx - 0.60 * inch, cy + 1.06 * inch),
    ]
    canvas.setStrokeColor(colors.HexColor("#8bd9cc"))
    canvas.setLineWidth(1.1)
    for i, j in ((0, 2), (0, 3), (0, 1), (0, 4), (0, 5)):
        canvas.line(*nodes[i], *nodes[j])
    for index, (x, y) in enumerate(nodes):
        canvas.setFillColor(colors.HexColor("#e4bb74" if index == 0 else "#83ded0"))
        canvas.circle(x, y, 3.8 if index == 0 else 2.8, stroke=0, fill=1)
    try:
        canvas.setStrokeAlpha(1)
        canvas.setFillAlpha(1)
    except AttributeError:
        pass

    margin = 0.72 * inch
    canvas.setFillColor(colors.HexColor("#75d5c6"))
    canvas.roundRect(margin, height * 0.637, 0.52 * inch, 4, 2, stroke=0, fill=1)

    canvas.setFillColor(colors.HexColor("#f4f7f5"))
    canvas.setFont("BookSans-Bold", 30)
    canvas.drawString(margin, height * 0.555, "The Human")
    canvas.drawString(margin, height * 0.495, "Advantage")

    canvas.setFillColor(colors.HexColor("#c5dadd"))
    canvas.setFont("BookSans", 11.8)
    canvas.drawString(margin + 2, height * 0.405, "A Practical Guide to AI, Technology,")
    canvas.drawString(margin + 2, height * 0.375, "and the Future We Choose")

    canvas.setStrokeColor(colors.HexColor("#83bfc1"))
    canvas.setStrokeAlpha(0.52)
    canvas.setLineWidth(0.7)
    canvas.line(margin, height * 0.16, width - margin, height * 0.16)
    try:
        canvas.setStrokeAlpha(1)
    except AttributeError:
        pass
    fit_text(canvas, f"BY {author.upper()}", margin, height * 0.112, width - 2 * margin, "BookSans-Bold", 10)
    canvas.setFillColor(colors.HexColor("#9db9c1"))
    canvas.setFont("BookSans", 7.5)
    canvas.drawString(margin, height * 0.061, "A HUMAN-CENTERED GUIDE FOR A CHANGING WORLD")
    canvas.restoreState()


def draw_page(canvas, doc, title: str, author: str) -> None:
    if doc.page == 1:
        canvas.setTitle(title)
        canvas.setAuthor(author)
        canvas.setSubject("A practical guide to AI, technology, and human-centered choices")
        canvas.setCreator("The Human Advantage ebook builder")
        draw_cover(canvas, doc, title, "A Practical Guide to AI, Technology, and the Future We Choose", author)
        return
    if doc.page == 2:
        return  # keep the title page quiet

    canvas.saveState()
    width, height = doc.pagesize
    left, right = 0.72 * inch, width - 0.72 * inch
    canvas.setFillColor(MUTED)
    canvas.setFont("BookSans-Bold", 7.2)
    canvas.drawString(left, height - 0.43 * inch, "THE HUMAN ADVANTAGE")
    canvas.setFont("BookSans", 7.1)
    canvas.drawRightString(right, height - 0.43 * inch, "AI  ·  TECHNOLOGY  ·  HUMAN CHOICE")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.55)
    canvas.line(left, height - 0.52 * inch, right, height - 0.52 * inch)
    canvas.line(left, 0.52 * inch, right, 0.52 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("BookSans", 8)
    canvas.drawCentredString(width / 2, 0.32 * inch, str(doc.page - 2))
    canvas.restoreState()


class CoverFiller(Flowable):
    """Occupy the first page; its background and artwork are painted by onPage."""

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = avail_height
        return self.width, self.height

    def draw(self):
        pass


class TitlePage(Flowable):
    def __init__(self, title: str, subtitle: str, author: str, width: float, height: float):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = avail_height
        return self.width, self.height

    def draw(self):
        c = self.canv
        mid = self.height * 0.55
        c.setFillColor(TEAL)
        c.roundRect(self.width / 2 - 0.34 * inch, mid + 1.58 * inch, 0.68 * inch, 4, 2, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont("BookSans-Bold", 27)
        c.drawCentredString(self.width / 2, mid + 0.72 * inch, self.title)
        c.setFillColor(MUTED)
        c.setFont("BookSans", 12)
        c.drawCentredString(self.width / 2, mid + 0.28 * inch, "A Practical Guide to AI, Technology,")
        c.drawCentredString(self.width / 2, mid + 0.04 * inch, "and the Future We Choose")
        c.setStrokeColor(RULE)
        c.setLineWidth(0.8)
        c.line(self.width * 0.23, mid - 0.36 * inch, self.width * 0.77, mid - 0.36 * inch)
        c.setFillColor(TEAL)
        c.setFont("BookSans-Bold", 10)
        c.drawCentredString(self.width / 2, mid - 0.73 * inch, f"BY {self.author.upper()}")
        c.setFillColor(MUTED)
        c.setFont("BookSans-Italic", 9.2)
        c.drawCentredString(self.width / 2, mid - 1.25 * inch, "Technology is most useful when it helps people do more of what matters.")


def rich_inline(element: ET.Element) -> str:
    pieces = [escape(element.text or "")]
    for child in element:
        tag = child.tag.rsplit("}", 1)[-1].lower()
        inner = rich_inline(child)
        if tag == "strong":
            inner = f"<b>{inner}</b>"
        elif tag == "em":
            inner = f"<i>{inner}</i>"
        elif tag == "code":
            inner = f'<font name="BookSans-Bold" size="8.5">{inner}</font>'
        elif tag == "a":
            href = escape(child.attrib.get("href", ""), {'"': "&quot;"})
            inner = f'<link href="{href}" color="#167c80">{inner}</link>'
        else:
            inner = f"<{tag}>{inner}</{tag}>"
        pieces.append(inner)
        pieces.append(escape(child.tail or ""))
    return "".join(pieces)


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["BodyText"]
    return {
        "Body": ParagraphStyle(
            "Body",
            parent=base,
            fontName="BookSans",
            fontSize=9.35,
            leading=14.3,
            textColor=INK,
            alignment=TA_LEFT,
            firstLineIndent=12,
            spaceAfter=7.2,
            splitLongWords=1,
            allowWidows=0,
            allowOrphans=0,
        ),
        "BodyNoIndent": ParagraphStyle(
            "BodyNoIndent",
            parent=base,
            fontName="BookSans",
            fontSize=9.35,
            leading=14.3,
            textColor=INK,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceAfter=7.2,
            splitLongWords=1,
        ),
        "ChapterTitle": ParagraphStyle(
            "ChapterTitle",
            parent=base,
            fontName="BookSans-Bold",
            fontSize=22,
            leading=28,
            textColor=NAVY,
            spaceBefore=3,
            spaceAfter=10,
            keepWithNext=1,
            splitLongWords=1,
        ),
        "Subhead": ParagraphStyle(
            "Subhead",
            parent=base,
            fontName="BookSans-Bold",
            fontSize=12.2,
            leading=16,
            textColor=TEAL,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=1,
            splitLongWords=1,
        ),
        "SubheadSmall": ParagraphStyle(
            "SubheadSmall",
            parent=base,
            fontName="BookSans-Bold",
            fontSize=10.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=1,
            splitLongWords=1,
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base,
            fontName="BookSans-Italic",
            fontSize=9.2,
            leading=13.6,
            textColor=INK,
            spaceAfter=0,
            firstLineIndent=0,
        ),
        "Takeaway": ParagraphStyle(
            "Takeaway",
            parent=base,
            fontName="BookSans",
            fontSize=9.1,
            leading=13.5,
            textColor=NAVY,
            firstLineIndent=0,
            spaceAfter=0,
        ),
        "ContentsTitle": ParagraphStyle(
            "ContentsTitle",
            parent=base,
            fontName="BookSans-Bold",
            fontSize=23,
            leading=29,
            textColor=NAVY,
            spaceAfter=18,
        ),
        "TOCEntry": ParagraphStyle(
            "TOCEntry",
            parent=base,
            fontName="BookSans",
            fontSize=9.3,
            leading=16,
            textColor=INK,
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=0,
            spaceAfter=1,
        ),
    }


def list_flowable(element: ET.Element, styles: dict[str, ParagraphStyle]) -> Flowable:
    items = []
    for child in element:
        if child.tag.rsplit("}", 1)[-1].lower() != "li":
            continue
        paragraph = Paragraph(rich_inline(child), styles["BodyNoIndent"])
        items.append(ListItem(paragraph, leftIndent=10, rightIndent=0, spaceAfter=1.5))
    kind = element.tag.rsplit("}", 1)[-1].lower()
    ordered = kind == "ol"
    options = {
        "bulletType": "1" if ordered else "bullet",
        "leftIndent": 21,
        "bulletFontName": "BookSans",
        "bulletFontSize": 8.6,
        "bulletColor": TEAL,
        "bulletDedent": 9,
        "spaceBefore": 2,
        "spaceAfter": 8,
        "bulletOffsetY": 1,
    }
    if ordered:
        options["start"] = "1"
    return ListFlowable(items, **options)


def markdown_flowables(markdown: str, styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    generated = build_ebook.markdown_to_html(markdown)
    root = ET.fromstring(f"<root>{generated}</root>")
    result: list[Flowable] = []
    for block in root:
        tag = block.tag.rsplit("}", 1)[-1].lower()
        if tag == "p":
            markup = rich_inline(block)
            if markup.startswith("<b>Chapter takeaway:</b>"):
                paragraph = Paragraph(markup, styles["Takeaway"])
                table = Table([[paragraph]], colWidths=[None])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                            ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                result.extend([Spacer(1, 3), table, Spacer(1, 9)])
            else:
                result.append(Paragraph(markup, styles["Body"]))
        elif tag in ("h2", "h3", "h4"):
            style = styles["Subhead"] if tag == "h2" else styles["SubheadSmall"]
            result.append(Paragraph(rich_inline(block), style))
        elif tag in ("ul", "ol"):
            result.append(list_flowable(block, styles))
        elif tag == "blockquote":
            paragraphs = [Paragraph(rich_inline(p), styles["Quote"]) for p in block if p.tag.rsplit("}", 1)[-1].lower() == "p"]
            if paragraphs:
                quote = Table([[paragraphs]], colWidths=[None])
                quote.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                            ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
                            ("LEFTPADDING", (0, 0), (-1, -1), 11),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                result.extend([Spacer(1, 3), quote, Spacer(1, 9)])
        elif tag == "hr":
            result.extend([Spacer(1, 4), HRFlowable(width="20%", thickness=1.2, color=TEAL, hAlign="LEFT", spaceBefore=2, spaceAfter=9)])
    return result


class HumanAdvantageDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, title: str, author: str, **kwargs):
        margin_x = 0.72 * inch
        frame = Frame(
            margin_x,
            0.66 * inch,
            PAGE_WIDTH - 2 * margin_x,
            PAGE_HEIGHT - 1.34 * inch,
            id="normal",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            showBoundary=0,
        )
        super().__init__(
            filename,
            pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            leftMargin=margin_x,
            rightMargin=margin_x,
            topMargin=0.72 * inch,
            bottomMargin=0.66 * inch,
            title=title,
            author=author,
            subject="A practical guide to AI, technology, and human-centered choices",
            **kwargs,
        )
        self.addPageTemplates(PageTemplate(id="book", frames=[frame], onPage=lambda c, d: draw_page(c, d, title, author)))

    def afterFlowable(self, flowable):
        key = getattr(flowable, "toc_key", None)
        if key:
            label = getattr(flowable, "toc_label", flowable.getPlainText())
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label, key, level=0, closed=False)
            self.notify("TOCEntry", (0, label, max(1, self.page - 2), key))


def make_chapter_heading(title: str, section_id: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    paragraph = Paragraph(html.escape(title), styles["ChapterTitle"] )
    paragraph.toc_key = f"chapter-{section_id}"
    paragraph.toc_label = title
    return paragraph


def build_pdf() -> None:
    register_fonts()
    metadata, manuscript = build_ebook.parse_front_matter(SOURCE.read_text(encoding="utf-8"))
    sections = build_ebook.split_sections(manuscript)
    title = metadata.get("title", "The Human Advantage")
    subtitle = metadata.get("subtitle", "A Practical Guide to AI, Technology, and the Future We Choose")
    author = metadata.get("author", "Cesar Pedrin")
    styles = make_styles()

    doc = HumanAdvantageDocTemplate(str(OUTPUT), title=title, author=author, pageCompression=1)
    toc = TableOfContents()
    toc.levelStyles = [styles["TOCEntry"]]
    toc.dotsMinLevel = 0

    story: list[Flowable] = [CoverFiller(), PageBreak()]
    story.append(TitlePage(title, subtitle, author, doc.width, doc.height))
    story.extend([PageBreak(), Paragraph("Copyright and a Note to Readers", styles["ChapterTitle"])])
    story.extend(markdown_flowables(sections[1]["body"], styles))
    story.extend([PageBreak(), Paragraph("Contents", styles["ContentsTitle"]), toc])

    for section in sections[2:]:
        story.append(PageBreak())
        story.append(make_chapter_heading(section["title"], section["id"], styles))
        story.append(HRFlowable(width=0.7 * inch, thickness=2, color=TEAL, hAlign="LEFT", spaceBefore=0, spaceAfter=14))
        story.extend(markdown_flowables(section["body"], styles))

    doc.multiBuild(story, maxPasses=5)
    print(f"Built {OUTPUT.name} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"Page size: 6 x 9 inches | PDF metadata author: {author}")


if __name__ == "__main__":
    build_pdf()
