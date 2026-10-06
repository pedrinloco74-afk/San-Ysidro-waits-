#!/usr/bin/env python3
"""Build the original Fieldnotes manuscript into a standards-based EPUB 3 file."""

from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "book.json"


def inline(text: str) -> str:
    code_snippets: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        code_snippets.append(html.escape(match.group(1), quote=False))
        return f"\x00{len(code_snippets) - 1}\x00"

    value = re.sub(r"`([^`]+)`", protect_code, text)
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
    value = re.sub(
        r"\x00(\d+)\x00",
        lambda match: f"<code>{code_snippets[int(match.group(1))]}</code>",
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


def render_markdown(markdown: str) -> str:
    lines = markdown.replace("\r", "").splitlines()
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.+?)\s*#*\s*$", line)
        if heading:
            level = min(len(heading.group(1)), 4)
            output.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if re.match(r"^\s*```", line):
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not re.match(r"^\s*```", lines[index]):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            output.append(f"<pre><code>{html.escape(chr(10).join(code_lines), quote=False)}</code></pre>")
            continue

        if re.match(r"^\s*---+\s*$", line):
            output.append("<hr />")
            index += 1
            continue

        if line.strip().startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1]):
            headers = table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(table_cells(lines[index]))
                index += 1
            header_html = "".join(f'<th scope="col">{inline(cell)}</th>' for cell in headers)
            body_html = "".join(
                "<tr>" + "".join(
                    f"<td>{inline(row[column] if column < len(row) else '')}</td>"
                    for column in range(len(headers))
                ) + "</tr>"
                for row in rows
            )
            output.append(f"<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>")
            continue

        if re.match(r"^>\s?", line):
            quote_lines: list[str] = []
            while index < len(lines) and re.match(r"^>\s?", lines[index]):
                quote_lines.append(re.sub(r"^>\s?", "", lines[index]))
                index += 1
            quote_html = "".join(f"<p>{inline(part)}</p>" for part in quote_lines)
            output.append(f"<blockquote>{quote_html}</blockquote>")
            continue

        unordered = re.match(r"^\s*[-*+]\s+(.+)", line)
        ordered = re.match(r"^\s*\d+\.\s+(.+)", line)
        if unordered or ordered:
            is_ordered = ordered is not None
            expression = r"^\s*\d+\.\s+(.+)" if is_ordered else r"^\s*[-*+]\s+(.+)"
            items: list[str] = []
            while index < len(lines):
                item = re.match(expression, lines[index])
                if not item:
                    break
                items.append(f"<li>{inline(item.group(1))}</li>")
                index += 1
            tag = "ol" if is_ordered else "ul"
            output.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        paragraphs = [line.strip()]
        index += 1
        while index < len(lines) and lines[index].strip() and not starts_block(lines, index):
            paragraphs.append(lines[index].strip())
            index += 1
        output.append(f"<p>{inline(' '.join(paragraphs))}</p>")

    return "\n".join(output)


