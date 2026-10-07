# THE EX-FILES — KDP publishing pack

**A Crossword Book for Men Who Are Absolutely Fine: 15 Adult Humour Puzzles About Your Ex**

A ready-to-upload Amazon KDP puzzle book: 15 hand-built, fully verified crossword
puzzles about the ex-girlfriend, written in adult-humour voice, plus a full answer
key and comedy filler pages.

---

## Files to upload

| File | Use it for | KDP setting |
|---|---|---|
| `The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf` | **Paperback interior** | 8.5 x 11 in, **No bleed**, Black & white on **White** paper, **29 pages** |
| `cover/The_Ex_Files_paperback_wrap.pdf` | **Paperback cover** (front + spine + back, 0.125" bleed included) | Upload as the cover PDF |
| `cover/The_Ex_Files_ebook_cover_1600x2560.jpg` | **Kindle eBook cover** | 1600 x 2560 px, 1.6 ratio — exactly what KDP asks for |

The interior PDF already contains the title page, copyright/instructions page, all
15 puzzles, 5 answer-key pages, and the comedy pages. Everything is black text on
white, all fonts are embedded, and no content enters the trim margins.

## Spine width note

The wrap cover was generated for **29 pages on white paper** → spine ≈ **0.065 in**
(total wrap 17.315 x 11.25 in). If you change the page count, regenerate:

```bash
python src/covers.py          # uses pages=29 by default
```

## Trim / paper choices

* **No bleed** is correct here — nothing runs to the edge.
* **White paper** keeps the spine formula used above. If you switch to cream,
  update `per_page` in `src/covers.py` (cream is thicker per page).

---

## Suggested KDP listing copy

**Title:** The Ex-Files

**Subtitle:** A Crossword Book for Men Who Are Absolutely Fine: 15 Adult Humour
Puzzles About Your Ex

**Description** (paste into KDP's description box):

> She kept the dog. You kept the words.
>
> THE EX-FILES is a real crossword book for the man who is doing fine. Completely
> fine. So fine that he has filled fifteen large-print grids with clues about her,
> her new boyfriend, her mother, the group chat that holds him upright, and the
> playlist he has been told to delete twice.
>
> Inside you'll find fifteen original puzzles, each one built around the language
> of the modern breakup — the unsent text, the 2 a.m. spiral, the rebranded dog,
> the speech at her brother's wedding that everybody still brings up.
>
> Also inside: the Ground Rules of the Breakup, a translation of the ten messages
> the group chat will send you in the next thirty days, a promises page you will
> fail, and a scorecard you should not fill in honestly.
>
> - 15 original crossword puzzles, 30–43 answers each
> - Large 8.5 x 11 inch pages, easy to write in
> - Full answer key at the back (nobody saw you turn to it)
> - Adult humour: drinking, swearing, and one clue about the rebound that lands
>
> A perfect gag gift for a friend who says he does not want to talk about it.
> He will laugh. He will finish it. He will absolutely not mention puzzle eleven
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
4. `tools/make_book.py` — builds 15 puzzles, then **verifies every entry**: it
   re-spells each answer from the actual grid letters and checks that every white
   cell belongs to a listed clue. It refuses to write a PDF if anything fails.
5. `src/render.py` / `src/extras.py` / `src/covers.py` — the PDF interior, the
   comedy pages, and the covers. `render.WARNINGS` catches any clue block that
   would run off the page.

Rebuild everything:

```bash
python tools/check_bank.py     # word-bank sanity: A-Z, clue present, no dupes
python tools/make_book.py      # 15 puzzles + verification + interior PDF
python src/covers.py           # ebook cover + paperback wrap
```

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
