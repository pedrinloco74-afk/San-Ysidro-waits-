# THE EX-FILES — KDP publishing pack

**Author: Cesar Pedrin**

**A Crossword Book for Men Who Are Absolutely Fine: 8 Adult Humour Puzzles About Your Ex**

A ready-to-upload Amazon KDP puzzle book: 8 hand-built, fully verified crossword
puzzles about the ex-girlfriend, written in adult-humour voice, plus a full answer
key and comedy filler pages.

---

## Download the complete KDP kit

The single-file upload kit ZIP contains the four files KDP needs for the Kindle
eBook and paperback, plus a short upload guide and copy-ready listing details.

**KDP upload kit (ZIP):** [Open the ZIP's GitHub file page](https://github.com/pedrinloco74-afk/San-Ysidro-waits-/blob/arena/f6bd7949-san-ysidro-waits/docs/THE_EX_FILES_Cesar_Pedrin_KDP_UPLOAD_KIT.zip) and
choose **Download raw file**. If that download method is blocked, use the
**GitHub source snapshot ZIP** link below; after unzipping it, open the
`kdp_upload_kit/` folder (or its bundled ZIP in `docs/`).

**Fallback — download a ZIP snapshot from GitHub:** [Download repository snapshot](https://codeload.github.com/pedrinloco74-afk/San-Ysidro-waits-/zip/refs/heads/arena%2Ff6bd7949-san-ysidro-waits)

The files are also available individually:

| What | GitHub file page |
|---|---|
| **Paperback interior — PDF (25 pages)** | [Open the print interior](https://github.com/pedrinloco74-afk/San-Ysidro-waits-/blob/arena/f6bd7949-san-ysidro-waits/The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf) |
| **Paperback full cover wrap — PDF** | [Open the paperback wrap](https://github.com/pedrinloco74-afk/San-Ysidro-waits-/blob/arena/f6bd7949-san-ysidro-waits/cover/The_Ex_Files_paperback_wrap.pdf) |
| **Kindle eBook manuscript — EPUB 3** | [Open the Kindle EPUB](https://github.com/pedrinloco74-afk/San-Ysidro-waits-/blob/arena/f6bd7949-san-ysidro-waits/ebook/THE_EX_FILES_kindle.epub) |
| **Kindle cover — JPG (1600 × 2560 px)** | [Open the Kindle cover image](https://github.com/pedrinloco74-afk/San-Ysidro-waits-/blob/arena/f6bd7949-san-ysidro-waits/cover/The_Ex_Files_ebook_cover_1600x2560.jpg) |

No GitHub account is required. On each file page, choose **Download raw file**.
The package is pinned to the build with Cesar Pedrin's author credit and the
current eight-puzzle edition.

---

## Files to upload

### Kindle eBook edition

| File | Use it for | KDP setting |
|---|---|---|
| `ebook/THE_EX_FILES_kindle.epub` | **Kindle eBook manuscript** | Upload as the eBook content file. EPUB is KDP's recommended format |
| `cover/The_Ex_Files_ebook_cover_1600x2560.jpg` | **Kindle eBook cover** | 1600 x 2560 px, 1.6 ratio — exactly what KDP asks for |

The EPUB is sold as a **Kindle eBook**, so it does not use print trim sizes.
It is reflowable EPUB 3 with an EPUB 2 `toc.ncx` fallback, a clickable table of
contents, and both formats of navigation landmarks. Every grid ships as a
high-resolution PNG (1192 px, ~25 KB each) so readers can zoom in on any Kindle
or in the Kindle app; every clue and answer stays as selectable text so font
size, search and dictionary lookup keep working.

### Paperback edition

| File | Use it for | KDP setting |
|---|---|---|
| `The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf` | **Paperback interior** | 8.5 x 11 in, **No bleed**, Black & white on **White** paper, **25 pages** |
| `cover/The_Ex_Files_paperback_wrap.pdf` | **Paperback cover** (front + spine + back, 0.125" bleed included) | Upload as the cover PDF |

The interior PDF already contains the title page, copyright/instructions page, all
8 puzzles, 8 answer-key pages (one per puzzle) and the comedy pages. Everything is black text on
white, all fonts are embedded, and no content enters the trim margins.

## What differs between the two editions

Both editions contain the same 8 puzzles, the same clues and the same answer
key (generated from one build, so they can never disagree).

* **Print** has tick-boxes, the scorecard and blank lines you write on, plus
  page numbers and a spine.
* **eBook** replaces the write-on pages with read-only versions (a note explains
  this), drops page numbers and headers, and adds a clickable contents list.
* The eBook cover is the same artwork as the print front cover, exported at
  KDP's required 1600 x 2560 px.

## Spine width note

The wrap cover was generated for **25 pages on white paper** → spine ≈ **0.056 in**
(total wrap 17.306 x 11.25 in). If you change the page count, regenerate:

```bash
python tools/make_covers.py    # page count lives in PAGES at the top
```

## Trim / paper choices

* **No bleed** is correct here — nothing runs to the edge.
* **White paper** keeps the spine formula used above. If you switch to cream,
  update `PER_PAGE_IN` in `tools/make_covers.py` (cream paper is thicker).

---

## Suggested KDP listing copy

**Title:** The Ex-Files

**Author:** Cesar Pedrin

**Subtitle:** A Crossword Book for Men Who Are Absolutely Fine: 8 Adult Humour
Puzzles About Your Ex

**Description** (paste into KDP's description box):

> She kept the dog. You kept the words.
>
> THE EX-FILES is a real crossword book for the man who is doing fine. Completely
> fine. So fine that he has filled eight large-print grids with clues about her,
> her new boyfriend, her mother, the group chat that holds him upright, and the
> playlist he has been told to delete twice.
>
> Inside you'll find eight original puzzles, each one built around the language
> of the modern breakup — the unsent text, the 2 a.m. spiral, the rebranded dog,
> the speech at her brother's wedding that everybody still brings up.
>
> Also inside: the Ground Rules of the Breakup, a translation of the ten messages
> the group chat will send you in the next thirty days, a promises page you will
> fail, and a scorecard you should not fill in honestly.
>
> - 8 original crossword puzzles, 32–43 answers each
> - Large 8.5 x 11 inch pages, easy to write in
> - Full answer key at the back (nobody saw you turn to it)
> - Adult humour: drinking, swearing, and one clue about the rebound that lands
>
> A perfect gag gift for a friend who says he does not want to talk about it.
> He will laugh. He will finish it. He will absolutely not mention puzzle eight
> to anybody.
>
> 18+ / adult humour. Not for children.

**Keywords:** crossword puzzle books for adults, funny breakup gift for men,
divorce gifts for men, gag gift for him, adult crossword book, large print
crosswords, funny gifts for ex boyfriend, men's humour book

**Categories:** Humor & Entertainment › Puzzles & Games › Crosswords;
Humor & Entertainment › Humor › Love, Sex & Marriage

**Age range:** 18+ (adult humour — keep the DRM/Age guidance and the on-cover
"18+ ADULT HUMOUR" line visible)

---

## How the puzzles are built (and why they're correct)

Amazon puzzle books live and die on errors, so this repo is built to make wrong
answers impossible:

1. `src/bank.py` — **3,022 hand-written answers** (315 themed for the ex-girlfriend
   voice, the rest neutral fill), each with its own clue.
2. `src/crossword.py` — grid utilities, numbering, and a simulated-annealing
   black-square generator (used for the classic-grid experiments).
3. `src/weave.py` — the construction engine. It places each word only where it
   already fits an interlocking grid, so every puzzle is **valid by construction**:
   no accidental runs, no disconnected islands, no duplicate answers. Theme words
   are prioritised until each grid carries a quota of them.
4. `tools/make_book.py` — builds 8 puzzles, then **verifies every entry**: it
   re-spells each answer from the actual grid letters and checks that every white
   cell belongs to a listed clue. It refuses to write a PDF if anything fails.
5. `src/render.py` / `src/extras.py` / `src/cover_design.py` — the PDF interior,
   the comedy pages, and the covers. `render.WARNINGS` catches any clue block
   that would run off the page.

Rebuild everything:

```bash
python tools/check_bank.py     # word-bank sanity: A-Z, clue present, no dupes
python tools/make_book.py      # 8 puzzles + verification + interior PDF
python tools/make_epub.py      # Kindle EPUB (reads build/puzzles.json)
python tools/make_covers.py    # ebook cover PDF+JPG, paperback wrap PDF
python tools/check_cover.py    # text-collision + bounds check on both covers
python tools/make_kdp_kit.py   # refresh docs/ downloads + KDP upload ZIP
```

### About the cover

The front cover carries a real, completed crossword made only from the book's
funny themed answers — CLOSURE, WHISKEY, GHOSTED, DUMPED, UNSENT and MAD — six
words, hand-placed, with three clue call-outs above it and the grid anchored at
the bottom. Fewer, bigger words read better at the size Amazon shows in search
results than a dense grid did. It is drawn as vectors (not a bitmap), so the
wordmark and grid stay sharp at any size.

Page 1 of the print interior draws that same cover routine — same wordmark, same
grid, same answers — scaled to sit inside the trim with 1 in side margins. The
interior has no bleed, so the artwork is set into the page as a framed plate
rather than running off the edge. `src/render.py` calls the one routine in
`src/cover_design.py`, so the paperback and the Kindle edition cannot show
different covers. The cover and title page credit the author, Cesar Pedrin; the
PDF metadata and EPUB creator metadata use the same name.

`tools/make_epub.py` validates its own output: it checks the EPUB `mimetype` is
stored first and uncompressed, parses every XML file, confirms every manifest and
in-page reference resolves, and then walks all 8 puzzles checking that the exact
clue text, every clue number and every answer image made it into the book. It
exits non-zero rather than shipping a broken file.

`build/puzzles.json` holds the machine-readable answer key for every puzzle.

---

## Note on puzzle format

These are **freeform** crosswords: words interlock where they share letters, and
some squares are crossed by two answers while others are not. That format is
standard for activity books (it is what you get when every answer is a real word
from a fixed vocabulary), and the "How the puzzles work" page inside the book
tells the solver how to approach them.

Nothing in this repository is medical, legal, or relationship advice. It is a book
of jokes with correct answers.
