#!/usr/bin/env bash
# Builds the ebook: PDF (print-ready, 30 pages) + EPUB 3 + cover art.
#
#   ./build.sh              # build everything
#   ./build.sh pdf          # PDF only
#   ./build.sh epub         # EPUB only
#
# Requirements: python3 (3.10+).  Dependencies are installed into .venv on the
# first run: reportlab, pillow, fonttools, brotli — and the Google/OFL fonts
# are committed in assets/fonts, so no network access is needed.
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
if [ ! -d "$VENV" ]; then
  echo "==> creating virtualenv"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet reportlab pillow fonttools brotli
fi

TARGET="${1:-all}"
case "$TARGET" in
  pdf)  "$VENV/bin/python" src/build_pdf.py ;;
  epub) "$VENV/bin/python" src/build_epub.py ;;
  all)
    "$VENV/bin/python" src/build_pdf.py
    "$VENV/bin/python" src/build_epub.py
    ;;
  *) echo "usage: ./build.sh [pdf|epub|all]" >&2; exit 2 ;;
esac

echo
echo "Artifacts in ebook/:"
ls -lh ebook/ | tail -n +2
