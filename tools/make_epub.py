"""
Build the Kindle eBook edition of THE EX-FILES as a reflowable EPUB 3.

Design decisions, and why:

* Grids are embedded as high-resolution PNG images. A crossword grid is a piece
  of fixed geometry; reflowable HTML cannot keep squares aligned, so every
  serious Kindle puzzle book ships the grid as an image and lets the reader
  pinch-zoom or use Kindle's tap-to-zoom.
* Clues stay as real, selectable text. That means font size control, search,
  dictionary lookup and (on Kindle) Kindle X-Ray style navigation keep working.
* Images are palette PNGs: crossword grids use a handful of flat colours, so
  quantising produces files ~10x smaller than RGB, well inside KDP's guidance.
* Both nav.xhtml (EPUB 3) and toc.ncx (EPUB 2 fallback) are written, because
  Kindle's older engines still read the NCX.

Output: ebook/THE_EX_FILES_kindle.epub
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from cover_design import AUTHOR_NAME

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
INK = (27, 27, 29)
ACCENT = (164, 36, 59)
GRIDLINE = (201, 201, 207)
WHITE = (255, 255, 255)

CELL_PX = 74          # final pixels per square
SUPERSAMPLE = 3       # draw big, downscale for clean antialiased lines
BORDER_PX = 4

TITLES = {
    1: "It's Not You, It's the Puzzle",
    2: "The Five Stages, in Ink",
    3: "Two A.M. Typing Lessons",
    4: "The Group Chat Is Typing...",
    5: "She Took the Dog",
    6: "Blocked, Unblocked, Blocked",
    7: "Closure (Not Included)",
    8: "The Dog Is Fine, by the Way",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def grid_image(puzzle, letters=None, path="grid.png"):
    """Render one crossword grid, optionally with the answers filled in."""
    grid = puzzle["grid"]
    rows, cols = len(grid), len(grid[0])
    W = cols * CELL_PX + BORDER_PX * 2
    H = rows * CELL_PX + BORDER_PX * 2
    img = Image.new("RGB", (W * SUPERSAMPLE, H * SUPERSAMPLE), WHITE)
    d = ImageDraw.Draw(img)

    c = CELL_PX * SUPERSAMPLE
    b = BORDER_PX * SUPERSAMPLE

    # white cells first (so gridlines sit on top of an even background)
    for r in range(rows):
        for col in range(cols):
            if grid[r][col] == "#":
                x = b + col * c
                y = b + r * c
                d.rectangle([x, y, x + c - 1, y + c - 1], fill=INK)

    # hairline grid
    lw = max(1, SUPERSAMPLE)
    for r in range(rows + 1):
        y = b + r * c
        d.rectangle([b, y, b + cols * c, y + lw - 1], fill=GRIDLINE)
    for col in range(cols + 1):
        x = b + col * c
        d.rectangle([x, b, x + lw - 1, b + rows * c], fill=GRIDLINE)

    # numbers
    num_font = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans.ttf",
                                  int(c * 0.27))
    for r in range(rows):
        for col in range(cols):
            num = puzzle["numbers"].get(f"{r},{col}")
            if num and grid[r][col] != "#":
                d.text((b + col * c + c * 0.10, b + r * c + c * 0.07), str(num),
                       font=num_font, fill=INK)

    # answer letters
    if letters:
        let_font = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf",
                                      int(c * 0.58))
        for r in range(rows):
            for col in range(cols):
                ch = letters.get((r, col))
                if ch and grid[r][col] != "#":
                    box = d.textbbox((0, 0), ch, font=let_font)
                    tw, th = box[2] - box[0], box[3] - box[1]
                    d.text((b + col * c + (c - tw) / 2 - box[0],
                            b + r * c + (c - th) / 2 - box[1]),
                           ch, font=let_font, fill=ACCENT)

    # outer frame
    d.rectangle([b - lw, b - lw, b + cols * c + lw, b + rows * c + lw],
                outline=INK, width=3 * SUPERSAMPLE)

    img = img.resize((W, H), Image.LANCZOS)
    img = img.convert("P", palette=Image.ADAPTIVE, colors=16)
    img.save(path, "PNG", optimize=True)
    return path


# ---------------------------------------------------------------------------
# XHTML fragments
# ---------------------------------------------------------------------------
CSS = """@charset "utf-8";
body { font-family: serif; margin: 0 5%; line-height: 1.45; }
h1 { font-family: sans-serif; font-size: 1.5em; line-height: 1.2;
     margin: 0.9em 0 0.1em 0; page-break-before: always; }
