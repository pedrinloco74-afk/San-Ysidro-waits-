"""Sanity-check the word bank: lengths, characters, overlaps."""
import re
import sys
from collections import Counter

sys.path.insert(0, "src")
from bank import THEMED, FILL  # noqa: E402

BAD = []
for name, bank in (("THEMED", THEMED), ("FILL", FILL)):
    for w, clue in bank.items():
        if not re.fullmatch(r"[A-Z]+", w):
            BAD.append(f"{name}: '{w}' is not A-Z only")
        if not clue or not clue.strip():
            BAD.append(f"{name}: '{w}' has no clue")
        if len(clue) > 68:
            BAD.append(f"{name}: '{w}' clue long ({len(clue)}): {clue}")

dup = set(THEMED) & set(FILL)
if dup:
    BAD.append(f"word in BOTH banks: {sorted(dup)}")

print("theme words :", len(THEMED))
print("fill words  :", len(FILL))
print("total       :", len(THEMED) + len(FILL))

for bank, label in ((THEMED, "THEMED"), (FILL, "FILL")):
    c = Counter(len(w) for w in bank)
    print(f"{label:7s} by length:", {k: c[k] for k in sorted(c)})

if BAD:
    print("\nPROBLEMS:")
    for b in BAD:
        print("  -", b)
    sys.exit(1)
print("\nBank OK")