def xhtml(title: str, body: str, *, classes: str = "") -> str:
    class_attribute = f' class="{html.escape(classes, quote=True)}"' if classes else ""
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="styles.css" />
</head>
<body{class_attribute}>
{body}
</body>
</html>
'''


def cover_svg(title: str, subtitle: str, author: str) -> str:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_author = html.escape(author)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="600" height="800" viewBox="0 0 600 800" role="img" aria-labelledby="title desc">
  <title id="title">{safe_title}</title>
  <desc id="desc">{safe_subtitle}, by {safe_author}</desc>
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#214b42"/><stop offset=".58" stop-color="#183a34"/><stop offset="1" stop-color="#102e2a"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#efa57c"/><stop offset="1" stop-color="#ca6548"/></linearGradient>
  </defs>
  <rect width="600" height="800" fill="url(#paper)"/>
  <g fill="none" stroke="#e5d5b2" opacity=".25">
    <circle cx="498" cy="124" r="123"/><circle cx="498" cy="124" r="94"/>
    <path d="M40 242C147 42 423 52 557 202" stroke-dasharray="4 10"/>
    <path d="M38 245c119 130 360 122 516-15" stroke="url(#accent)" stroke-width="2"/>
    <path d="M77 105c81 133 225 228 422 170"/>
    <path d="M169 51c47 107 76 220 85 343"/>
  </g>
  <g fill="url(#accent)" stroke="#f2dfc3" stroke-width="2">
    <circle cx="39" cy="245" r="9"/><circle cx="554" cy="230" r="11"/><circle cx="254" cy="394" r="7"/>
  </g>
  <circle cx="554" cy="230" r="27" fill="none" stroke="#e4d2ab" opacity=".7"/>
  <g fill="#f0e8d8" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="700" letter-spacing="3">
    <text x="50" y="54">FIELDNOTES</text><text x="512" y="54">NO. 01</text>
  </g>
  <g fill="#f1e9da" font-family="Georgia, 'Times New Roman', serif" font-size="70" letter-spacing="-3">
    <text x="50" y="490">Systems</text><text x="50" y="558">that keep</text>
    <text x="50" y="626" fill="#df9979">their promises.</text>
  </g>
  <g fill="#d9d0bc" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="700" letter-spacing="2.4">
    <text x="52" y="671">A FIELD GUIDE TO BUILDING</text><text x="52" y="690">DEPENDABLE DATA PRODUCTS</text>
  </g>
  <path d="M50 730h500" stroke="#e5d5b2" opacity=".32"/>
  <g fill="#f0e8d8" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="700" letter-spacing="2.2">
    <text x="50" y="761">{safe_author.upper()}</text><text x="501" y="761">2026</text>
  </g>
</svg>
'''


