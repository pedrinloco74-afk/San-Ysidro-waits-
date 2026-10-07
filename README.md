# Are They Cheating?

**The No-Nonsense Field Guide to the Truth, the Proof, and the Way Out**
*San Ysidro Press · Field Guide No. 1*

A 30-page, two-column workbook on catching infidelity — written like a field
manual, built to be finished in an evening and used for the next two weeks.

> **EVERY ANSWER YOU NEED** — the truth, the proof, the decision.
> Quietly. Legally. Without warning them. And without losing yourself.

## Deliverables

| File | What it is |
| --- | --- |
| `ebook/Are-They-Cheating.pdf` | Print-ready PDF, 30 pages, 2-column workbook layout, clickable contents + PDF outline |
| `ebook/Are-They-Cheating.epub` | Reflowable EPUB 3 with cover, nav, and all 38 sections |
| `ebook/cover.png` | Cover art, 1800 × 2700 (6 × 9 in at 300 dpi) |

## What's inside

- **Part One — Stop Guessing.** Why your gut is data; the **25 signs that
  actually matter** (ranked by how hard they are to fake); the **Red Flag
  Scorecard** with scored thresholds.
- **Part Two — The Rules of the Hunt.** The **Seven Rules**; **the legal
  line** (what is safe, what needs a lawyer, what is never worth it); building
  a case file that holds up.
- **Part Three — The Playbook.** Phones, money, time, the internet, paperwork,
  and people; **nine questions** that get to the truth; the **14-Day Proof
  Plan**, day by day.
- **Part Four — The Confrontation.** The **five-sentence script**; what they
  will say — the **Cheater's Dictionary**, 25 lines translated; what to do if
  you were wrong.
- **Part Five — Decide, Protect, Recover.** The two roads; protecting your
  safety, health, money, and kids; the first ninety days.
- **Appendices.** The Scorecard, Evidence Log, Master Timeline, One-Page
  Summary worksheets; eight copy-and-use scripts; crisis resources; a
  tonight-only action list.

## Building

```bash
./build.sh          # PDF + EPUB + cover
./build.sh pdf      # PDF only
./build.sh epub     # EPUB only
```

Requires `python3`. On the first run the script creates `.venv` and installs
`reportlab`, `pillow`, `fonttools`, and `brotli`. Fonts (Anton, Inter, Source
Serif 4 — all OFL) are committed under `assets/fonts`, so no network access is
needed to build.

## How it is made

The book is source, not a binary. Words live in Markdown; the layout is
produced by a small purpose-built typesetting engine.

```
src/manuscript/*.md   the book — prose, boxes, tables, scorecards
src/mdparse.py        Markdown-ish parser  -> block tree
src/engine.py         typesetting engine: measurement, wrapping, inline
                      bold/italic, callout boxes, tables, splitting,
                      two-column pagination, running heads, bookmarks
src/build_pdf.py      manuscript -> PDF (ReportLab)
src/build_epub.py     manuscript -> EPUB 3 (zip + XHTML/CSS)
src/fetch_fonts.py    regenerates assets/fonts from @fontsource packages
```

Because pagination is measured rather than estimated, adjusting the type scale
in `src/engine.py` (`class Typo`) re-flows the whole book and the contents page
renumbers itself.

## Notes

- The book is educational material, not legal advice or therapy. It says so on
  the copyright page and repeats the point wherever the law is involved.
- Every legal claim is written jurisdiction-neutral on purpose: the reader is
  told to confirm local law before collecting anything, and Chapter 18 sends
  anyone in danger to a hotline before anything else.

© 2026 San Ysidro Press. First edition.
