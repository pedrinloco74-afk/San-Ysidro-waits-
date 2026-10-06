#!/usr/bin/env python3
"""Build the reflowable EPUB and browser-readable HTML from the Markdown source."""
from __future__ import annotations

import html
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "the-human-advantage.md"
CSS_FILE = ROOT / "book.css"
COVER_FILE = ROOT / "cover.svg"
EPUB_FILE = ROOT / "the-human-advantage.epub"
HTML_FILE = ROOT / "the-human-advantage.html"

XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
ET.register_namespace("", XHTML_NS)
ET.register_namespace("epub", EPUB_NS)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("The manuscript must begin with YAML-style front matter.")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("Could not find the end of manuscript front matter.")
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, text[end + 5 :]


def split_sections(text: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"(?m)^#\s+(.+?)\s*$", text))
    if not matches:
        raise ValueError("The manuscript has no level-one chapter headings.")
    sections: list[dict[str, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        body = text[match.end() : end].strip()
        sections.append({"title": title, "body": body, "id": slugify(title)})
    return sections


def slugify(text: str) -> str:
    value = text.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def inline_markup(text: str) -> str:
    value = html.escape(text, quote=False)
    # Simple, intentionally conservative inline Markdown needed by this manuscript.
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None
    quote_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + inline_markup(" ".join(line.strip() for line in paragraph)) + "</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items and list_kind:
            output.append(f"<{list_kind}>" + "".join(f"<li>{item}</li>" for item in list_items) + f"</{list_kind}>")
            list_items.clear()
        list_kind = None

    def flush_quote() -> None:
        if quote_lines:
            joined = " ".join(line.strip() for line in quote_lines)
            output.append("<blockquote><p>" + inline_markup(joined) + "</p></blockquote>")
            quote_lines.clear()

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue

        heading = re.match(r"^(#{2,6})\s+(.+?)\s*#*\s*$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            flush_quote()
            level = min(len(heading.group(1)), 4)
            heading_text = heading.group(2).strip()
            heading_id = slugify(heading_text)
            output.append(f'<h{level} id="{heading_id}">{inline_markup(heading_text)}</h{level}>')
            continue

        if re.fullmatch(r"(?:---+|\*\*\*+|___+)", stripped):
            flush_paragraph()
            flush_list()
            flush_quote()
            output.append("<hr />")
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            quote_lines.append(re.sub(r"^>\s?", "", stripped))
            continue
        else:
            flush_quote()

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            desired_kind = "ul" if bullet else "ol"
            if list_kind and list_kind != desired_kind:
                flush_list()
            list_kind = desired_kind
            item_text = (bullet or numbered).group(1)
            list_items.append(inline_markup(item_text))
            continue

        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(output)


def xhtml_page(title: str, body: str, body_class: str = "", css_href: str = "../book.css") -> str:
    safe_title = html.escape(title, quote=True)
    class_attr = f' class="{html.escape(body_class, quote=True)}"' if body_class else ""
    safe_css_href = html.escape(css_href, quote=True)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" xml:lang="en" lang="en">
<head>
  <title>{safe_title}</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="{safe_css_href}" />
</head>
<body{class_attr}>
{body}
</body>
</html>
'''


def section_xhtml(section: dict[str, str], index: int) -> str:
    title = section["title"]
    section_type = "chapter"
    if index == 0:
        section_type = "titlepage"
    elif title.lower().startswith("copyright"):
        section_type = "copyright-page"
    elif title.lower().startswith("introduction"):
        section_type = "introduction"
    elif title.lower().startswith("conclusion"):
        section_type = "conclusion"
    elif title.lower().startswith("appendix"):
        section_type = "appendix"
    elif title.lower().startswith("about the author"):
        section_type = "contributors"
    body_class = "title-page" if index == 0 else ""
    body_html = (
        f'<section epub:type="{section_type}" id="{html.escape(section["id"], quote=True)}">'
        f'<h1>{inline_markup(title)}</h1>\n{markdown_to_html(section["body"])}\n</section>'
    )
    return xhtml_page(title, body_html, body_class)


def nav_xhtml(sections: list[dict[str, str]]) -> str:
    entries = []
    for i, section in enumerate(sections):
        href = f'text/section-{i:02d}.xhtml#{html.escape(section["id"], quote=True)}'
        label = html.escape(section["title"])
        entries.append(f'<li><a href="{href}">{label}</a></li>')
    nav_body = f'''<nav epub:type="toc" id="toc">
  <h1>Contents</h1>
  <ol>{''.join(entries)}</ol>
</nav>
<nav epub:type="landmarks" hidden="hidden">
  <h2>Guide</h2>
  <ol>
    <li><a epub:type="cover" href="cover.xhtml">Cover</a></li>
    <li><a epub:type="bodymatter" href="text/section-02.xhtml">Start reading</a></li>
  </ol>
</nav>'''
    return xhtml_page("Contents", nav_body, css_href="book.css")


def cover_xhtml() -> str:
    return '''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
  <title>The Human Advantage — Cover</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" type="text/css" href="book.css" />
  <style>html, body { margin: 0; padding: 0; } .cover { display: block; width: 100%; height: 100vh; object-fit: contain; }</style>
</head>
<body epub:type="cover">
  <section class="cover-page"><img class="cover" src="cover.svg" alt="The Human Advantage: A Practical Guide to AI, Technology, and the Future We Choose, by Cesar Pedrin" /></section>
</body>
</html>
'''


def make_opf(metadata: dict[str, str], sections: list[dict[str, str]], identifier: str, modified: str) -> str:
    title = html.escape(metadata.get("title", "The Human Advantage"))
    creator = html.escape(metadata.get("author", "Cesar Pedrin"))
    language = html.escape(metadata.get("language", "en"))
    date = html.escape(metadata.get("date", "2026-10-06"))
    description = html.escape(metadata.get("subtitle", "A Practical Guide to AI, Technology, and the Future We Choose"))

    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="css" href="book.css" media-type="text/css"/>',
        '<item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="cover-image" href="cover.svg" media-type="image/svg+xml" properties="cover-image"/>',
    ]
    spine = ['<itemref idref="cover-page"/>']
    for i, section in enumerate(sections):
        item_id = f"section-{i:02d}"
        manifest.append(f'<item id="{item_id}" href="text/{item_id}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{item_id}"/>')

    return f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="{OPF_NS}" xmlns:dc="{DC_NS}" version="3.0" unique-identifier="pub-id" xml:lang="{language}">
  <metadata>
    <dc:identifier id="pub-id">{identifier}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator id="creator">{creator}</dc:creator>
    <dc:language>{language}</dc:language>
    <dc:date>{date}</dc:date>
    <dc:description>{description}</dc:description>
    <meta property="dcterms:modified">{modified}</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
    {''.join(manifest)}
  </manifest>
  <spine page-progression-direction="ltr">
    {''.join(spine)}
  </spine>
</package>
'''


def make_browser_html(metadata: dict[str, str], sections: list[dict[str, str]]) -> str:
    title = html.escape(metadata.get("title", "The Human Advantage"))
    subtitle = html.escape(metadata.get("subtitle", "A Practical Guide to AI, Technology, and the Future We Choose"))
    author = html.escape(metadata.get("author", "Cesar Pedrin"))
    toc = []
    article = []
    for i, section in enumerate(sections):
        label = html.escape(section["title"])
        toc.append(f'<li><a href="#{html.escape(section["id"], quote=True)}">{label}</a></li>')
        class_name = " class=\"title-page\"" if i == 0 else ""
        article.append(
            f'<section id="{html.escape(section["id"], quote=True)}"{class_name}>'
            f'<h1>{inline_markup(section["title"])}</h1>\n{markdown_to_html(section["body"])}\n</section>'
        )
    cover_alt = html.escape(f"{title}: {subtitle}, by {author}", quote=True)
    return f'''<!doctype html>
<html lang="{html.escape(metadata.get("language", "en"), quote=True)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{subtitle}" />
  <title>{title} — {subtitle}</title>
  <link rel="stylesheet" href="book.css" />
</head>
<body>
  <header class="cover-page"><img class="cover-image" src="cover.svg" alt="{cover_alt}" /></header>
  <nav class="contents" aria-label="Table of contents">
    <h2>Contents</h2>
    <ol>{''.join(toc)}</ol>
  </nav>
  <main class="book-content">{''.join(article)}</main>
</body>
</html>
'''


def validate_epub(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise ValueError("EPUB mimetype must be the first archive entry.")
        if archive.read("mimetype") != b"application/epub+zip":
            raise ValueError("Invalid EPUB mimetype declaration.")
        for name in names:
            if name.endswith((".xml", ".xhtml", ".opf", ".svg")):
                try:
                    ET.fromstring(archive.read(name))
                except ET.ParseError as error:
                    raise ValueError(f"Invalid XML in {name}: {error}") from error


def main() -> None:
    raw = SOURCE.read_text(encoding="utf-8")
    metadata, body = parse_front_matter(raw)
    sections = split_sections(body)
    css = CSS_FILE.read_text(encoding="utf-8")
    cover = COVER_FILE.read_text(encoding="utf-8")

    title = metadata.get("title", "The Human Advantage")
    author = metadata.get("author", "Cesar Pedrin")
    publication_date = metadata.get("date", "2026-10-06")
    identifier = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"{title}|{author}|{publication_date}"))
    try:
        modified_dt = datetime.strptime(publication_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        modified_dt = datetime.now(timezone.utc)
    modified = modified_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    container = f'''<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="{CONTAINER_NS}" version="1.0">
  <rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
'''
    opf = make_opf(metadata, sections, identifier, modified)
    nav = nav_xhtml(sections)
    cover_page = cover_xhtml()

    with zipfile.ZipFile(EPUB_FILE, "w") as archive:
        info = zipfile.ZipInfo("mimetype", date_time=(2026, 10, 6, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, b"application/epub+zip")
        files: dict[str, str] = {
            "META-INF/container.xml": container,
            "EPUB/package.opf": opf,
            "EPUB/nav.xhtml": nav,
            "EPUB/cover.xhtml": cover_page,
            "EPUB/cover.svg": cover,
            "EPUB/book.css": css,
        }
        for i, section in enumerate(sections):
            files[f"EPUB/text/section-{i:02d}.xhtml"] = section_xhtml(section, i)
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)

    HTML_FILE.write_text(make_browser_html(metadata, sections), encoding="utf-8")
    validate_epub(EPUB_FILE)
    word_count = len(re.findall(r"\b[\w’'-]+\b", body))
    print(f"Built {EPUB_FILE.name} and {HTML_FILE.name}")
    print(f"Sections: {len(sections)} | Approx. manuscript words: {word_count:,}")
    print(f"EPUB size: {EPUB_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
