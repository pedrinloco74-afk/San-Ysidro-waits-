"""
Weave construction: build a crossword by repeatedly placing the single best
word that fits the grid so far.

Why not "make a grid, then fill it"? Because filling a fixed dense grid from a
hand-written 3,000-word pool dead-ends constantly (English does not have enough
J's in position two). Weaving inverts the problem: a word is only ever placed
where it already fits, so the finished puzzle is valid BY CONSTRUCTION. Every
white cell belongs to a placed word; everything else becomes a black square, so
there are never any unfillable runs, and connectivity comes free because every
new word must cross an existing one.

Rules enforced on every placement:
  * stays inside the grid
  * matches every letter it crosses, and crosses at least one (keeps it joined)
  * does not run into another word end-to-end
  * does not sit parallel-touching another word (no accidental longer runs)
  * no duplicate answers inside one puzzle
"""

from __future__ import annotations

import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Bank:
    """Word pool with letter/position pattern lookups."""

    def __init__(self, clues: dict, theme: set, min_len=3, max_len=8):
        self.clues = clues
        self.theme = theme
        self.answers = [w for w in clues if min_len <= len(w) <= max_len]
        self.by_letter_pos = defaultdict(list)
        for w in sorted(self.answers):
            for i, ch in enumerate(w):
                self.by_letter_pos[(ch, i)].append(w)

    def candidates(self, ch, pos):
        return self.by_letter_pos.get((ch, pos), ())


class Placed:
    __slots__ = ("word", "d", "r", "c", "cells")

    def __init__(self, word, d, r, c):
        self.word = word
        self.d = d                        # "A" across, "D" down
        self.r, self.c = r, c
        if d == "A":
            self.cells = [(r, c + i) for i in range(len(word))]
        else:
            self.cells = [(r + i, c) for i in range(len(word))]


def _fits(letters, word, d, r, c, size, cell_dir=None):
    """Return the cell list if the word may be placed, else None.

    cell_dir maps each occupied cell to the set of directions already running
    through it, so a word can never swallow another word going the same way.
    """
    L = len(word)
    if r < 0 or c < 0:
        return None
    if d == "A":
        if c + L > size or r >= size:
            return None
        cells = [(r, c + i) for i in range(L)]
    else:
        if r + L > size or c >= size:
            return None
        cells = [(r + i, c) for i in range(L)]

    crossings = 0
    for (rr, cc), ch in zip(cells, word):
        cur = letters.get((rr, cc))
        if cur is None:
            continue
        if cur != ch:
            return None
        if cell_dir is not None and d in cell_dir.get((rr, cc), ()):
            return None                  # would swallow an entry going our way
        crossings += 1
    if crossings == 0:
        return None

    # nothing may touch the word end-to-end
    if d == "A":
        if letters.get((r, c - 1)) or letters.get((r, c + L)):
            return None
    else:
        if letters.get((r - 1, c)) or letters.get((r + L, c)):
            return None

    # flat sides may not run alongside another word
    for (rr, cc) in cells:
        if (rr, cc) in letters:
            continue
        if d == "A":
            if letters.get((rr - 1, cc)) or letters.get((rr + 1, cc)):
                return None
        else:
            if letters.get((rr, cc - 1)) or letters.get((rr, cc + 1)):
                return None
    return cells


