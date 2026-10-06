#!/usr/bin/env python3
"""Build the Fieldnotes manuscript as a book-sized, bookmarked PDF."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
PAGE_SIZE = (6 * inch, 9 * inch)

INK = colors.HexColor("#26312d")
INK_DARK = colors.HexColor("#17221e")
MUTED = colors.HexColor("#737c74")
MUTED_DARK = colors.HexColor("#535f58")
LINE = colors.HexColor("#dedbd3")
ACCENT = colors.HexColor("#c65a3e")
ACCENT_DARK = colors.HexColor("#a8422a")
ACCENT_PALE = colors.HexColor("#f6eee8")
FOREST = colors.HexColor("#183b35")
FOREST_LIGHT = colors.HexColor("#254f46")
COVER_PAPER = colors.HexColor("#f1e9da")


def register_fonts() -> None:
    """Use ReportLab's built-in, embeddable Type 1 fonts for a portable PDF."""
    pdfmetrics.registerFontFamily(
        "Times-Roman",
        normal="Times-Roman",
        bold="Times-Bold",
        italic="Times-Italic",
        boldItalic="Times-BoldItalic",
    )


def inline_markup(text: str) -> str:
    code_snippets: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        code_snippets.append(escape(match.group(1)))
        return f"\x00{len(code_snippets) - 1}\x00"

    value = re.sub(r"`([^`]+)`", protect_code, text)
    value = escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", value)
    value = re.sub(
        r"\x00(\d+)\x00",
        lambda match: (
            f'<font name="Courier" size="8.4" color="{ACCENT_DARK.hexval()}">'
            f"{code_snippets[int(match.group(1))]}</font>"
        ),
        value,
    )
    return value


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_divider(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$", line))


def starts_block(lines: list[str], index: int) -> bool:
    line = lines[index] if index < len(lines) else ""
    return bool(
        re.match(r"^#{1,4}\s", line)
        or re.match(r"^>\s?", line)
        or re.match(r"^\s*[-*+]\s+", line)
        or re.match(r"^\s*\d+\.\s+", line)
        or re.match(r"^\s*```", line)
        or re.match(r"^\s*---+\s*$", line)
        or (line.strip().startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1]))
    )


