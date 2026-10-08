# Tijuana Birria — A Short, Illustrated Field Guide

A 19-page cookbook on authentic Tijuana-style birria de res: the specific
beef cuts, the chiles, the big-chain and market shopping guide, a full
master recipe, and how to build a quesabirria. All pictures are real
photographs sourced via web image search (credits on the last page).

## Files

- `Tijuana-Birria-Cookbook.pdf` — the finished book (8 x 10 in, 19 pages)
- `build_book.py` — the build script that generates the PDF
- `photos/` — the 10 photographs used in the book (processed to the exact
  aspect ratios the layout expects)
- `art/` — the original painted-illustration set (unused, kept as an
  alternative style)
- `art_jpg/` — derived JPEG cache for PDF embedding (generated, ignored by git)
- `fonts/` — Playfair Display, Lora and Archivo (SIL OFL, via Fontsource)

## Rebuild

```bash
python3 -m venv .venv            # or use any Python 3.10+
.venv/bin/pip install fpdf2 pillow
.venv/bin/python build_book.py
```

Everything is laid out programmatically — typography, the pot cross-section
diagram, the quesabirria fold sequence, the heat and timing bars, and the
hand-drawn icon set (cow/goat/sheep/pig for meats, plus tacos, chiles,
limes, tortillas, cheese, pots and Tijuana rubber-stamps) — so text edits
in `build_book.py` rebuild cleanly. To swap a photo, replace the
matching file in `photos/` (same name, any reasonable size) and re-run.

Photographs are from public web sources for personal, non-commercial use.
