# The Human Advantage

An original, practical ebook about using AI and everyday technology with human judgment, privacy, attention, and responsibility at the center.

## Files

- `ebook/the-human-advantage.epub` — reflowable EPUB 3 edition.
- `ebook/the-human-advantage.pdf` — print-ready 6 × 9 inch PDF edition.
- `ebook/the-human-advantage.html` — browser-readable edition with a table of contents.
- `ebook/the-human-advantage.md` — editable manuscript.
- `ebook/cover.svg` and `ebook/book.css` — cover artwork and shared styles.

The author is credited as **Cesar Pedrin** in the manuscript, cover, and publishing metadata. The short author biography is based only on the book itself; edit it if you want to add personal details.

## Rebuild

Run `python3 ebook/build_ebook.py` from the repository root to rebuild the EPUB and HTML; that builder uses only Python’s standard library.

To rebuild the PDF, install its optional dependency and run the PDF builder:

```sh
python3 -m pip install -r ebook/requirements-pdf.txt
python3 ebook/build_pdf.py
```
