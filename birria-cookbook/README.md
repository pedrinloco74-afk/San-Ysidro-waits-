# Tijuana Birria — A Short, Illustrated Field Guide

A 19-page illustrated cookbook on authentic Tijuana-style birria de res:
the specific beef cuts, the chiles, the big-chain and market shopping guide,
a full master recipe, and how to build a quesabirria.

## Files

- `Tijuana-Birria-Cookbook.pdf` — the finished book (8 × 10 in, 19 pages)
- `build_book.py` — the build script that generates the PDF
- `art/` — the 10 painted illustration plates (source PNGs)
- `art_jpg/` — derived JPEG cache for PDF embedding (generated, ignored by git)
- `fonts/` — Playfair Display, Lora and Archivo (SIL OFL, via Fontsource)

## Rebuild

```bash
python3 -m venv .venv            # or use any Python 3.10+
.venv/bin/pip install fpdf2 pillow
.venv/bin/python build_book.py
```

Everything in the book is laid out programmatically — typography, the pot
cross-section diagram, the quesabirria fold sequence, the heat and timing
bars — so text edits in `build_book.py` rebuild cleanly.
