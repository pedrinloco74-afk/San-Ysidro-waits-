"""Assemble the ready-to-upload KDP files and a small listing/setup guide."""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from cover_design import AUTHOR_NAME  # noqa: E402

KIT = ROOT / "kdp_upload_kit"
ZIP_PATH = ROOT / "docs" / "THE_EX_FILES_Cesar_Pedrin_KDP_UPLOAD_KIT.zip"

UPLOADS = [
    (ROOT / "The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf",
     "01_Paperback_Interior_8.5x11_25_pages.pdf"),
    (ROOT / "cover" / "The_Ex_Files_paperback_wrap.pdf",
     "02_Paperback_Full_Cover_Wrap.pdf"),
    (ROOT / "ebook" / "THE_EX_FILES_kindle.epub",
     "03_Kindle_Manuscript.epub"),
    (ROOT / "cover" / "The_Ex_Files_ebook_cover_1600x2560.jpg",
     "04_Kindle_Cover_1600x2560.jpg"),
]
DOC_COPIES = [
    (ROOT / "The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf", ROOT / "docs" / "book.pdf"),
    (ROOT / "ebook" / "THE_EX_FILES_kindle.epub", ROOT / "docs" / "book.epub"),
    (ROOT / "cover" / "The_Ex_Files_ebook_cover_1600x2560.jpg", ROOT / "docs" / "cover.jpg"),
    (ROOT / "cover" / "The_Ex_Files_paperback_wrap.pdf", ROOT / "docs" / "paperback-cover.pdf"),
]

SUBTITLE = ("A Crossword Book for Men Who Are Absolutely Fine: "
            "8 Adult Humour Puzzles About Your Ex")
DESCRIPTION = """She kept the dog. You kept the words.

THE EX-FILES is a real crossword book for the man who is doing fine. Completely
fine. So fine that he has filled eight large-print grids with clues about her,
her new boyfriend, her mother, the group chat that holds him upright, and the
playlist he has been told to delete twice.

Inside you'll find eight original puzzles, each one built around the language
of the modern breakup — the unsent text, the 2 a.m. spiral, the rebranded dog,
the speech at her brother's wedding that everybody still brings up.

Also inside: the Ground Rules of the Breakup, a translation of the ten messages
the group chat will send you in the next thirty days, a promises page you will
fail, and a scorecard you should not fill in honestly.

• 8 original crossword puzzles, 32–43 answers each
• Large 8.5 x 11 inch paperback pages, easy to write in
• Full answer key at the back (nobody saw you turn to it)
• Adult humour: drinking, swearing, and one clue about the rebound that lands

A perfect gag gift for a friend who says he does not want to talk about it.
He will laugh. He will finish it. He will absolutely not mention puzzle eight
to anybody.

18+ / adult humour. Not for children."""

LISTING_DETAILS = f"""THE EX-FILES — AMAZON KDP BOOK DETAILS
========================================

Use these details in KDP's Bookshelf setup. This text file is for copying into
the listing form; it is not a manuscript upload.

Title: The Ex-Files
Subtitle: {SUBTITLE}
Author: {AUTHOR_NAME}
Language: English

DESCRIPTION
-----------
{DESCRIPTION}

KEYWORDS (enter individually)
-----------------------------
crossword puzzle books for adults
funny breakup gift for men
divorce gifts for men
gag gift for him
adult crossword book
large print crosswords
funny gifts for ex boyfriend
men's humour book

SUGGESTED CATEGORIES
--------------------
Humor & Entertainment > Puzzles & Games > Crosswords
Humor & Entertainment > Humor > Love, Sex & Marriage

AGE / CONTENT NOTE
------------------
Adult humour; intended for readers 18 and over. The book is not explicit.

PAPERBACK PRINT SETTINGS
------------------------
Trim size: 8.5 x 11 inches
Interior: black & white on white paper
Bleed: no bleed
Length: 25 pages
Paperback cover: full wrap PDF, including 0.125-inch bleed
The back-cover barcode panel is intentionally blank for KDP's barcode.

KINDLE EBOOK
------------
Manuscript: EPUB 3
Cover: separate JPG, 1600 x 2560 pixels

Author credit is included on the cover/title page and in the EPUB/PDF metadata.
Please use the same author name, “{AUTHOR_NAME}”, in the KDP book-details form.
"""

UPLOAD_GUIDE = """KDP UPLOAD GUIDE — THE EX-FILES
===============================

This kit contains the four upload files, plus a KDP listing-details text file.

PAPERBACK
1. Start a Paperback title in KDP.
2. Enter the title and author exactly as shown in KDP_LISTING_DETAILS.txt.
3. Set trim size to 8.5 x 11 inches, black & white interior, white paper,
   and no bleed.
4. Upload 01_Paperback_Interior_8.5x11_25_pages.pdf as the manuscript.
5. Upload 02_Paperback_Full_Cover_Wrap.pdf as the full cover.
6. The back cover leaves a white barcode panel for KDP. Select a KDP ISBN or
   follow KDP's barcode instructions. If using your own ISBN, check KDP's cover
   template requirements before approval.

KINDLE EBOOK
1. Start a Kindle eBook title in KDP.
2. Enter the same title and author details.
3. Upload 03_Kindle_Manuscript.epub as the manuscript.
4. Upload 04_Kindle_Cover_1600x2560.jpg as the cover.

Before publishing, preview both editions in KDP Previewer and review the
proof/print preview. Categories, keywords, pricing, territories and rights are
selected by you in KDP; the suggested copy is in KDP_LISTING_DETAILS.txt.
"""


def main() -> int:
    for source, _name in UPLOADS:
        if not source.is_file():
            print(f"Missing required deliverable: {source}")
            return 1

    for source, destination in DOC_COPIES:
        if not source.is_file():
            print(f"Missing document download copy source: {source}")
            return 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    KIT.mkdir(parents=True, exist_ok=True)
    for source, name in UPLOADS:
        shutil.copyfile(source, KIT / name)
    (KIT / "KDP_UPLOAD_GUIDE.txt").write_text(UPLOAD_GUIDE, encoding="utf-8")
    (KIT / "KDP_LISTING_DETAILS.txt").write_text(LISTING_DETAILS,
                                                  encoding="utf-8")

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for path in sorted(KIT.iterdir()):
            archive.write(path, arcname=path.name)

    print(f"KDP upload kit: {KIT}")
    print(f"ZIP bundle: {ZIP_PATH} ({ZIP_PATH.stat().st_size:,} bytes)")
    print("Included 4 upload files, a KDP upload guide, and listing details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