def _best_placement(letters, size, bank, used, rng, want_theme,
                    min_len, max_len, bbox, anchors=12, sample=45, cell_dir=None,
                    discourage=frozenset()):
    """Try words crossing a sample of already-placed letters; keep the best."""
    occupied = list(letters.items())
    rng.shuffle(occupied)
    occupied = occupied[:anchors]

    best = None
    for (r, c), ch in occupied:
        for d in ("A", "D"):
            for k in range(0, max_len):
                pool_here = bank.candidates(ch, k)
                if not pool_here:
                    continue
                cand = list(pool_here)
                if len(cand) > sample:
                    rng.shuffle(cand)
                    cand = cand[:sample]
                for w in cand:
                    if w in used or len(w) <= k:
                        continue
                    if not (min_len <= len(w) <= max_len):
                        continue
                    if d == "A":
                        rr, cc = r, c - k
                    else:
                        rr, cc = r - k, c
                    cells = _fits(letters, w, d, rr, cc, size, cell_dir)
                    if cells is None:
                        continue
                    ncross = sum(1 for rc2 in cells if rc2 in letters)
                    rs = [x for x, _y in cells]
                    cs = [y for _x, y in cells]
                    nr0, nr1 = min(bbox[0], min(rs)), max(bbox[1], max(rs))
                    nc0, nc1 = min(bbox[2], min(cs)), max(bbox[3], max(cs))
                    if nr1 - nr0 + 1 > size or nc1 - nc0 + 1 > size:
                        continue
                    area = (nr1 - nr0 + 1) * (nc1 - nc0 + 1)
                    blacks = sum(1 for x in range(nr0, nr1 + 1)
                                 for y in range(nc0, nc1 + 1)
                                 if (x, y) not in letters) + len(w) - ncross
                    fill_ratio = 1.0 - blacks / max(1, area)
                    score = ncross * 17.0 + fill_ratio * 14.0 + len(w) * 0.4
                    if w in bank.theme:
                        score += 7.0 if want_theme else 1.5
                    elif want_theme:
                        score -= 2.5
                    if w in discourage:
                        score -= 4.0
                    score -= rng.random() * 1.5
                    if best is None or score > best[0]:
                        best = (score, w, d, rr, cc, cells)
    return best



def _coverage(placed):
    cov = {}
    for p in placed:
        for rc in p.cells:
            cov[rc] = cov.get(rc, 0) + 1
    return cov


def _rebuild_letters(placed):
    letters = {}
    for p in placed:
        for rc, ch in zip(p.cells, p.word):
            letters[rc] = ch
    return letters


def _repair(letters, placed, bank, used, rng, size, min_len, max_len,
            rounds=600, sample=40, cell_dir=None):
    """Place extra words to cross-check cells that currently sit in only one
    entry. Every white cell must belong to an across AND a down answer."""
    for _ in range(rounds):
        cov = _coverage(placed)
        unchecked = [rc for rc, n in cov.items() if n == 1]
        if not unchecked:
            return True
        rng.shuffle(unchecked)
        best = None
        for (r, c) in unchecked[:36]:
            ch = letters[(r, c)]
            for d in ("A", "D"):
                for k in range(0, max_len):
                    pool_here = bank.candidates(ch, k)
                    if not pool_here:
                        continue
                    cand = list(pool_here)
                    if len(cand) > sample:
                        rng.shuffle(cand)
                        cand = cand[:sample]
                    for w in cand:
                        if w in used or len(w) <= k:
                            continue
                        if not (min_len <= len(w) <= max_len):
                            continue
                        rr, cc = (r, c - k) if d == "A" else (r - k, c)
                        cells = _fits(letters, w, d, rr, cc, size, cell_dir)
                        if cells is None:
                            continue
                        fixed = sum(1 for x in cells if cov.get(x, 0) == 1)
                        new = sum(1 for x in cells if cov.get(x, 0) == 0)
                        ncross_rep = sum(1 for x in cells if cov.get(x, 0))
                        if ncross_rep < 2:
                            continue
                        gain = fixed - new
                        if gain <= 0:
                            continue
                        score = gain * 12.0 + fixed * 3.0 - new * 3.0 + ncross_rep
                        if best is None or score > best[0]:
                            best = (score, w, d, rr, cc, cells)
        if best is None:
            return False
        _s, w, d, rr, cc, cells = best
        placed.append(Placed(w, d, rr, cc))
        used.add(w)
        for rc, ch in zip(cells, w):
            letters[rc] = ch
    return False


def _prune(placed):
    """Drop any word that still has a cell belonging to it alone."""
    while True:
        cov = _coverage(placed)
        bad = [p for p in placed
               if any(cov[rc] == 1 for rc in p.cells)]
        if not bad:
            return placed
        worst = max(bad, key=lambda p: sum(1 for rc in p.cells if cov[rc] == 1))
        placed.remove(worst)
        if len(placed) <= 8:
            return placed