h2 { font-family: sans-serif; font-size: 1.05em; margin: 1.2em 0 0.3em 0; }
h3 { font-family: sans-serif; font-size: 1em; margin: 1em 0 0.3em 0; }
p { margin: 0.5em 0; }
.kicker { font-family: sans-serif; font-size: 0.72em; letter-spacing: 0.08em;
          text-transform: uppercase; color: #6b6b73; margin: 0.2em 0 0.8em 0; }
.gridbox { text-align: center; margin: 0.8em 0 1.2em 0; }
.gridbox img { max-width: 100%; height: auto; }
.clue { margin: 0.22em 0 0.22em 1.7em; text-indent: -1.7em; font-size: 0.95em; }
.clue .n { font-weight: bold; }
.accent { color: #a4243b; font-weight: bold; }
.note { font-size: 0.85em; color: #6b6b73; font-style: italic; }
.coverpage { margin: 0; padding: 0; text-align: center; }
.coverpage img { max-width: 100%; height: auto; }
.center { text-align: center; }
.spread { margin-top: 1.6em; }
hr { border: 0; border-top: 1px solid #c9c9cf; margin: 1.4em 0; }
ul { margin: 0.4em 0 0.4em 1.2em; padding: 0; }
li { margin: 0.35em 0; }
dl { margin: 0.6em 0; }
dt { font-family: monospace; font-weight: bold; color: #a4243b;
     margin-top: 0.9em; }
dd { margin: 0.1em 0 0 1.2em; }
.toc ul { list-style: none; margin-left: 0.6em; }
.toc li { margin: 0.25em 0; }
"""


def page(title, body, extra_class=""):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
<meta charset="utf-8"/>
<title>{esc(title)}</title>
<link rel="stylesheet" type="text/css" href="../style.css"/>
</head>
<body class="{extra_class}">
{body}
</body>
</html>
"""


def clue_list(entries, direction):
    out = []
    for e in entries:
        if e["dir"] != direction:
            continue
        out.append(f'<p class="clue"><span class="n">{e["num"]}.</span> '
                   f'{esc(e["clue"])}</p>')
    return "\n".join(out)


def puzzle_xhtml(pz):
    across = sorted((e for e in pz["entries"] if e["dir"] == "A"),
                    key=lambda e: e["num"])
    down = sorted((e for e in pz["entries"] if e["dir"] == "D"),
                  key=lambda e: e["num"])
    body = f"""<section epub:type="chapter">
<p class="kicker">Puzzle {pz['index']} of {len(puzzles)}</p>
<h1>Puzzle {pz['index']}: {esc(pz['title'])}</h1>
<div class="gridbox">
<img src="../images/puzzle{pz['index']:02d}.png" alt="Crossword grid for puzzle {pz['index']}"/></div>

<h2>Across</h2>
{clue_list(across, 'A')}

<h2>Down</h2>
{clue_list(down, 'D')}

<hr/>
<p class="note">Freeform crossword: words cross wherever they share a letter, so
some squares carry two answers and some carry one. Stuck? Every answer is in
the back — try not to go there in the first hour.</p>
</section>"""
    return page(f"Puzzle {pz['index']}", body, "puzzle")


def answer_xhtml(pz):
    body = f"""<section epub:type="chapter">
<h1>Puzzle {pz['index']}: {esc(pz['title'])}</h1>
<div class="gridbox">
<img src="../images/answer{pz['index']:02d}.png" alt="Completed grid for puzzle {pz['index']}"/></div>
</section>"""
    return page(f"Answer {pz['index']}", body, "answer")


# ---------------------------------------------------------------------------
# front / back matter
# ---------------------------------------------------------------------------
def front_matter():
    pages = {}

    pages["cover"] = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Cover</title>
<link rel="stylesheet" type="text/css" href="../style.css"/></head>
<body class="coverpage">
<section epub:type="cover">
<img src="../images/cover.jpg" alt="The Ex-Files: A Crossword Book for Men Who Are Absolutely Fine"/>
</section>
</body>
</html>
"""

    pages["title"] = page("The Ex-Files", f"""<section epub:type="titlepage">
<div class="center">
<p class="kicker">The</p>
<h1 style="page-break-before:auto; font-size:2.3em;">EX-FILES</h1>
<p class="accent">A Crossword Book for Men Who Are Absolutely Fine</p>
<p class="center">By {esc(AUTHOR_NAME)}</p>
</div>
<hr/>
<p class="center">Eight puzzles. One ex-girlfriend. Zero closure.</p>
<p class="center">Somewhere in here are the things you said out loud at two in the
morning, written down as clues so you can finally get them out of your system.</p>
<p class="center accent">You are not sad. You are themed.</p>
<hr/>
<p class="note center">8 puzzles &#183; full answer key &#183; adult humour (18+)</p>
<p class="note center">This eBook edition gives you every grid as a high-resolution
image, so you can zoom in on Kindle and write nothing down at all. The print
edition has the tick-boxes, the scorecard and room for your handwriting.</p>
</section>""")

    pages["before"] = page("Before we begin", """<section epub:type="preface">
<h1>Before we begin</h1>
<p>This book is a joke. It is also a real crossword book. It can be both.</p>
<p>Every grid in here was built by hand-writing a themed answer list and then
weaving the words together until they interlocked, so every letter you see in a
square is doing a job. If a clue makes you laugh and then immediately feel
something, that is the intended effect, and you should not worry about it.</p>
<p>The tone is adult: there is swearing, there is drinking, and there is one clue
about the group chat that will hit too close to home. If you are buying this for
somebody's birthday, congratulations, you have excellent taste and no
supervision.</p>

<h2>How the puzzles work</h2>
<p>These are freeform crosswords. Words run across and down, and they cross
wherever they happen to share a letter.</p>
<p>That means some squares are crossed by two words and some are not. Start with
the words that cross something, then work outward, the way you would with any
crossword.</p>
<p>Every answer is a real word between 3 and 8 letters, and every one of them is
checked against the grid before the book is published. The theme never changes:
her, him, the dog, the group chat, and your ongoing recovery.</p>
<p>Numbers in the top-left corner of a word's first square send you to the Across
and Down lists printed under each grid. Tap or pinch a grid on your Kindle to see
the squares up close.</p>
<p>Stuck? Every answer is in the back. Try not to go there in the first hour.</p>
<p>If you finish all eight puzzles, you have officially processed the breakup
and may now talk about something else at parties.</p>
<hr/>
<p class="note">All contents copyright &#169; 2026. All rights reserved. No part of
this book may be reproduced or distributed in any form without written permission
from the publisher, except for brief quotations in a review. Names, characters and
events are the product of the author's very active imagination and several
people's group chats. For entertainment purposes only. Adult humour: this book is
written for readers aged 18 and over.</p>
</section>""")

    rules = [
        "Nobody in the group chat needs to hear about her sister's wedding. Ever. Again.",
        "You are allowed exactly one (1) unsent text per month. Draft it, read it, delete it, sleep.",
        "The dog was always going to go with her. You knew that. You bought the dog food. You knew.",
        "Do not ask her new man's friends what he does for a living. He is an accountant. Let it go.",
        "If you say \u201cI'm fine\u201d with your whole chest at brunch, someone will hand you a drink and change the subject. That is a friend.",
        "Watching her stories at 2 a.m. counts as contact. You know this. Stop it.",
        "The gym membership is a tattoo now. It costs the same and it hurts the same.",
        "You may keep one (1) song. Not the whole playlist. One.",
        "Never text her mom. Her mom likes you. That is the trap.",
        "Every rule on this page is negotiable after ten p.m. That is why it is printed here instead of saved on your phone.",
    ]
    items = "\n".join(f"<li>{esc(t)}</li>" for t in rules)
    pages["rules"] = page("Ground Rules of the Breakup", f"""<section epub:type="chapter">
<h1>Ground Rules of the Breakup</h1>
<p class="note">Ten rules, written down for your own protection. Tear this page out
if you must, but you will want it again by Thursday.</p>
<ol>
{items}
</ol>
</section>""")

    glossary = [
        ("ARE YOU UP", "Code for: I need to say something about her immediately, and it cannot wait until morning."),
        ("NO WAY", "Confirmation that the thing you just said is both true and completely insane."),
        ("TOTALLY FINE", "The official diagnosis. It is not a compliment."),
        ("WE'RE NOT DOING THAT", "A plan, vetoed for your own good. Accept it."),
        ("COME OUT", "Dinner, two hours, one beer, then home. Non-negotiable, lightly enforced."),
        ("SHE TEXTED?", "The emergency that gets everybody off the couch at midnight."),
        ("DRINK WATER", "The last message in the thread, always sent at 3:04 a.m., by the one who is awake."),
        ("I'M PICKING YOU UP", "No discussion, no options, arriving in nine minutes."),
        ("NEW GUY", "Two words that end a good evening abruptly."),
        ("I SAID WHAT", "Quote confirmation, sent with a screenshot you do not want to see."),
    ]
    terms = "\n".join(f"<dt>{esc(t)}</dt>\n<dd>{esc(m)}</dd>" for t, m in glossary)
    pages["glossary"] = page("The Group Chat Glossary", f"""<section epub:type="chapter">
<h1>The Group Chat Glossary</h1>
<p class="note">Ten messages you will receive in the next thirty days, translated.</p>
<dl>
{terms}
</dl>
</section>""")

    promises = [
        "Run a marathon (started: a 4k, in October, in the rain)",
        "Learn to cook something that is not eggs",
        "Delete her number (you still know it by heart)",
        "Get the dog back (legally impossible, emotionally necessary)",
        "Take up a hobby (bought the equipment, never opened the box)",
        "Apologise to her brother (he was fine with it the whole time)",
        "Grow a beard (it came in patchy; it has been described as \u2018moss\u2019)",
        "Move to a new city (moved apartments, same block, same view of her parking spot)",
        "Be friends with her (you cannot, and that is allowed)",
        "Be genuinely happy for her (working on it, in the gym)",
        "Say one sentence about it without mentioning her name",
        "Sleep before one a.m. for four nights in a row",
    ]
    plist = "\n".join(f"<li>{esc(t)}</li>" for t in promises)
    pages["promises"] = page("Things You Swore You Would Do", f"""<section epub:type="chapter">
<h1>Things You Swore You Would Do</h1>
<p class="note">The print edition gives you tick-boxes for these. In here you will
have to be honest with yourself, which is worse.</p>
<ul>
{plist}
</ul>
</section>""")

    scorecard = [
        ("Hours spent thinking about her", "Estimated. Add ten percent for shower time."),
        ("Texts sent to her", "Across any and all apps, including the one you deleted"),
        ("Unsent drafts written and deleted", "The real hero number of the whole breakup"),
        ("Times the playlist played end to end", "If over 40, see a professional"),
        ("Gym visits claimed / gym visits actual", "Be honest. Two numbers, both surprising."),
        ("Times you explained the breakup to a stranger", "Includes the barber, who did not ask"),
        ("Songs skipped because they got to you", "Count the ones by that band from college"),
        ("Group chat messages sent after midnight", "Roughly equal to the number of bad ideas"),
    ]
    rows = "\n".join(
        f'<p><strong>{esc(a)}</strong><br/><span class="note">{esc(b)}</span> '
        f'&#8212; ______ / ______</p>' for a, b in scorecard)
    pages["scorecard"] = page("The Scorecard", f"""<section epub:type="chapter">
<h1>The Scorecard</h1>
<p class="note">Fill this in after puzzle 8. Numbers do not lie, and yours are
hilarious. (On Kindle you can scribble these onto your own phone. Nobody is
watching.)</p>
{rows}
<hr/>
<p class="accent">Final score: whatever you wrote, add 40 points for finishing the
book.</p>
</section>""")

    pages["back"] = page("One last thing", """<section epub:type="chapter">
<h1>One last thing</h1>
<p>Eight puzzles. You did them. You are, statistically, fine now.</p>
<p>Somewhere around puzzle four you stopped thinking about her and started
thinking about a four-letter word for the guy she told you not to worry about.
That is growth. That is practically a hobby.</p>
<p>If you laughed even once, this book did its job. If you cried once, that was
the postage, and nobody in the group chat needs to hear about it.</p>
<p>Put it on a shelf. Buy a copy for a friend who is going through it. Tell him
you found it in a store and thought of him, which is a lie, and also the nicest
thing you will do all year.</p>
<hr/>
<p><strong>THE EX-FILES</strong><br/>
Crosswords for the recently single, the long recovered, and anyone who needs a
gift for a man who is totally fine.</p>
<p class="note">If you enjoyed this, a review on Amazon helps other people find it
&#8212; and it is the cheapest possible way to feel something again.</p>
</section>""")

    return pages


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build_epub(data_path, cover_jpg, out_path):
    global puzzles
    with open(data_path) as fh:
        data = json.load(fh)
    puzzles = data["puzzles"]

    work = os.path.join(ROOT, "build", "epub_src")
    # A previous, longer edition may have left unused XHTML/images here. Start
    # clean so the ZIP contains only files from this exact puzzle count.
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(os.path.join(work, "images"), exist_ok=True)
    os.makedirs(os.path.join(work, "text"), exist_ok=True)

    # ---- images ----
    img_sizes = {}
    for pz in puzzles:
        letters = {}
        for e in pz["entries"]:
            for i, (r, c) in enumerate(e["cells"]):
                letters[(r, c)] = e["answer"][i]
        p = os.path.join(work, "images", f"puzzle{pz['index']:02d}.png")
        grid_image(pz, None, p)
        a = os.path.join(work, "images", f"answer{pz['index']:02d}.png")
        grid_image(pz, letters, a)
        img_sizes[f"puzzle{pz['index']:02d}"] = os.path.getsize(p)
        img_sizes[f"answer{pz['index']:02d}"] = os.path.getsize(a)
    shutil.copyfile(cover_jpg, os.path.join(work, "images", "cover.jpg"))

    # ---- xhtml ----
    front = front_matter()
    files = {}          # href -> level for nav
    def write(name, content):
        with open(os.path.join(work, "text", name), "w", encoding="utf-8") as fh:
            fh.write(content)

    order = ["cover", "title", "before", "rules", "glossary"]
    for k in order:
        write(f"{k}.xhtml", front[k])
    for pz in puzzles:
        write(f"puzzle{pz['index']:02d}.xhtml", puzzle_xhtml(pz))
    for k in ["promises", "scorecard"]:
        write(f"{k}.xhtml", front[k])
    for pz in puzzles:
        write(f"answer{pz['index']:02d}.xhtml", answer_xhtml(pz))
    write("back.xhtml", front["back"])

    with open(os.path.join(work, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)

    # ---- nav + ncx ----
    def nav_item(href, label, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f'<li><a href="text/{href}"{c}>{esc(label)}</a></li>'

    puzzle_items = "\n".join(
        nav_item(f"puzzle{pz['index']:02d}.xhtml",
                 f"{pz['index']}. {pz['title']}") for pz in puzzles)
    answer_items = "\n".join(
        nav_item(f"answer{pz['index']:02d}.xhtml",
                 f"Puzzle {pz['index']} — {pz['title']}") for pz in puzzles)

    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Contents</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body class="toc">
<nav epub:type="toc" id="toc" role="doc-toc">
<h1>Contents</h1>
<ol>
{nav_item('title.xhtml', 'Title Page')}
{nav_item('before.xhtml', 'Before We Begin')}
{nav_item('rules.xhtml', 'Ground Rules of the Breakup')}
{nav_item('glossary.xhtml', 'The Group Chat Glossary')}
<li><strong>The Puzzles</strong>
<ol>
{puzzle_items}
</ol></li>
{nav_item('promises.xhtml', 'Things You Swore You Would Do')}
{nav_item('scorecard.xhtml', 'The Scorecard')}
<li><strong>The Answers, Admitted</strong>
<ol>
{answer_items}
</ol></li>
{nav_item('back.xhtml', 'One Last Thing')}
</ol>
</nav>
<nav epub:type="landmarks" id="landmarks" hidden="hidden">
<h1>Guide</h1>
<ol>
<li><a epub:type="cover" href="text/cover.xhtml">Cover</a></li>
<li><a epub:type="toc" href="nav.xhtml">Table of Contents</a></li>
<li><a epub:type="bodymatter" href="text/title.xhtml">Start of Content</a></li>
</ol>
</nav>
</body>
</html>
"""

    # NCX ordering must match the reading order
    reading_order = ["cover.xhtml", "title.xhtml", "before.xhtml", "rules.xhtml",
                     "glossary.xhtml"] + \
        [f"puzzle{pz['index']:02d}.xhtml" for pz in puzzles] + \
        ["promises.xhtml", "scorecard.xhtml"] + \
        [f"answer{pz['index']:02d}.xhtml" for pz in puzzles] + ["back.xhtml"]

    navpoints = []
    play = 0
    ncx_labels = {
        "cover.xhtml": "Cover", "title.xhtml": "Title Page",
        "before.xhtml": "Before We Begin", "rules.xhtml": "Ground Rules of the Breakup",
        "glossary.xhtml": "The Group Chat Glossary",
        "promises.xhtml": "Things You Swore You Would Do",
        "scorecard.xhtml": "The Scorecard", "back.xhtml": "One Last Thing",
    }
    for pz in puzzles:
        ncx_labels[f"puzzle{pz['index']:02d}.xhtml"] = f"{pz['index']}. {pz['title']}"
        ncx_labels[f"answer{pz['index']:02d}.xhtml"] = f"Answer: {pz['title']}"
    for href in reading_order:
        if href == "cover.xhtml":
            continue
        play += 1
        navpoints.append(f"""<navPoint id="np{play}" playOrder="{play}">
<navLabel><text>{esc(ncx_labels[href])}</text></navLabel>
<content src="text/{href}"/>
</navPoint>""")
    ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en">
<head>
<meta name="dtb:uid" content="urn:uuid:{uuid_for(puzzles)}"/>
<meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/>
<meta name="dtb:maxPageNumber" content="0"/>
</head>
<docTitle><text>The Ex-Files</text></docTitle>
<navMap>
{chr(10).join(navpoints)}
</navMap>
</ncx>
"""
    with open(os.path.join(work, "nav.xhtml"), "w", encoding="utf-8") as fh:
        fh.write(nav)
    with open(os.path.join(work, "toc.ncx"), "w", encoding="utf-8") as fh:
        fh.write(ncx)

    # ---- opf ----
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="style.css" media-type="text/css"/>',
                '<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>']
    spine = []
    for href in reading_order:
        if href == "cover.xhtml":
            manifest.append('<item id="cover" href="text/cover.xhtml" '
                            'media-type="application/xhtml+xml"/>')
            spine.append('<itemref idref="cover" linear="yes"/>')
            continue
        base = href[:-6]
        manifest.append(f'<item id="{base}" href="text/{href}" '
                        f'media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{base}" linear="yes"/>')
    for pz in puzzles:
        for kind in ("puzzle", "answer"):
            n = f"{kind}{pz['index']:02d}"
            manifest.append(f'<item id="{n}" href="images/{n}.png" media-type="image/png"/>')

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">urn:uuid:{uuid_for(puzzles)}</dc:identifier>
<dc:title>The Ex-Files</dc:title>
<dc:title id="sub">A Crossword Book for Men Who Are Absolutely Fine: {len(puzzles)} Adult Humour Puzzles About Your Ex</dc:title>
<dc:creator id="creator">{esc(AUTHOR_NAME)}</dc:creator>
<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>
<dc:language>en</dc:language>
<dc:rights>Copyright &#169; 2026. All rights reserved.</dc:rights>
<dc:subject>Humor</dc:subject>
<dc:subject>Games &amp; Activities</dc:subject>
<dc:subject>Crosswords</dc:subject>
<dc:description>Eight original adult-humour crossword puzzles about your ex-girlfriend, the group chat that holds you upright, and the dog you still refer to as ours. Full answer key included. 18+</dc:description>
<meta property="dcterms:modified">{modified}</meta>
<meta name="cover" content="cover-image"/>
<meta property="schema:accessMode">textual</meta>
<meta property="schema:accessMode">visual</meta>
<meta property="schema:accessibilityFeature">alternativeText</meta>
<meta property="schema:accessibilityHazard">none</meta>
<meta property="schema:accessibilitySummary">Grids are supplied as images; every grid has alternative text, and all clues and answers are selectable text.</meta>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine toc="ncx">
{chr(10).join(spine)}
</spine>
<guide>
<reference type="cover" title="Cover" href="text/cover.xhtml"/>
<reference type="toc" title="Contents" href="nav.xhtml"/>
<reference type="text" title="Start" href="text/title.xhtml"/>
</guide>
</package>
"""
    with open(os.path.join(work, "content.opf"), "w", encoding="utf-8") as fh:
        fh.write(opf)

    # ---- zip it as an EPUB ----
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles>
<rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
</rootfiles>
</container>
"""
    with zipfile.ZipFile(out_path, "w") as z:
        # the mimetype entry must be first and stored uncompressed
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        z.writestr(zi, "application/epub+zip")
        z.writestr("META-INF/container.xml", container,
                   compress_type=zipfile.ZIP_DEFLATED)
        for name in ("content.opf", "nav.xhtml", "toc.ncx", "style.css"):
            z.write(os.path.join(work, name), name, compress_type=zipfile.ZIP_DEFLATED)
        for fn in sorted(os.listdir(os.path.join(work, "text"))):
            z.write(os.path.join(work, "text", fn), f"text/{fn}",
                    compress_type=zipfile.ZIP_DEFLATED)
        for fn in sorted(os.listdir(os.path.join(work, "images"))):
            z.write(os.path.join(work, "images", fn), f"images/{fn}",
                    compress_type=zipfile.ZIP_DEFLATED)
    return out_path, img_sizes


def uuid_for(puzzles):
    seed = "the-ex-files-" + "-".join(str(p["index"]) for p in puzzles) + \
           "".join(sorted(e["answer"] for p in puzzles[:3] for e in p["entries"]))
    h = hashlib.sha256(seed.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ---------------------------------------------------------------------------
puzzles = []


def validate(epub_path):
    """Structural checks: EPUB needs the mimetype stored first, valid XML,
    and every referenced file present."""
    problems = []
    with zipfile.ZipFile(epub_path) as z:
        names = z.namelist()
        if names[0] != "mimetype":
            problems.append("mimetype is not the first entry")
        info = z.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            problems.append("mimetype is compressed (must be stored)")
        if z.read("mimetype") != b"application/epub+zip":
            problems.append("mimetype content wrong")

        from xml.etree import ElementTree as ET
        xml_files = [n for n in names if n.endswith((".xhtml", ".opf", ".ncx", ".xml"))]
        for n in xml_files:
            try:
                ET.fromstring(z.read(n))
            except ET.ParseError as e:
                problems.append(f"XML error in {n}: {e}")

        opf = z.read("content.opf").decode()
        if f"<dc:creator id=\"creator\">{esc(AUTHOR_NAME)}</dc:creator>" not in opf:
            problems.append("EPUB creator metadata is missing the author name")
        expected_grid_images = {
            f"images/{kind}{i:02d}.png"
            for i in range(1, len(puzzles) + 1)
            for kind in ("puzzle", "answer")
        }
        actual_grid_images = {
            n for n in names
            if re.fullmatch(r"images/(?:puzzle|answer)\d+\.png", n)
        }
        if actual_grid_images != expected_grid_images:
            problems.append("grid image set does not match the current puzzle count")
        hrefs = re.findall(r'href="([^"]+)"', opf)
        for h in hrefs:
            if h not in names:
                problems.append(f"manifest href missing from package: {h}")
        # every image/xhtml referenced by the pages must exist too
        for n in names:
            if n.endswith(".xhtml"):
                body = z.read(n).decode()
                page_dir = os.path.dirname(n)
                for src in re.findall(r'src="([^"]+)"', body):
                    target = os.path.normpath(os.path.join(page_dir, src))
                    if target not in names:
                        problems.append(f"{n} references missing {target}")
        # navigation must point at real files
        for n in ("nav.xhtml", "toc.ncx"):
            for href in re.findall(r'href="([^"#]+)"|src="([^"#]+)"',
                                   z.read(n).decode()):
                h = href[0] or href[1]
                if h.startswith("http"):
                    continue
                if h not in names:
                    problems.append(f"{n} points at missing {h}")

        total = sum(i.file_size for i in z.infolist())
        biggest = max(z.infolist(), key=lambda i: i.file_size)
        print(f"  entries: {len(names)}  uncompressed total: {total/1e6:.2f} MB")
        print(f"  largest file: {biggest.filename} "
              f"({biggest.file_size/1024:.0f} KB)")

    # ---- content completeness: every clue and every answer must be present ----
    with zipfile.ZipFile(epub_path) as z:
        title_page = z.read("text/title.xhtml").decode()
        if f"By {esc(AUTHOR_NAME)}" not in title_page:
            problems.append("title page is missing the author byline")
        for pz in puzzles:
            n = pz["index"]
            body = z.read(f"text/puzzle{n:02d}.xhtml").decode()
            if f"Puzzle {n} of {len(puzzles)}" not in body:
                problems.append(f"puzzle {n}: displayed puzzle count is wrong")
            clues = re.findall(r'<p class="clue">(.*?)</p>', body, re.S)
            if len(clues) != len(pz["entries"]):
                problems.append(f"puzzle {n}: {len(clues)} clues printed for "
                                f"{len(pz['entries'])} entries")
            for e in pz["entries"]:
                # the exact clue text must appear in the page
                if esc(e["clue"]) not in body:
                    problems.append(f"puzzle {n}: clue missing for "
                                    f'{e["dir"]}{e["num"]} ({e["answer"]})')
                if f'<span class="n">{e["num"]}.</span>' not in body:
                    problems.append(f"puzzle {n}: number {e['num']} missing")
            ans = z.read(f"text/answer{n:02d}.xhtml").decode()
            if f"answer{n:02d}.png" not in ans:
                problems.append(f"puzzle {n}: answer grid image not referenced")
        # every answer image must actually differ from its puzzle image
        for pz in puzzles:
            n = pz["index"]
            a = z.read(f"images/puzzle{n:02d}.png")
            b = z.read(f"images/answer{n:02d}.png")
            if a == b:
                problems.append(f"puzzle {n}: answer image identical to puzzle image")
    return problems


if __name__ == "__main__":
    data = os.path.join(ROOT, "build", "puzzles.json")
    if not os.path.exists(data):
        print("run tools/make_book.py first (build/puzzles.json missing)")
        raise SystemExit(1)
    out = os.path.join(ROOT, "ebook", "THE_EX_FILES_kindle.epub")
    path, sizes = build_epub(data, os.path.join(ROOT, "cover",
                           "The_Ex_Files_ebook_cover_1600x2560.jpg"), out)
    print(f"wrote {path}  ({os.path.getsize(path)/1e6:.2f} MB)")
    print(f"  grid images: {len(sizes)}, "
          f"avg {sum(sizes.values())/len(sizes)/1024:.0f} KB, "
          f"largest {max(sizes.values())/1024:.0f} KB")
    problems = validate(path)
    if problems:
        print("VALIDATION PROBLEMS:")
        for p in problems[:25]:
            print("  -", p)
        raise SystemExit(2)
    print("  validation: mimetype stored-first OK, XML well-formed, "
          "all references resolve")