def build_styles():
    sample = getSampleStyleSheet()
    styles = {}
    styles["body"] = ParagraphStyle(
        "BookBody",
        parent=sample["BodyText"],
        fontName="Times-Roman",
        fontSize=10.4,
        leading=16.1,
        textColor=INK,
        spaceAfter=9.5,
        allowWidows=0,
        allowOrphans=0,
        splitLongWords=1,
    )
    styles["body_small"] = ParagraphStyle(
        "BookBodySmall",
        parent=styles["body"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=10.6,
        spaceAfter=0,
    )
    styles["h2"] = ParagraphStyle(
        "BookHeadingTwo",
        fontName="Times-Roman",
        fontSize=18,
        leading=22,
        textColor=INK_DARK,
        spaceBefore=20,
        spaceAfter=8,
        keepWithNext=True,
    )
    styles["h3"] = ParagraphStyle(
        "BookHeadingThree",
        fontName="Times-Bold",
        fontSize=12.1,
        leading=16,
        textColor=INK_DARK,
        spaceBefore=15,
        spaceAfter=6,
        keepWithNext=True,
    )
    styles["chapter_kicker"] = ParagraphStyle(
        "ChapterKicker",
        fontName="Helvetica-Bold",
        fontSize=7.4,
        leading=10,
        textColor=ACCENT_DARK,
        uppercase=True,
        tracking=1.1,
        spaceAfter=10,
    )
    styles["chapter_title"] = ParagraphStyle(
        "ChapterTitle",
        fontName="Times-Roman",
        fontSize=27,
        leading=30,
        textColor=INK_DARK,
        spaceAfter=8,
        keepWithNext=True,
    )
    styles["chapter_summary"] = ParagraphStyle(
        "ChapterSummary",
        fontName="Times-Italic",
        fontSize=11.7,
        leading=16,
        textColor=MUTED_DARK,
        spaceAfter=12,
    )
    styles["chapter_meta"] = ParagraphStyle(
        "ChapterMeta",
        fontName="Helvetica-Bold",
        fontSize=6.7,
        leading=9,
        textColor=MUTED,
        tracking=1.05,
        spaceAfter=20,
    )
    styles["toc_title"] = ParagraphStyle(
        "ContentsTitle",
        fontName="Times-Roman",
        fontSize=27,
        leading=31,
        textColor=INK_DARK,
        spaceAfter=19,
    )
    styles["toc_entry"] = ParagraphStyle(
        "ContentsEntry",
        fontName="Times-Roman",
        fontSize=10,
        leading=16,
        textColor=INK,
        leftIndent=0,
        firstLineIndent=0,
        spaceBefore=1,
        spaceAfter=3,
        backColor=None,
    )
    styles["front_kicker"] = ParagraphStyle(
        "FrontKicker",
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=10,
        textColor=ACCENT_DARK,
        tracking=1.15,
        spaceAfter=16,
    )
    styles["front_title"] = ParagraphStyle(
        "FrontTitle",
        fontName="Times-Roman",
        fontSize=25,
        leading=29,
        textColor=INK_DARK,
        spaceAfter=10,
    )
    styles["front_subtitle"] = ParagraphStyle(
        "FrontSubtitle",
        fontName="Times-Italic",
        fontSize=13,
        leading=18,
        textColor=MUTED_DARK,
        spaceAfter=18,
    )
    styles["front_author"] = ParagraphStyle(
        "FrontAuthor",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=14,
        textColor=INK_DARK,
        tracking=.4,
        spaceAfter=34,
    )
    styles["copyright"] = ParagraphStyle(
        "CopyrightText",
        fontName="Helvetica",
        fontSize=7.7,
        leading=12,
        textColor=MUTED_DARK,
        spaceAfter=8,
    )
    styles["imprint"] = ParagraphStyle(
        "Imprint",
        fontName="Helvetica-Bold",
        fontSize=6.7,
        leading=9,
        textColor=MUTED,
        tracking=1.05,
    )
    return styles


class BookDocument(BaseDocTemplate):
    def __init__(self, filename: str, book: dict, **kwargs):
        self.book = book
        self.left_margin = .68 * inch
        self.right_margin = .62 * inch
        self.top_margin = .77 * inch
        self.bottom_margin = .66 * inch
        super().__init__(
            filename,
            pagesize=PAGE_SIZE,
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
            title=book["title"],
            author=book["author"],
            subject=book["description"],
            creator="Fieldnotes PDF edition",
            pageCompression=1,
            **kwargs,
        )
        width, height = PAGE_SIZE
        cover_frame = Frame(0, 0, width, height, id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        body_frame = Frame(
            self.left_margin,
            self.bottom_margin,
            width - self.left_margin - self.right_margin,
            height - self.top_margin - self.bottom_margin,
            id="body",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=self.draw_cover),
            PageTemplate(id="Body", frames=[body_frame], onPage=self.draw_page_furniture),
        ])

    def beforeDocument(self):
        self.canv.setTitle(self.book["title"])
        self.canv.setAuthor(self.book["author"])
        self.canv.setSubject(self.book["description"])
        self.canv.setCreator("Fieldnotes PDF edition")
        self.canv.setKeywords("data systems, distributed systems, reliability, software architecture")

    def afterFlowable(self, flowable):
        key = getattr(flowable, "bookmark_key", None)
        if key:
            label = flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label, key, level=0, closed=False)
            self.notify("TOCEntry", (0, label, self.page, key))

    def draw_cover(self, canvas, _doc):
        width, height = PAGE_SIZE
        canvas.saveState()
        canvas.setFillColor(FOREST)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        canvas.setFillColor(FOREST_LIGHT)
        canvas.circle(width + 12, height - 42, 148, stroke=0, fill=1)
        canvas.setFillColor(FOREST)
        canvas.circle(width + 12, height - 42, 126, stroke=0, fill=1)

        # Original linework motif: paths and nodes suggest connected systems.
        canvas.setLineWidth(.65)
        canvas.setStrokeColor(colors.HexColor("#718a78"))
        canvas.setDash(1.5, 4)
        path = canvas.beginPath()
        path.moveTo(27, 341)
        path.curveTo(70, 484, 225, 520, 394, 431)
        canvas.drawPath(path, stroke=1, fill=0)
        path = canvas.beginPath()
        path.moveTo(32, 370)
        path.curveTo(117, 288, 270, 299, 401, 388)
        canvas.drawPath(path, stroke=1, fill=0)
        path = canvas.beginPath()
        path.moveTo(70, 525)
        path.curveTo(113, 431, 170, 372, 247, 328)
        canvas.drawPath(path, stroke=1, fill=0)
        canvas.setDash()
        canvas.setStrokeColor(colors.HexColor("#c97a5c"))
        path = canvas.beginPath()
        path.moveTo(36, 365)
        path.curveTo(138, 427, 273, 455, 398, 392)
        canvas.drawPath(path, stroke=1, fill=0)

        nodes = [
            (35, 365, 4.1, colors.HexColor("#df9979")),
            (397, 393, 5.2, COVER_PAPER),
            (247, 328, 3.8, colors.HexColor("#d6bd91")),
            (70, 525, 3.5, colors.HexColor("#d6bd91")),
        ]
        for x, y, radius, color in nodes:
            canvas.setFillColor(color)
            canvas.circle(x, y, radius, stroke=0, fill=1)
        canvas.setStrokeColor(colors.HexColor("#d6bd91"))
        canvas.setLineWidth(.6)
        canvas.circle(397, 393, 13, stroke=1, fill=0)
        canvas.setFillColor(COVER_PAPER)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(39, height - 40, "FIELDNOTES")
        canvas.setFillColor(colors.HexColor("#c4b99f"))
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(width - 39, height - 40, "NO. 01  /  2026")

        canvas.setFillColor(COVER_PAPER)
        canvas.setFont("Times-Roman", 34)
        canvas.drawString(39, 286, "Systems")
        canvas.drawString(39, 249, "that keep")
        canvas.setFillColor(colors.HexColor("#df9979"))
        canvas.setFont("Times-Italic", 33)
        canvas.drawString(39, 212, "their promises.")

        canvas.setFillColor(colors.HexColor("#d9d0bc"))
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(41, 177, "A FIELD GUIDE TO BUILDING")
        canvas.drawString(41, 165, "DEPENDABLE DATA PRODUCTS")
        canvas.setStrokeColor(colors.HexColor("#5c7467"))
        canvas.line(39, 83, width - 39, 83)
        canvas.setFillColor(COVER_PAPER)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(39, 59, self.book["author"].upper())
        canvas.setFillColor(colors.HexColor("#c4b99f"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(width - 39, 59, "FIRST DIGITAL EDITION")
        canvas.restoreState()

    def draw_page_furniture(self, canvas, doc):
        width, height = PAGE_SIZE
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.5)
        canvas.line(self.left_margin, height - .48 * inch, width - self.right_margin, height - .48 * inch)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Bold", 6.4)
        canvas.drawString(self.left_margin, height - .38 * inch, "FIELDNOTES  /  SYSTEMS")
        canvas.setFont("Helvetica", 6.4)
        canvas.drawRightString(width - self.right_margin, height - .38 * inch, self.book["author"].upper())
        canvas.line(self.left_margin, .44 * inch, width - self.right_margin, .44 * inch)
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.left_margin, .29 * inch, "SYSTEMS THAT KEEP THEIR PROMISES")
        canvas.setFillColor(INK_DARK)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawRightString(width - self.right_margin, .29 * inch, str(doc.page))
        canvas.restoreState()


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def add_markdown(markdown: str, story: list, styles: dict, content_width: float, hide_first_heading=True):
    lines = markdown.replace("\r", "").splitlines()
    if hide_first_heading:
        first = next((index for index, line in enumerate(lines) if line.strip()), None)
        if first is not None and re.match(r"^#\s+", lines[first]):
            del lines[first]

    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.+?)\s*#*\s*$", line)
        if heading:
            level = min(len(heading.group(1)), 4)
            style = styles["h2"] if level == 2 else styles["h3"]
            story.append(paragraph(inline_markup(heading.group(2)), style))
            index += 1
            continue

        if re.match(r"^\s*```", line):
            code_lines = []
            index += 1
            while index < len(lines) and not re.match(r"^\s*```", lines[index]):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            code_style = ParagraphStyle(
                "CodeBlock",
                fontName="Courier",
                fontSize=8,
                leading=11,
                textColor=INK_DARK,
                leftIndent=9,
                rightIndent=7,
                borderColor=LINE,
                borderWidth=.5,
                borderPadding=7,
                backColor=colors.HexColor("#f6f5f1"),
                spaceBefore=6,
                spaceAfter=12,
            )
            code_html = "<br/>".join(escape(part) if part else "&#160;" for part in code_lines)
            story.append(Paragraph(code_html, code_style))
            continue

        if re.match(r"^\s*---+\s*$", line):
            rule = Table([[""]], colWidths=[.44 * inch], rowHeights=[1])
            rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LINE)]))
            story.extend([Spacer(1, 10), rule, Spacer(1, 10)])
            index += 1
            continue

        if line.strip().startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1]):
            headers = table_cells(line)
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(table_cells(lines[index]))
                index += 1
            cell_style = styles["body_small"]
            table_data = [[paragraph(f"<b>{inline_markup(cell)}</b>", cell_style) for cell in headers]]
            for row in rows:
                table_data.append([
                    paragraph(inline_markup(row[column] if column < len(row) else ""), cell_style)
                    for column in range(len(headers))
                ])
            col_width = content_width / max(1, len(headers))
            table = Table(table_data, colWidths=[col_width] * len(headers), repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeae1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK_DARK),
                ("LINEBELOW", (0, 0), (-1, 0), .7, ACCENT),
                ("LINEBELOW", (0, 1), (-1, -1), .35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([Spacer(1, 5), table, Spacer(1, 9)])
            continue

        if re.match(r"^>\s?", line):
            quote_lines = []
            while index < len(lines) and re.match(r"^>\s?", lines[index]):
                quote_lines.append(re.sub(r"^>\s?", "", lines[index]))
                index += 1
            quote_content = "<br/>".join(inline_markup(part) for part in quote_lines)
            quote_style = ParagraphStyle(
                "QuoteText",
                parent=styles["body"],
                fontSize=9.7,
                leading=14.2,
                textColor=MUTED_DARK,
                spaceAfter=0,
            )
            quote = Table([[Paragraph(quote_content, quote_style)]], colWidths=[content_width], hAlign="LEFT")
            quote.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT_PALE),
                ("LINEBEFORE", (0, 0), (0, -1), 2, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 13),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.extend([Spacer(1, 7), quote, Spacer(1, 8)])
            continue

        unordered = re.match(r"^\s*[-*+]\s+(.+)", line)
        ordered = re.match(r"^\s*\d+\.\s+(.+)", line)
        if unordered or ordered:
            is_ordered = ordered is not None
            expression = r"^\s*\d+\.\s+(.+)" if is_ordered else r"^\s*[-*+]\s+(.+)"
            items = []
            while index < len(lines):
                item = re.match(expression, lines[index])
                if not item:
                    break
                item_paragraph = Paragraph(inline_markup(item.group(1)), styles["body"])
                items.append(ListItem(item_paragraph, leftIndent=10, rightIndent=2, value=None))
                index += 1
            list_flowable = ListFlowable(
                items,
                bulletType="1" if is_ordered else "bullet",
                start="1" if is_ordered else None,
                leftIndent=16,
                bulletFontName="Helvetica",
                bulletFontSize=7.2,
                bulletColor=ACCENT,
                bulletDedent=7,
                spaceBefore=1,
                spaceAfter=8,
            )
            story.append(list_flowable)
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while index < len(lines) and lines[index].strip() and not starts_block(lines, index):
            paragraph_lines.append(lines[index].strip())
            index += 1
        story.append(paragraph(" ".join(inline_markup(part) for part in paragraph_lines), styles["body"]))