def weave(bank: Bank, size: int, rng: random.Random, target_words: int = 60,
          theme_quota: int = 14, min_len: int = 3, max_len: int = 8,
          seed_word: str | None = None, discourage=frozenset()):
    """Return (letters, placed_words) or None."""
    letters: dict[tuple[int, int], str] = {}
    placed: list[Placed] = []
    used: set[str] = set()
    cell_dir: dict[tuple[int, int], set] = defaultdict(set)

    if seed_word is None:
        seeds = sorted(w for w in bank.theme if 5 <= len(w) <= max_len)
        if not seeds:
            return None
        seed_word = rng.choice(seeds)
    placed.append(Placed(seed_word, "A", size // 2, (size - len(seed_word)) // 2))
    used.add(seed_word)
    for rc, ch in zip(placed[0].cells, seed_word):
        letters[rc] = ch
        cell_dir[rc].add("A")

    bbox = (min(r for r, _ in letters), max(r for r, _ in letters),
            min(c for _, c in letters), max(c for _, c in letters))

    while len(placed) < target_words:
        want_theme = sum(1 for p in placed if p.word in bank.theme) < theme_quota
        best = None
        for anchors in (10, 28, 70):
            best = _best_placement(letters, size, bank, used, rng, want_theme,
                                   min_len, max_len, bbox, anchors=anchors,
                                   cell_dir=cell_dir, discourage=discourage)
            if best is not None:
                break
        if best is None:
            break
        _s, w, d, r, c, cells = best
        placed.append(Placed(w, d, r, c))
        used.add(w)
        for rc, ch in zip(cells, w):
            letters[rc] = ch
            cell_dir[rc].add(d)
        rs = [x for x, _ in cells] + [bbox[0], bbox[1]]
        cs = [y for _, y in cells] + [bbox[2], bbox[3]]
        bbox = (min(rs), max(rs), min(cs), max(cs))

    # best-effort: cross-check as many single-entry cells as we can
    _repair(letters, placed, bank, used, rng, size, min_len, max_len,
            cell_dir=cell_dir)

    if not validate_weave(letters, placed, size, max_len):
        return None
    checked = sum(1 for _rc, n in _coverage(placed).items() if n > 1)
    total = len(letters)
    if len(placed) < 12:
        return None
    return letters, placed, checked / max(1, total)


def validate_weave(letters, placed, size, max_len=8):
    """Every placed word must be exactly one maximal run, and all the white
    cells must form a single connected blob."""
    if not letters:
        return False
    cell_owner = {}
    for p in placed:
        if not (3 <= len(p.word) <= max_len):
            return False
        for rc in p.cells:
            if cell_owner.get(rc, p) is not p and cell_owner[rc] is not p:
                pass
    # each word must be a maximal run in its own direction
    for p in placed:
        d, cells, w = p.d, p.cells, p.word
        for rc, ch in zip(cells, w):
            if letters.get(rc) != ch:
                return False
        r0, c0 = cells[0]
        rN, cN = cells[-1]
        if d == "A":
            if (r0, c0 - 1) in letters or (r0, cN + 1) in letters:
                return False
        else:
            if (r0 - 1, c0) in letters or (rN + 1, c0) in letters:
                return False
    # connectivity
    start = next(iter(letters))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in letters and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == len(letters)


def to_grid(letters):
    """Build a rectangular Grid cropped to the woven content."""
    from crossword import Grid

    if not letters:
        return None, (0, 0)
    r0 = min(r for r, _c in letters)
    r1 = max(r for r, _c in letters)
    c0 = min(c for _, c in letters)
    c1 = max(c for _, c in letters)
    g = Grid(r1 - r0 + 1, c1 - c0 + 1)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) not in letters:
                g.cells[r - r0][c - c0] = True
    return g, (r0, c0)


def number_entries(grid, placed, shift, clues, theme):
    """Standard crossword numbering for the woven grid."""
    from crossword import number_slots

    numbered = number_slots(grid, grid.all_slots())
    lookup = {(d, tuple(cells)): num for (d, cells, num) in numbered}

    entries = []
    for p in placed:
        shifted = tuple((r - shift[0], c - shift[1]) for (r, c) in p.cells)
        num = lookup.get((p.d, shifted))
        if num is None:
            continue
        entries.append({
            "dir": p.d,
            "num": num,
            "answer": p.word,
            "clue": clues[p.word],
            "theme": p.word in theme,
            "cells": shifted,
        })
    entries.sort(key=lambda e: (e["num"], e["dir"]))
    return entries
