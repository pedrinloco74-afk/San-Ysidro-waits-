"""Builds the reflowable EPUB 3 edition of *Are They Cheating?*"""
from __future__ import annotations

import html
import pathlib
import re
import sys
import uuid
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mdparse
from cover import build_cover

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANUSCRIPT = sorted((ROOT / "src" / "manuscript").glob("*.md"))
OUT = ROOT / "ebook" / "Are-They-Cheating.epub"

BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                        "https://sanysidropress.example/are-they-cheating"))
TITLE = "Are They Cheating?"
SUBTITLE = "The No-Nonsense Field Guide to the Truth, the Proof, and the Way Out"
AUTHOR = "San Ysidro Press"

BOX_TITLES = {
    "truth": "The bottom line",
    "keypoints": "Key points",
    "note": "Note",
    "check": "Checklist",
    "watch": "Watch out",
    "legal": "The legal line",
    "donow": "Do it now",
    "script": "Script",
}

CSS = """@charset "utf-8";
html { font-size: 100%; }
body { font-family: "Source Serif 4", Georgia, serif; line-height: 1.5;
       margin: 0 5%; color: #1f242b; }
h1, h2, h3, h4 { font-family: "Inter", "Helvetica Neue", Arial, sans-serif;
       line-height: 1.2; color: #15191e; page-break-after: avoid; }
h1 { font-size: 1.6em; margin: 1.6em 0 0.5em; }
h1.part { font-size: 2.1em; letter-spacing: 0.02em; margin-top: 2.4em;
       text-transform: uppercase; }
h1.part span.part-label { display: block; color: #be3222; font-size: 0.62em;
       letter-spacing: 0.16em; margin-bottom: 0.35em; }
h2 { font-size: 1.18em; margin: 1.5em 0 0.4em; }
h3 { font-size: 1.02em; margin: 1.3em 0 0.35em; }
p { margin: 0 0 0.65em; text-align: left; }
p.lead { font-size: 1.05em; }
ul, ol { margin: 0.2em 0 0.9em 1.1em; padding: 0; }
li { margin-bottom: 0.35em; }
blockquote { margin: 0.8em 0; padding: 0.2em 0 0.2em 0.9em;
       border-left: 3px solid #132234; font-style: italic; }
aside { margin: 1em 0; padding: 0.8em 0.9em; border-radius: 2px; }
aside h3 { font-size: 0.78em; letter-spacing: 0.12em; text-transform: uppercase;
       margin: 0 0 0.5em; color: #be3222; }
aside p, aside li { font-size: 0.95em; }
aside.truth { background: #132234; color: #e8edf4; }
aside.truth h3 { color: #c79a3a; }
aside.truth strong { color: #fff; }
aside.donow { background: #fdf6e7; border: 1px solid #e3cd9c; }
aside.legal { background: #f5f8fc; border: 1px solid #1c3e63; }
aside.legal h3 { color: #1c3e63; }
aside.watch { background: #fdf2f0; border-left: 4px solid #be3222; }
aside.keypoints, aside.check, aside.note { background: #f4f5f7;
       border: 1px solid #d8dce1; }
aside.script { background: #f7f8fa; border-left: 4px solid #132234; }
table { width: 100%; border-collapse: collapse; margin: 0.9em 0 1.1em;
       font-size: 0.92em; }
th, td { text-align: left; vertical-align: top; padding: 0.4em 0.45em;
       border-bottom: 1px solid #e4e7eb; }
th { font-family: "Inter", Arial, sans-serif; font-size: 0.86em;
       letter-spacing: 0.04em; color: #15191e; }
table.score td:first-child { font-weight: 700; width: 2.4em; text-align: center;
       color: #be3222; }
table.score td:last-child { width: 2.2em; }
tr:nth-child(even) td { background: #f6f7f9; }
.pagebreak { page-break-after: always; }
.titlepage { text-align: left; margin-top: 18%; }
.titlepage .kicker { font-family: "Inter", Arial, sans-serif; font-size: 0.8em;
       letter-spacing: 0.18em; color: #c79a3a; text-transform: uppercase; }
.titlepage h1 { font-size: 2.6em; margin: 0.35em 0 0.2em; letter-spacing: 0.01em; }
.titlepage .sub { font-family: "Inter", Arial, sans-serif; font-size: 1.05em;
       color: #be3222; }
.footer-note { font-size: 0.85em; color: #6e7681; }
nav ol { list-style: none; margin-left: 0; }
nav ol ol { margin-left: 1.1em; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def rich(text: str) -> str:
    out = esc(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out, flags=re.S)
    out = re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def render_blocks(blocks, chapter_index):
    """Return (xhtml body, kind, title) for one chapter's worth of blocks."""
    parts = []
    title = ""
    kind = "chapter"
    open_boxes = 0

    for b in blocks:
        if b.kind == "part":
            t = esc(b.title or b.text)
            parts.append(f'<h1 class="part"><span class="part-label">{esc(b.text)}'
                         f'</span>{t}</h1>')
            title = b.text + ": " + (b.title or "")
            kind = "part"
        elif b.kind == "appendix_banner":
            parts.append(f'<h1>{esc(b.text)}: {esc(b.title)}</h1>')
            title = f"{b.text}: {b.title}"
        elif b.kind == "chapter":
            kicker = f'<p class="kicker">{esc(b.title)}</p>' if b.title else ""
            prefix = f"Chapter {b.number}: " if b.number else ""
            parts.append(f"<h1>{kicker}{esc(prefix)}{esc(b.text)}</h1>")
            title = (f"{b.title} " if b.title else "") + b.text
        elif b.kind == "h2":
            parts.append(f"<h2>{esc(b.text)}</h2>")
        elif b.kind == "h3":
            parts.append(f"<h3>{esc(b.text)}</h3>")
        elif b.kind == "p":
            parts.append(f"<p>{rich(b.text)}</p>")
        elif b.kind == "list":
            tag = "ol" if b.meta.get("variant") == "num" else "ul"
            cls = ' class="checklist"' if b.meta.get("variant") == "check" else ""
            items = "".join(f"<li>{rich(i)}</li>" for i in b.items)
            parts.append(f"<{tag}{cls}>{items}</{tag}>")
        elif b.kind == "quote":
            parts.append(f"<blockquote>{rich(b.text)}</blockquote>")
        elif b.kind == "table":
            rows = "".join(
                f"<tr><th>{rich(a)}</th><td>{rich(t)}</td></tr>" if a
                else f"<tr><td colspan='2'>{rich(t)}</td></tr>"
                for a, t in b.rows)
            cap = f"<h3>{esc(b.title)}</h3>" if b.title else ""
            parts.append(f"<table>{cap}{rows}</table>")
        elif b.kind == "score":
            rows = "".join(
                f"<tr><td>{esc(a)}</td><td>{rich(t)}</td><td>&#9744;</td></tr>"
                for a, t in b.rows)
            parts.append("<table class='score'><tbody>" + rows + "</tbody></table>")
        elif b.kind == "script":
            inner = [f"<p>{rich(b.text)}</p>"] if b.text else []
            inner += [f"<p>{rich(c.text)}</p>" for c in b.children if c.kind == "p"]
            for c in b.children:
                if c.kind == "list":
                    inner.append("<ul>" + "".join(
                        f"<li>{rich(i)}</li>" for i in c.items) + "</ul>")
            heading = f"<h3>{esc(b.title or 'Script')}</h3>"
            parts.append(f"<aside class='script'>{heading}{''.join(inner)}</aside>")
        elif b.kind == "box":
            inner = []
            for c in b.children:
                if c.kind == "p":
                    inner.append(f"<p>{rich(c.text)}</p>")
                elif c.kind == "list":
                    inner.append("<ul>" + "".join(
                        f"<li>{rich(i)}</li>" for i in c.items) + "</ul>")
            title_txt = (b.title or BOX_TITLES.get(b.text, "Note"))
            title_txt = title_txt.replace("The short version", "The bottom line")
            cls = b.text if b.text in BOX_TITLES else "note"
            parts.append(f"<aside class='{cls}'><h3>{esc(title_txt)}</h3>"
                         f"{''.join(inner)}</aside>")
        elif b.kind == "pagebreak":
            pass
        elif b.kind == "contents":
            parts.append('<div class="pagebreak"></div>')
    return "\n".join(parts), kind, title


