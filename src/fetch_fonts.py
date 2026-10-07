#!/usr/bin/env python3
"""Convert the @fontsource woff2 web fonts into TTFs ReportLab can embed.

Fonts are Open Font License (Google Fonts); woff2 files come from the npm
packages @fontsource/{anton,inter,source-serif-4}.  Run once:

    npm --prefix .fontcache install @fontsource/anton @fontsource/inter @fontsource/source-serif-4
    python3 src/fetch_fonts.py
"""
import pathlib, sys
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / ".fontcache" / "node_modules" / "@fontsource"
if not SRC.exists():
    SRC = pathlib.Path("/home/user/.fontdl/node_modules/@fontsource")
DST = ROOT / "assets" / "fonts"
DST.mkdir(parents=True, exist_ok=True)

WANTED = [
    ("anton", "anton-latin-400-normal.woff2", "Anton-Regular.ttf"),
    ("inter", "inter-latin-400-normal.woff2", "Inter-Regular.ttf"),
    ("inter", "inter-latin-400-italic.woff2", "Inter-Italic.ttf"),
    ("inter", "inter-latin-600-normal.woff2", "Inter-SemiBold.ttf"),
    ("inter", "inter-latin-700-normal.woff2", "Inter-Bold.ttf"),
    ("inter", "inter-latin-900-normal.woff2", "Inter-Black.ttf"),
    ("source-serif-4", "source-serif-4-latin-400-normal.woff2", "SourceSerif-Regular.ttf"),
    ("source-serif-4", "source-serif-4-latin-400-italic.woff2", "SourceSerif-Italic.ttf"),
    ("source-serif-4", "source-serif-4-latin-600-normal.woff2", "SourceSerif-SemiBold.ttf"),
    ("source-serif-4", "source-serif-4-latin-700-normal.woff2", "SourceSerif-Bold.ttf"),
    ("source-serif-4", "source-serif-4-latin-700-italic.woff2", "SourceSerif-BoldItalic.ttf"),
]

for pkg, woff2, out in WANTED:
    src = SRC / pkg / "files" / woff2
    if not src.exists():
        sys.exit(f"missing {src}")
    font = TTFont(str(src))
    font.flavor = None          # strips woff2 compression -> plain TTF
    font.save(str(DST / out))
    print(f"{out:28} {src.stat().st_size/1024:7.1f} KB -> {(DST/out).stat().st_size/1024:7.1f} KB")
