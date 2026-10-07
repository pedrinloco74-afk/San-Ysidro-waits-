"""Generates the front cover (PNG) with Pillow — used by both the PDF and EPUB."""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"

W, H = 1800, 2700
PAD = 150
NAVY = (14, 25, 40)
RED = (190, 50, 34)
GOLD = (201, 158, 62)
WHITE = (255, 255, 255)
OFFWHITE = (219, 227, 237)


def _font(name, size):
    return ImageFont.truetype(str(FONTS / name), int(size))


def _tw(draw, text, font, tracking=0.0):
    w = sum(draw.textlength(ch, font=font) + tracking for ch in text)
    return w - tracking if text else 0


def _tracked(draw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def _fit(draw, text, font_name, target_w, tracking=0.0):
    """Pick the font size that makes `text` close to target_w wide."""
    size = 40
    while size < 900:
        f = _font(font_name, size)
        if _tw(draw, text, f, tracking) > target_w:
            return _font(font_name, size - 2)
        size += 2
    return _font(font_name, 900)


def build_cover(path="ebook/cover.png"):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # background wash: navy at the top fading to near-black at the bottom
    for y in range(H):
        t = (y / H) ** 0.85
        d.line([(0, y), (W, y)],
               fill=(int(20 - 12 * t), int(35 - 23 * t), int(56 - 40 * t)))

    d.rectangle([0, 0, W, 16], fill=GOLD)

    f_kick = _font("Inter-Bold.ttf", 40)
    f_sub = _font("Inter-SemiBold.ttf", 58)
    f_sub2 = _font("Inter-Regular.ttf", 46)
    f_feat = _font("Inter-Bold.ttf", 38)
    f_item = _font("Inter-Regular.ttf", 46)
    f_badge = _font("Anton-Regular.ttf", 72)
    f_foot = _font("Inter-SemiBold.ttf", 36)

    # ---------------------------------------------------------------- head --
    _tracked(d, (PAD, 250), "THE NO-NONSENSE FIELD GUIDE TO THE TRUTH",
             f_kick, GOLD, tracking=5)

    # --------------------------------------------------------------- title --
    fit_w = W - 2 * PAD - 20
    f_are = _fit(d, "ARE THEY", "Anton-Regular.ttf", fit_w, 2)
    f_cheat = _fit(d, "CHEATING?", "Anton-Regular.ttf", fit_w, 2)
    y = 360
    h1 = int(f_are.size * 0.92)
    _tracked(d, (PAD, y), "ARE THEY", f_are, WHITE, tracking=2)
    y += int(h1 * 1.02)
    _tracked(d, (PAD, y), "CHEATING?", f_cheat, WHITE, tracking=2)
    y += int(f_cheat.size * 0.98)

    d.rectangle([PAD + 4, y + 58, PAD + 340, y + 74], fill=RED)
    y += 152

    # ------------------------------------------------------------ subtitle --
    lines = [
        ("EVERY ANSWER YOU NEED.", WHITE, f_sub),
        ("THE TRUTH. THE PROOF. THE DECISION.", GOLD, f_sub),
    ]
    for text, col, f in lines:
        _tracked(d, (PAD, y), text, f, col, tracking=2.5)
        y += int(f.size * 1.38)
    y += 22
    _tracked(d, (PAD, y), "Quietly. Legally. Without warning them.", f_sub2,
             OFFWHITE, tracking=1)
    y += int(f_sub2.size * 1.32)
    _tracked(d, (PAD, y), "And without losing yourself.", f_sub2, OFFWHITE, tracking=1)
    y += int(f_sub2.size * 1.6)

    # --------------------------------------------------------- feature card --
    feats = [
        "The 25 signs that actually matter",
        "The Red Flag Scorecard — score it in 3 minutes",
        "The legal line: what you can look at, and what you cannot",
        "The 14-Day Proof Plan, day by day",
        "The confrontation script, word for word",
        "The Cheater's Dictionary: 25 lines, translated",
    ]
    row_h = 74
    card_h = 118 + row_h * len(feats) + 34
    card_y = y + 26
    d.rectangle([PAD, card_y, W - PAD, card_y + card_h], fill=(247, 249, 251))
    d.rectangle([PAD, card_y, PAD + 20, card_y + card_h], fill=RED)
    iy = card_y + 44
    _tracked(d, (PAD + 62, iy), "INSIDE — AND USE IT TONIGHT", f_feat, RED, tracking=4)
    iy += 74
    for t in feats:
        d.ellipse([PAD + 64, iy + 14, PAD + 82, iy + 32], fill=NAVY)
        _tracked(d, (PAD + 104, iy), t, f_item, (34, 42, 54), tracking=0.4)
        iy += row_h
    card_bottom = card_y + card_h

    # --------------------------------------------------------------- badge --
    by = card_bottom + 92
    bw = _tw(d, "THE 14-DAY PLAN", f_badge, 3) + 80
    d.rectangle([PAD, by, PAD + bw, by + 124], fill=RED)
    _tracked(d, (PAD + 40, by + 26), "THE 14-DAY PLAN", f_badge, WHITE, tracking=3)

    # -------------------------------------------------------------- footer --
    fy = H - 190
    d.rectangle([PAD, fy - 52, W - PAD, fy - 48], fill=(42, 60, 82))
    _tracked(d, (PAD, fy), "SAN YSIDRO PRESS", f_foot, OFFWHITE, tracking=6)
    label = "FIELD GUIDE NO. 1"
    _tracked(d, (W - PAD - _tw(d, label, f_foot, 6), fy), label, f_foot,
             (116, 134, 156), tracking=6)

    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"cover -> {out} {img.size} (badge bottom {by + 124}, footer {fy})")
    return out


if __name__ == "__main__":
    build_cover()