def build_epub(output: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    chapters = manifest["chapters"]
    output.parent.mkdir(parents=True, exist_ok=True)

    files: dict[str, bytes] = {}
    files["mimetype"] = b"application/epub+zip"
    files["META-INF/container.xml"] = b'''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''

    cover_name = "cover.svg"
    cover_alt = f"Cover of {manifest['title']}: {manifest['subtitle']}, by {manifest['author']}"
    files[f"EPUB/{cover_name}"] = cover_svg(manifest["title"], manifest["subtitle"], manifest["author"]).encode("utf-8")
    files["EPUB/cover.xhtml"] = xhtml(
        "Cover",
        f'<main epub:type="cover" class="cover-page"><img src="{cover_name}" alt="{html.escape(cover_alt, quote=True)}" /></main>',
        classes="cover-document",
    ).encode("utf-8")

    copyright_body = f'''<main epub:type="copyright-page" class="frontmatter">
  <p class="imprint">FIELDNOTES · FIRST DIGITAL EDITION · 2026</p>
  <h1>{html.escape(manifest['title'])}</h1>
  <p>{html.escape(manifest['subtitle'])}</p>
  <p class="author">{html.escape(manifest['author'])}</p>
  <hr />
  <p>Copyright © 2026 {html.escape(manifest['author'])}. All rights reserved.</p>
  <p>This is an original field guide about the design and operation of dependable data products.</p>
  <p>First digital edition, 2026.</p>
</main>'''
    files["EPUB/copyright.xhtml"] = xhtml("Title and copyright", copyright_body).encode("utf-8")

    nav_items: list[str] = []
    spine_items = ['<itemref idref="cover" linear="yes" />', '<itemref idref="copyright" />']
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="styles" href="styles.css" media-type="text/css" />',
        '<item id="cover-image" href="cover.svg" media-type="image/svg+xml" properties="cover-image" />',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml" />',
        '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml" />',
    ]

    for number, chapter in enumerate(chapters, start=1):
        filename = f"chapter-{number:02d}.xhtml"
        source = ROOT / "book" / "chapters" / f"{chapter['id']}.md"
        content = source.read_text(encoding="utf-8")
        rendered = render_markdown(content)
        chapter_body = f'''<main epub:type="bodymatter" class="chapter">
  <p class="chapter-label">{html.escape(chapter['kicker'])}</p>
  {rendered}
  <p class="chapter-signoff">Systems that keep their promises · Cesar Pedrin</p>
</main>'''
        files[f"EPUB/{filename}"] = xhtml(chapter["title"], chapter_body).encode("utf-8")
        manifest_items.append(f'<item id="chapter-{number:02d}" href="{filename}" media-type="application/xhtml+xml" />')
        spine_items.append(f'<itemref idref="chapter-{number:02d}" />')
        nav_items.append(f'<li><a href="{filename}">{html.escape(chapter["title"])}</a></li>')

    nav_body = f'''<nav epub:type="toc" id="toc">
  <h1>Contents</h1>
  <ol>{''.join(nav_items)}</ol>
</nav>
<nav epub:type="landmarks" hidden="hidden">
  <h2>Guide</h2><ol><li><a epub:type="cover" href="cover.xhtml">Cover</a></li><li><a epub:type="bodymatter" href="chapter-01.xhtml">Start reading</a></li></ol>
</nav>'''
    files["EPUB/nav.xhtml"] = xhtml("Contents", nav_body).encode("utf-8")

    css = '''html { color-scheme: light; }
body { margin: 0 auto; max-width: 44em; padding: 1.25em 1.2em 2em; color: #26312d; font-family: Georgia, "Times New Roman", serif; font-size: 1em; line-height: 1.72; }
h1, h2, h3, h4 { color: #17221e; font-family: Georgia, "Times New Roman", serif; font-weight: 500; line-height: 1.2; }
h1 { margin: .7em 0 .5em; font-size: 2.15em; letter-spacing: -.04em; }
h2 { margin: 1.7em 0 .6em; font-size: 1.5em; letter-spacing: -.025em; }
h3 { margin: 1.5em 0 .5em; font-size: 1.2em; }
p { margin: 0 0 1em; }
strong { color: #17221e; }
blockquote { margin: 1.6em 0; padding: .7em 1.1em; border-left: 2px solid #c65a3e; background: #f6eee8; color: #535f58; }
blockquote p:last-child { margin-bottom: 0; }
li { margin: .35em 0; }
li::marker { color: #c65a3e; }
table { width: 100%; margin: 1.5em 0; border-collapse: collapse; font-family: sans-serif; font-size: .8em; line-height: 1.5; }
th, td { padding: .55em .65em; border-bottom: 1px solid #dedbd3; text-align: left; vertical-align: top; }
th { color: #17221e; }
code { font-family: monospace; font-size: .82em; }
pre { overflow-wrap: anywhere; white-space: pre-wrap; }
hr { width: 3em; margin: 2em auto; border: 0; border-top: 1px solid #cfcac0; }
.cover-document { max-width: none; padding: 0; background: #183a34; }
.cover-page { display: block; margin: 0; padding: 0; text-align: center; }
.cover-page img { display: block; width: 100%; height: auto; max-height: 100vh; object-fit: contain; }
.frontmatter { padding-top: 18vh; }
.imprint, .chapter-label { color: #a8422a; font-family: sans-serif; font-size: .72em; font-weight: bold; letter-spacing: .13em; text-transform: uppercase; }
.author { margin-top: 1.8em; font-family: sans-serif; font-size: .9em; }
.chapter-label { margin: 0 0 1.1em; }
.chapter > h1:first-of-type { margin-top: 0; }
.chapter-signoff { margin-top: 3em; padding-top: 1em; border-top: 1px solid #dedbd3; color: #737c74; font-size: .75em; }
'''
    files["EPUB/styles.css"] = css.encode("utf-8")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_items_xml = "\n    ".join(manifest_items)
    spine_items_xml = "\n    ".join(spine_items)
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:3b7771e7-7357-4724-a6b4-7c49f16fce01</dc:identifier>
    <dc:title>{html.escape(manifest['title'])}</dc:title>
    <dc:creator>{html.escape(manifest['author'])}</dc:creator>
    <dc:language>{html.escape(manifest.get('language', 'en'))}</dc:language>
    <dc:description>{html.escape(manifest['description'])}</dc:description>
    <meta property="dcterms:modified">{timestamp}</meta>
    <meta property="belongs-to-collection" id="series">Fieldnotes</meta>
    <meta refines="#series" property="collection-type">series</meta>
  </metadata>
  <manifest>
    {manifest_items_xml}
  </manifest>
  <spine>
    {spine_items_xml}
  </spine>
</package>
'''
    files["EPUB/content.opf"] = opf.encode("utf-8")

    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("mimetype", files.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for path, content in files.items():
            archive.writestr(path, content, compress_type=zipfile.ZIP_DEFLATED)

    print(f"Built {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes, {len(chapters)} sections)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "downloads" / "systems-that-keep-their-promises.epub",
        help="Output EPUB path (default: downloads/systems-that-keep-their-promises.epub)",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    build_epub(output)


if __name__ == "__main__":
    main()