def split_chapters(blocks):
    """Group blocks into documents: front matter, parts/chapters, appendices."""
    docs = []
    current = {"kind": "front", "title": "Read This First", "blocks": [],
               "anchor": "front"}
    started = False

    for b in blocks:
        if b.kind == "titlepage":
            docs.append({"kind": "cover", "title": "", "blocks": [b], "anchor": "cover"})
            continue
        if b.kind == "contents":
            docs.append({"kind": "toc", "title": "Contents", "blocks": [b],
                         "anchor": "contents"})
            continue
        if b.kind == "part" and started:
            docs.append(current)
            current = {"kind": "part", "title": b.text, "blocks": [b],
                       "anchor": slug(b.text), "new_part": True}
            docs.append(current)
            current = {"kind": "chapter", "title": "", "blocks": [], "anchor": None,
                       "part": b.text}
            continue
        if b.kind == "part" and not started:
            started = True
            current = {"kind": "part", "title": b.text, "blocks": [b],
                       "anchor": slug(b.text)}
            docs.append(current)
            current = {"kind": "chapter", "title": "", "blocks": [], "anchor": None,
                       "part": b.text}
            continue
        if b.kind == "chapter":
            if current["blocks"]:
                docs.append(current)
            anchor = slug(f"{b.title or ''} {b.text}")
            current = {"kind": "chapter", "title": b.text, "blocks": [b],
                       "anchor": anchor}
            started = True
            continue
        if b.kind == "appendix_banner":
            if current["blocks"]:
                docs.append(current)
            current = {"kind": "appendix", "title": f"{b.text}: {b.title}",
                       "blocks": [b], "anchor": slug(b.text + b.title)}
            started = True
            continue
        current["blocks"].append(b)

    if current["blocks"]:
        docs.append(current)
    return [d for d in docs if d["blocks"]]


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def build_epub():
    cover = build_cover()
    blocks = mdparse.parse_manuscript(MANUSCRIPT)
    docs = split_chapters(blocks)

    files = {}
    nav_items = []
    spine = ["cover.xhtml", "titlepage.xhtml", "copyright.xhtml", "nav.xhtml"]

    for i, doc in enumerate(docs):
        if doc["kind"] == "cover":
            files["cover.xhtml"] = cover_xhtml()
            continue
        if doc["kind"] == "toc":
            continue
        name = f"ch{i:02d}.xhtml"
        body, kind, title = render_blocks(doc["blocks"], i)
        doc["file"] = name
        doc["resolved_title"] = title or doc.get("title") or "Untitled"
        files[name] = chapter_xhtml(title or doc["title"], body, kind)
        spine.append(name)

    # ---- navigation document (from the same structure)
    for doc in docs:
        if doc["kind"] in ("cover", "toc"):
            continue
        label = doc["resolved_title"]
        if doc.get("new_part"):
            label = doc["title"] + " · " + label
        nav_items.append((label, doc["file"]))

    nav = nav_xhtml(nav_items)
    files["nav.xhtml"] = nav
    files["titlepage.xhtml"] = titlepage_xhtml()
    files["copyright.xhtml"] = copyright_xhtml()

    # ---- package
    manifest = {
        "cover-image": "cover.png",
        "nav": "nav.xhtml",
        "css": "style.css",
    }
    for name in spine:
        manifest[name.replace(".xhtml", "")] = name
    for extra in ("nav.xhtml", "cover.xhtml"):
        pass
    out = ROOT / OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", CONTAINER, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/cover.png", pathlib.Path(cover).read_bytes(),
                   zipfile.ZIP_DEFLATED)
        for name, content in files.items():
            z.writestr(f"OEBPS/{name}", content, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", content_opf(manifest, spine),
                   zipfile.ZIP_DEFLATED)
    print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB, {len(spine)} documents)")
    return out


