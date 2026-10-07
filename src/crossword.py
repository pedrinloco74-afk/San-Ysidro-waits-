"""
Crossword engine.

Two jobs:
  1. gen_template()  -> makes a valid, 180-degree-rotationally-symmetric
                        black-square pattern for an NxN grid.
  2. fill()          -> fills that pattern with words from a pool using
                        MRV + forward-checking backtracking.

Validity rules enforced:
  * every maximal run of white cells (across and down) is either length 0
    or length >= 3 and <= MAXRUN
  * all white cells are orthogonally connected
  * black squares are symmetric under 180-degree rotation
  * every white cell is "checked" (part of an across AND a down entry)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

BLACK = "#"


# --------------------------------------------------------------------------
# Grid
# --------------------------------------------------------------------------
class Grid:
    """Rectangular crossword grid. cells[r][c] is True for black squares."""

    __slots__ = ("rows", "cols", "cells")

    def __init__(self, rows: int, cols: int | None = None):
        self.rows = rows
        self.cols = cols if cols is not None else rows
        self.cells = [[False] * self.cols for _ in range(self.rows)]

    @property
    def n(self):                      # convenience for square grids
        return self.rows

    def clone(self) -> "Grid":
        g = Grid(self.rows, self.cols)
        g.cells = [row[:] for row in self.cells]
        return g

    # -- validity ---------------------------------------------------------
    def runs(self):
        """Yield (direction, r, c, length) for every maximal white run."""
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                if self.cells[r][c]:
                    c += 1
                    continue
                start = c
                while c < self.cols and not self.cells[r][c]:
                    c += 1
                yield ("A", r, start, c - start)
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                if self.cells[r][c]:
                    r += 1
                    continue
                start = r
                while r < self.rows and not self.cells[r][c]:
                    r += 1
                yield ("D", start, c, r - start)

    def is_valid(self, max_run: int = 8) -> bool:
        # 1. every run is 0-length or >= 3, and short enough to fill
        for _d, _r, _c, ln in self.runs():
            if ln < 3 or ln > max_run:
                return False

        # 2. every white cell belongs to both an across and a down entry
        #    (guaranteed by rule 1) and 3. everything is connected
        start = None
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.cells[r][c]:
                    start = (r, c)
                    break
            if start:
                break
        if start is None:
            return False

        seen = {start}
        stack = [start]
        white_total = sum(1 for r in range(self.rows) for c in range(self.cols)
                          if not self.cells[r][c])
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.cells[nr][nc]:
                    if (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
        return len(seen) == white_total

    # -- slots ------------------------------------------------------------
    def all_slots(self):
        """Every maximal white run as (direction, cells) where cells is a
        list of (r, c) in reading order."""
        out = []
        for d, r, c, ln in self.runs():
            if ln < 3:
                continue
            if d == "A":
                cells = [(r, c + i) for i in range(ln)]
            else:
                cells = [(r + i, c) for i in range(ln)]
            out.append((d, cells))
        return out


# --------------------------------------------------------------------------
# 1. Template generation
# --------------------------------------------------------------------------
def min_run_ok(grid: Grid) -> bool:
    """No white run of length 1 or 2 anywhere (the unbreakable rule)."""
    for _d, _r, _c, ln in grid.runs():
        if ln < 3:
            return False
    return True


def _mirror_pair(n, r, c):
    rr, cc = n - 1 - r, n - 1 - c
    return [(r, c)] if (r, c) == (rr, cc) else [(r, c), (rr, cc)]


def _place(grid: Grid, cells, value: bool):
    for x, y in cells:
        grid.cells[x][y] = value


def _longest_run(grid: Grid):
    runs = [r for r in grid.runs()]
    if not runs:
        return None
    return max(runs, key=lambda t: t[3])


def _count_blacks(grid: Grid) -> int:
    return sum(1 for row in grid.cells for x in row if x)


def energy(grid: Grid, max_run: int, target_blacks: int) -> float:
    """Lower is better. Punishes unfillable runs, over-long runs,
    a wrong black-square count, and disconnected white areas."""
    e = 0.0
    for _d, _r, _c, ln in grid.runs():
        if ln < 3:
            e += 90.0                      # a 1- or 2-cell entry: unacceptable
        elif ln > max_run:
            e += (ln - max_run) * 10.0     # too long to fill from the pool

    e += abs(_count_blacks(grid) - target_blacks) * 2.0

    n = grid.rows
    white = [(r, c) for r in range(n) for c in range(n) if not grid.cells[r][c]]
    if white:
        seen = {white[0]}
        stack = [white[0]]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and not grid.cells[nr][nc] \
                        and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        e += (len(white) - len(seen)) * 10.0   # orphaned cells
    return e


def gen_template(n: int, target_blacks: int, rng: random.Random,
                 max_run: int = 8, iters: int = 6000,
                 restarts: int = 12) -> Grid | None:
    """Simulated-annealing search for a symmetric, fillable black pattern.

    Only mirrored pairs are ever toggled, so 180-degree symmetry is exact by
    construction. Every accepted candidate is re-checked with Grid.is_valid.
    """
    density = target_blacks / (n * n)

    for _restart in range(restarts):
        grid = Grid(n)
        # symmetric random start
        for r in range(n):
            for c in range(n):
                rr, cc = n - 1 - r, n - 1 - c
                if (rr, cc) < (r, c):
                    continue                       # decided by its partner
                black = rng.random() < density
                if black:
                    for x, y in _mirror_pair(n, r, c):
                        grid.cells[x][y] = True

        cur = energy(grid, max_run, target_blacks)
        best = cur
        best_cells = [row[:] for row in grid.cells]

        t0, t1 = 9.0, 0.05
        for step in range(iters):
            t = t0 * (t1 / t0) ** (step / max(1, iters - 1))
            r = rng.randrange(n)
            c = rng.randrange(n)
            pair = _mirror_pair(n, r, c)
            before = [(x, y, grid.cells[x][y]) for x, y in pair]
            for x, y in pair:
                grid.cells[x][y] = not grid.cells[x][y]
            new = energy(grid, max_run, target_blacks)
            if new <= cur or rng.random() < pow(2.718281828, -(new - cur) / t):
                cur = new
                if new < best:
                    best = new
                    best_cells = [row[:] for row in grid.cells]
            else:
                for x, y, v in before:
                    grid.cells[x][y] = v

        cand = Grid(n)
        cand.cells = best_cells
        if cand.is_valid(max_run=max_run) and \
                abs(_count_blacks(cand) - target_blacks) <= max(3, target_blacks * 0.2):
            return cand
    return None


def slots_signature(grid: Grid):
    return tuple(sorted((d, len(cells)) for d, cells in grid.all_slots()))


# --------------------------------------------------------------------------
# 2. The filler
# --------------------------------------------------------------------------
@dataclass
class Pool:
    """Word pool indexed for fast pattern lookups."""
    words: list[str] = field(default_factory=list)
    clues: dict[str, str] = field(default_factory=dict)
    theme: set[str] = field(default_factory=set)

    def index(self):
        n = len(self.words)
        self.by_pos_letter: dict[tuple[int, int, str], int] = {}
        self.by_len: dict[int, int] = {}
        masks = [0] * n
        for i, w in enumerate(self.words):
            L = len(w)
            for j, ch in enumerate(w):
                self.by_pos_letter.setdefault((L, j, ch), 0)
                masks[i] |= 1 << (L * 26 + j * 26 + (ord(ch) - 65))
            self.by_len[L] = self.by_len.get(L, 0) + 1
        self.masks = masks
        self.all_by_len: dict[int, int] = {}
        for i, w in enumerate(self.words):
            self.all_by_len[len(w)] = self.all_by_len.get(len(w), 0) | (1 << i)
        return self


def _word_mask(word: str) -> int:
    m = 0
    for j, ch in enumerate(word):
        m |= 1 << (len(word) * 26 + j * 26 + (ord(ch) - 65))
    return m


def fill(grid: Grid, pool: Pool, rng: random.Random,
         node_limit: int = 400_000, restarts: int = 1):
    """Return (letters, slots) or None.

    letters is a dict (r, c) -> char for white cells; slots is a list of
    dicts with direction / number / cells / answer.
    """
    slots = grid.all_slots()
    slot_cells = [cells for _d, cells in slots]
    slot_len = [len(c) for c in slot_cells]
    crossing: list[list[int]] = [[] for _ in slots]

    # map each white cell -> the slots that cover it
    cell_slots: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for si, cells in enumerate(slot_cells):
        for pos, rc in enumerate(cells):
            cell_slots.setdefault(rc, []).append((si, pos))
    for rc, owners in cell_slots.items():
        for si, _pos in owners:
            for sj, _pos2 in owners:
                if si != sj:
                    crossing[si].append(sj)
    crossing = [sorted(set(x)) for x in crossing]

    # candidate mask per slot
    words = pool.words
    full = pool.all_by_len

    def cand_mask(letters):
        out = []
        for si in range(len(slots)):
            m = full.get(slot_len[si], 0)
            if m == 0:
                return None
            for pos, (r, c) in enumerate(slot_cells[si]):
                ch = letters.get((r, c))
                if ch:
                    km = pool_by_pos.get((slot_len[si], pos, ch), 0)
                    m &= km
                    if m == 0:
                        return None
            out.append(m)
        return out

    # (len, pos, letter) -> bitmask of words
    pool_by_pos: dict[tuple[int, int, str], int] = {}
    for i, w in enumerate(words):
        L = len(w)
        for j, ch in enumerate(w):
            k = (L, j, ch)
            pool_by_pos[k] = pool_by_pos.get(k, 0) | (1 << i)

    best = None
    best_score = -1
    nodes = 0

    def order_candidates(mask, si):
        idxs = _bits(mask)
        rng.shuffle(idxs)
        # prefer theme words
        idxs.sort(key=lambda i: 0 if words[i] in pool.theme else 1)
        return idxs

    def recurse(letters, masks, filled_count, theme_count):
        nonlocal nodes, best, best_score
        nodes += 1
        if nodes > node_limit:
            return False
        if filled_count == len(slots):
            score = theme_count * 1000 - len(slots)
            if score > best_score:
                best_score = score
                best = (dict(letters), [words[i] for i in _chosen])
            return True

        # MRV: unfilled slot with fewest candidates
        best_si = -1
        best_n = 1 << 30
        for si in range(len(slots)):
            if _chosen[si] is not None:
                continue
            m = masks[si]
            cnt = m.bit_count()
            if cnt < best_n:
                best_n = cnt
                best_si = si
                if cnt <= 1:
                    break
        if best_n == 0:
            return False

        si = best_si
        for wi in order_candidates(masks[si], si):
            w = words[wi]
            new_letters = dict(letters)
            ok = True
            for pos, (r, c) in enumerate(slot_cells[si]):
                new_letters[(r, c)] = w[pos]
            new_masks = list(masks)
            new_masks[si] = 1 << wi
            # forward check
            for sj in range(len(slots)):
                if _chosen[sj] is not None or sj == si:
                    continue
                m = new_masks[sj]
                for pos, (r, c) in enumerate(slot_cells[sj]):
                    ch = new_letters.get((r, c))
                    if ch:
                        m &= pool_by_pos.get((slot_len[sj], pos, ch), 0)
                        if m == 0:
                            ok = False
                            break
                if not ok:
                    break
                new_masks[sj] = m
            if not ok:
                continue

            _chosen[si] = wi
            cnt = recurse(new_letters, new_masks, filled_count + 1,
                          theme_count + (1 if w in pool.theme else 0))
            _chosen[si] = None
            if cnt:
                return True
        return False

    for _ in range(restarts):
        nodes = 0
        _chosen = [None] * len(slots)
        masks = cand_mask({})
        if masks is None:
            continue
        masks = list(masks)
        recurse({}, masks, 0, 0)
        if best is not None:
            break
    if best is None:
        return None

    letters, answers = best
    numbered = number_slots(grid, slots)
    out = []
    for (d, cells), ans in zip(slots, answers):
        out.append({
            "dir": d,
            "num": next(n for (dd, cc, nn) in numbered if cc == cells and dd == d),
            "cells": cells,
            "answer": ans,
            "theme": ans in pool.theme,
        })
    return letters, out


def _bits(mask):
    out = []
    while mask:
        low = mask & -mask
        out.append(low.bit_length() - 1)
        mask ^= low
    return out


# --------------------------------------------------------------------------
# Numbering (standard crossword numbering)
# --------------------------------------------------------------------------
def number_slots(grid: Grid, slots):
    """Return list of (direction, cells, number)."""
    starts = {}
    num = 0
    for r in range(grid.rows):
        for c in range(grid.cols):
            if grid.cells[r][c]:
                continue
            opens_across = (c == 0 or grid.cells[r][c - 1]) and (
                c + 1 < grid.cols and not grid.cells[r][c + 1]
            )
            opens_down = (r == 0 or grid.cells[r - 1][c]) and (
                r + 1 < grid.rows and not grid.cells[r + 1][c]
            )
            if opens_across or opens_down:
                num += 1
                starts[(r, c)] = num
    out = []
    for d, cells in slots:
        out.append((d, cells, starts[cells[0]]))
    return out


def render_ascii(grid: Grid, letters) -> str:
    lines = []
    for r in range(grid.rows):
        row = []
        for c in range(grid.cols):
            if grid.cells[r][c]:
                row.append("###")
            else:
                ch = letters.get((r, c), "?")
                row.append(f" {ch} ")
        lines.append("".join(row))
    return "\n".join(lines)
