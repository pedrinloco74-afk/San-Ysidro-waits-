# Systems That Keep Their Promises

An original e-book by **Cesar Pedrin**: a practical field guide to the decisions behind dependable data products. The manuscript is organized around product promises, data ownership, durable writes, read models, asynchronous work, partitioning, coordination, and recovery, then brings those ideas together in a worked neighborhood-co-op design.

This is an original work about the broad subject of data-system design; it does not reproduce or adapt the linked book's text, examples, or chapter structure.

## Read the book

- Open `index.html` through a local web server for the responsive reader.
- Download [`downloads/systems-that-keep-their-promises.pdf`](downloads/systems-that-keep-their-promises.pdf) for the book-sized PDF edition.
- Download [`downloads/systems-that-keep-their-promises.epub`](downloads/systems-that-keep-their-promises.epub) for an e-reader.
- The reader supports chapter navigation, whole-book search, dark theme, adjustable type size, reading progress, and printing the current section to PDF.

For a quick local preview:

```sh
python3 -m http.server 4173 --bind 0.0.0.0
```

Then visit `http://localhost:4173`.

## Manuscript and EPUB build

The manuscript source lives in `book/chapters/`; `book.json` contains book metadata and the table of contents. Rebuild the EPUB after editing the manuscript with:

```sh
python3 scripts/build_epub.py
```

The EPUB builder uses only Python's standard library and writes to `downloads/systems-that-keep-their-promises.epub`.

Rebuild the book-sized PDF with ReportLab:

```sh
python3 -m pip install -r requirements-pdf.txt
python3 scripts/build_pdf.py
```

The PDF is written to `downloads/systems-that-keep-their-promises.pdf` with a cover, table of contents, page headers/footers, and chapter bookmarks.