CONTAINER = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def content_opf(manifest, spine):
    items = []
    for mid, href in manifest.items():
        media = {"png": "image/png", "css": "text/css",
                 "xhtml": "application/xhtml+xml"}[href.rsplit(".", 1)[1]]
        props = ' properties="nav"' if href == "nav.xhtml" else ""
        items.append(f'    <item id="{mid}" href="{href}" '
                     f'media-type="{media}"{props}/>')
    refs = "\n".join(f'    <itemref idref="{s.replace(".xhtml", "")}"/>'
                     for s in spine)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0"
         unique-identifier="bookid" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{BOOK_ID}</dc:identifier>
    <dc:title>{TITLE}: {SUBTITLE}</dc:title>
    <dc:creator>{AUTHOR}</dc:creator>
    <dc:language>en</dc:language>
    <dc:description>A practical 14-day field guide to identifying infidelity,
      gathering lawful evidence, holding the confrontation, and deciding what
      comes next.</dc:description>
    <dc:subject>Family &amp; Relationships</dc:subject>
    <dc:subject>Marriage</dc:subject>
    <dc:subject>Self-Help</dc:subject>
    <meta property="dcterms:modified">2026-10-07T00:00:00Z</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
{chr(10).join(items)}
  </manifest>
  <spine>
{refs}
  </spine>