def build_pdf(output: Path) -> None:
    register_fonts()
    book = json.loads((ROOT / "book.json").read_text(encoding="utf-8"))
    styles = build_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    page_width = PAGE_SIZE[0]
    content_width = page_width - .68 * inch - .62 * inch
    doc = BookDocument(str(output), book)

    toc = TableOfContents()
    toc.levelStyles = [styles["toc_entry"]]
    toc.dotsMinLevel = 0
    toc.rightColumnWidth = 28
    toc.tableStyle = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ])

    story = [
        Spacer(1, 1),
        NextPageTemplate("Body"),
        PageBreak(),
        Spacer(1, .82 * inch),
        paragraph("FIELDNOTES · FIRST DIGITAL EDITION · 2026", styles["front_kicker"]),
        paragraph(html.escape(book["title"]), styles["front_title"]),
        paragraph(html.escape(book["subtitle"]), styles["front_subtitle"]),
        paragraph(html.escape(book["author"].upper()), styles["front_author"]),
        Table([[""]], colWidths=[.55 * inch], rowHeights=[1], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)])),
        Spacer(1, 17),
        paragraph(f"Copyright © 2026 {html.escape(book['author'])}. All rights reserved.", styles["copyright"]),
        paragraph("This is an original field guide about the design and operation of dependable data products.", styles["copyright"]),
        paragraph("First digital edition, 2026.", styles["copyright"]),
        PageBreak(),
        paragraph("Contents", styles["toc_title"]),
        toc,
        PageBreak(),
    ]

    for index, chapter in enumerate(book["chapters"], start=1):
        if index > 1:
            story.append(PageBreak())
        kicker = paragraph(html.escape(chapter["kicker"].upper()), styles["chapter_kicker"])
        title = paragraph(html.escape(chapter["title"]), styles["chapter_title"])
        title.bookmark_key = f"section-{index:02d}"
        summary = paragraph(html.escape(chapter["summary"]), styles["chapter_summary"])
        meta_label = "OPENING NOTE" if index == 1 else "WORKED DESIGN" if index == len(book["chapters"]) else f"CHAPTER {index - 1:02d} · 08"
        meta = paragraph(f"{meta_label}  ·  CESAR PEDRIN", styles["chapter_meta"])
        story.append(KeepTogether([kicker, title, summary, meta]))
        chapter_path = ROOT / "book" / "chapters" / f"{chapter['id']}.md"
        add_markdown(chapter_path.read_text(encoding="utf-8"), story, styles, content_width, hide_first_heading=True)
        story.extend([
            Spacer(1, 15),
            Table([[paragraph("SYSTEMS THAT KEEP THEIR PROMISES  ·  CESAR PEDRIN", styles["imprint"])]],
                  colWidths=[content_width],
                  style=TableStyle([
                      ("LINEABOVE", (0, 0), (-1, 0), .5, LINE),
                      ("TOPPADDING", (0, 0), (-1, -1), 10),
                      ("LEFTPADDING", (0, 0), (-1, -1), 0),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                  ])),
        ])

    doc.multiBuild(story, maxPasses=8)
    print(f"Built {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "downloads" / "systems-that-keep-their-promises.pdf",
        help="Output PDF path (default: downloads/systems-that-keep-their-promises.pdf)",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    build_pdf(output)


if __name__ == "__main__":
    main()