</package>
"""


def chapter_xhtml(title, body, kind):
    cls = ' class="part"' if kind == "part" else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{esc(title)} — {esc(TITLE)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body}
</body>
</html>
"""


def cover_xhtml():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Cover</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <div style="text-align:center;margin:0;padding:0;">
    <img src="cover.png" alt="{esc(TITLE)}" style="max-width:100%;height:auto;"/>
  </div>
</body>
</html>
"""


def titlepage_xhtml():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Title Page</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
<div class="titlepage">
  <p class="kicker">The No-Nonsense Field Guide</p>
  <h1>Are They<br/>Cheating?</h1>
  <p class="sub">{esc(SUBTITLE)}</p>
  <p class="footer-note">Quietly. Legally. Without warning them. And without
  losing yourself.</p>
  <p>Every answer you need: the 25 signs that matter, the Red Flag Scorecard,
  the legal line, the 14-Day Proof Plan, the confrontation script, and the
  Cheater's Dictionary — in one workbook you can finish in an evening and use
  for the next two weeks.</p>
</div>
<div class="pagebreak"></div>
</body>
</html>
"""


def copyright_xhtml():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Copyright</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
<h2>{esc(TITLE)}</h2>
<p>{esc(SUBTITLE)}</p>
<p>Copyright © 2026 San Ysidro Press. All rights reserved. First edition.
Field Guide No. 1.</p>
<p>This book is educational material. It is not legal advice, medical advice,
psychological treatment, or a substitute for any of them. Laws about
surveillance, recording, privacy, and evidence differ by state, province, and
country, and they change. Nothing here authorizes you to break a law where you
live.</p>
<p>If you are in danger, contact emergency services or a domestic violence
hotline before doing anything else in this book. See Appendix C.</p>
<p>No part of this publication may be reproduced, distributed, or transmitted in
any form without prior written permission, except brief quotations in a review.
The advice in this book is general; every relationship, every jurisdiction, and
every person is specific.</p>
</body>
</html>
"""


def nav_xhtml(items):
    lis = "\n".join(f'      <li><a href="{href}">{esc(label)}</a></li>'
                    for label, href in items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"
      xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Contents</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Contents</h1>
    <ol>
{lis}
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="hidden">
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">Cover</a></li>
      <li><a epub:type="toc" href="nav.xhtml">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="{items[0][1] if items else 'nav.xhtml'}">
        Start Reading</a></li>
    </ol>
  </nav>
</body>
</html>
"""


if __name__ == "__main__":
    build_epub()
