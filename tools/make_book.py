"""Build THE EX-FILES: generate the puzzles, then render the KDP interior PDF."""
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from bank import FILL, THEMED                      # noqa: E402
from crossword import number_slots                 # noqa: E402
from weave import Bank, weave, to_grid, number_entries  # noqa: E402
from reportlab.pdfgen import canvas                # noqa: E402
import render                                      # noqa: E402
import extras                                      # noqa: E402

TITLES = [
    ("It's Not You, It's the Puzzle", "things you said at 2 a.m."),
    ("The Five Stages, in Ink", "bargaining, mostly"),
    ("Two A.M. Typing Lessons", "drafts you never sent"),
    ("The Group Chat Is Typing...", "the official position"),
    ("She Took the Dog", "custody, disputed"),
    ("Certified Absolutely Fine", "per your own statement"),
    ("The Rebound Rules", "a policy document"),
    ("Blocked, Unblocked, Blocked", "a timeline"),
    ("Sunday Scaries, Extra Large", "weekends, unstructured"),
    ("The Playlist You Must Delete", "songs, weaponised"),
    ("Closure (Not Included)", "what you cannot buy"),
    ("Moving Out, Sort Of", "boxes, half packed"),
    ("One (1) Unsent Text", "drafts, revisited"),
    ("Her Mom Still Likes You", "a trap, obviously"),
    ("The Dog Is Fine, By the Way", "final statement"),
]

SIZES = [15, 14, 16, 13, 15, 14, 16, 13, 15, 16, 14, 15, 15, 14, 16]


def build_bank():
    clues = {}
    for w, c in FILL.items():
        if w not in THEMED:
            clues[w] = c
    for w, c in THEMED.items():
        clues[w] = c
    return Bank(clues, set(THEMED))


MIN_WORDS = 26
MIN_DIM = 12


def make_puzzle(bank, index, size, seed, discourage, target=70, quota=16):
    rng = random.Random(seed)
    result = weave(bank, size, rng, target_words=target, theme_quota=quota,
                   discourage=discourage)
    if result is None:
        return None
    letters, placed, checked = result
    grid, shift = to_grid(letters)
    entries = number_entries(grid, placed, shift, bank.clues, bank.theme)

    numbered = number_slots(grid, grid.all_slots())
    num_map = {}
    for d, cells, num in numbered:
        num_map[f"{cells[0][0]},{cells[0][1]}"] = num

    rows = [["#" if grid.cells[r][c] else "." for c in range(grid.cols)]
            for r in range(grid.rows)]
    shifted_letters = {(r - shift[0], c - shift[1]): ch
                       for (r, c), ch in letters.items()}

    if len(placed) < MIN_WORDS or grid.rows < MIN_DIM or grid.cols < MIN_DIM:
        return None
    if len(entries) != len(placed):
        return None

    title, hint = TITLES[index - 1]
    return {
        "index": index,
        "title": title,
        "theme_hint": hint,
        "size": size,
        "grid": ["".join(r) for r in rows],
        "numbers": num_map,
        "entries": entries,
        "letters": shifted_letters,
        "answer": {f"{r},{c}": ch for (r, c), ch in shifted_letters.items()},
        "stats": {
            "words": len(placed),
            "theme_words": sum(1 for p in placed if p.word in bank.theme),
            "checked_pct": round(100 * checked, 1),
            "rows": grid.rows,
            "cols": grid.cols,
        },
    }


def verify(puzzles):
    """Re-check every entry against the printed grid and the answer key."""
    problems = []
    for pz in puzzles:
        grid = pz["grid"]
        letters = pz["letters"]
        seen = set()
        for e in pz["entries"]:
            cells = [tuple(x) for x in e["cells"]]
            spelled = "".join(letters[rc] for rc in cells)
            if spelled != e["answer"]:
                problems.append(f"p{pz['index']} {e['dir']}{e['num']} "
                                f"{e['answer']} != {spelled}")
            if e["answer"] in seen:
                problems.append(f"p{pz['index']} duplicate answer {e['answer']}")
            seen.add(e["answer"])
        for (r, c), ch in letters.items():
            if grid[r][c] == "#":
                problems.append(f"p{pz['index']} letter in black square {r},{c}")
        for r, row in enumerate(grid):
            if len(row) != len(grid[0]):
                problems.append(f"p{pz['index']} ragged row {r}")
    return problems


def main():
    t0 = time.time()
    bank = build_bank()
    print(f"bank: {len(bank.answers)} answers "
          f"({len(bank.theme)} themed)")

    puzzles = []
    discourage = set()
    seed = 1000
    while len(puzzles) < len(TITLES) and seed < 1000 + 400:
        idx = len(puzzles) + 1
        size = SIZES[idx - 1]
        pz = None
        for _try in range(12):
            pz = make_puzzle(bank, idx, size, seed, discourage)
            seed += 1
            if pz is not None:
                break
        if pz is None:
            continue
        # store entry cells as plain lists for the PDF renderer
        for e in pz["entries"]:
            e["cells"] = [list(x) for x in e["cells"]]
        puzzles.append(pz)
        discourage.update(e["answer"] for e in pz["entries"])
        print(f"  puzzle {idx:2d}  {pz['stats']['rows']}x{pz['stats']['cols']}  "
              f"{pz['stats']['words']:2d} words  "
              f"{pz['stats']['theme_words']:2d} themed  "
              f"{pz['stats']['checked_pct']:.0f}% checked  "
              f"{time.time() - t0:5.1f}s")

    if len(puzzles) < len(TITLES):
        print(f"!! only built {len(puzzles)} puzzles")
        return 1

    out_pdf = os.path.join(ROOT, "The_Ex_Files_Crossword_Book_8.5x11_KDP.pdf")
    meta = {"puzzle_count": len(puzzles)}

    render.register_fonts()
    c = canvas.Canvas(out_pdf, pagesize=(render.PAGE_W, render.PAGE_H),
                      initialFontName="Body")
    c.setTitle("The Ex-Files: A Crossword Book for Men Who Are Absolutely Fine")
    c.setAuthor("The Ex-Files")
    c.setSubject("Adult humour crossword puzzle book (8.5 x 11 in)")

    render.title_page(c, meta)
    render.copyright_page(c, meta)
    extras.numbered_list(
        c, "house rules", "Ground Rules of the Breakup",
        [
            "Nobody in the group chat needs to hear about her sister's wedding. Ever. Again.",
            "You are allowed exactly one (1) unsent text per month. Draft it, read it, delete it, sleep.",
            "The dog was always going to go with her. You knew that. You bought the dog food. You knew.",
            "Do not ask her new man's friends what he does for a living. He is an accountant. Let it go.",
            "If you say 'I'm fine' with your whole chest at brunch, someone will hand you a drink and change the subject. That is a friend.",
            "Watching her stories at 2 a.m. counts as contact. You know this. Stop it.",
            "The gym membership is a tattoo now. It costs the same and it hurts the same.",
            "You may keep one (1) song. Not the whole playlist. One.",
            "Never text her mom. Her mom likes you. That is the trap.",
            "Every rule on this page is negotiable after ten p.m. That is why it is printed here instead of saved on your phone.",
        ],
        sub=["Ten rules, written down for your own protection. Tear this page out if you",
             "must, but you will want it again by Thursday."])

    extras.glossary(
        c, "the group chat", "The Group Chat Glossary",
        ["Ten messages you will receive in the next thirty days, translated."],
        [
            ("ARE YOU UP", "Code for: I need to say something about her immediately, and it cannot wait until morning."),
            ("NO WAY", "Confirmation that the thing you just said is both true and completely insane."),
            ("TOTALLY FINE", "The official diagnosis. It is not a compliment."),
            ("WE'RE NOT DOING THAT", "A plan, vetoed for your own good. Accept it."),
            ("COME OUT", "Dinner, two hours, one beer, then home. Non-negotiable, lightly enforced."),
            ("SHE TEXTED?", "The emergency that gets everybody off the couch at midnight."),
            ("DRINK WATER", "The last message in the thread, always sent at 3:04 a.m., by the one who is awake."),
            ("I'M PICKING YOU UP", "No discussion, no options, arriving in nine minutes."),
            ("NEW GUY", "Two words that end a good evening abruptly."),
            ("I SAID WHAT", "Quote confirmation, sent with a screenshot you do not want to see."),
        ])

    for pz in puzzles:
        render.puzzle_page(c, pz, meta)

    extras.checklist(
        c, "the promises page", "Things You Swore You Would Do",
        ["Tick what you actually did. Be honest. Nobody is reading this but you and",
         "possibly your brother, who will absolutely tell everyone."],
        [
            "Run a marathon (started: a 4k, in October, in the rain)",
            "Learn to cook something that is not eggs",
            "Delete her number (you still know it by heart)",
            "Get the dog back (legally impossible, emotionally necessary)",
            "Take up a hobby (bought the equipment, never opened the box)",
            "Apologise to her brother (he was fine with it the whole time)",
            "Grow a beard (it came in patchy; it has been described as 'moss')",
            "Move to a new city (moved apartments, same block, same view of her parking spot)",
            "Be friends with her (you cannot, and that is allowed)",
            "Be genuinely happy for her (working on it, in the gym)",
            "Say one sentence about it without mentioning her name",
            "Sleep before one a.m. for four nights in a row",
        ])

    extras.scorecard(
        c, "self assessment", "The Scorecard",
        ["Fill this in after puzzle 15. Numbers do not lie, and yours are hilarious."],
        [
            ("Hours spent thinking about her", "Estimated. Add ten percent for shower time."),
            ("Texts sent to her", "Across any and all apps, including the one you deleted"),
            ("Unsent drafts written and deleted", "The real hero number of the whole breakup"),
            ("Times the playlist played end to end", "If over 40, see a professional"),
            ("Gym visits claimed / gym visits actual", "Be honest. Two numbers, both surprising."),
            ("Times you explained the breakup to a stranger", "Includes the barber, who did not ask"),
            ("Songs skipped because they got to you", "Count the ones by that band from college"),
            ("Group chat messages sent after midnight", "Roughly equal to the number of bad ideas"),
        ],
        "Final score: whatever you wrote, add 40 points for finishing the book.")

    extras.notes_page(
        c, "private page", "Things You Will Not Say Out Loud",
        ["Write them here instead. It is cheaper than a text and it has never once",
         "ended up on her phone at 2 a.m. That is the entire point of this page."],
        lines=24)

    extras.part_page(
        c, "part two", "The Answers, Admitted",
        ["Every answer, every grid, no judgement.", "",
         "Try not to arrive here before the first hour is up."])

    for i in range(0, len(puzzles), 3):
        render.answer_page(c, puzzles[i:i + 3], page_no=i // 3 + 1, meta=meta)

    render.back_page(c, meta)
    c.save()

    problems = verify(puzzles)
    if problems:
        print("VERIFY PROBLEMS:")
        for pr in problems[:20]:
            print("  -", pr)
        return 2
    print(f"verified {len(puzzles)} puzzles: every entry matches the grid")

    manifest = os.path.join(ROOT, "build", "puzzles.json")
    os.makedirs(os.path.dirname(manifest), exist_ok=True)
    safe = []
    for pz in puzzles:
        q = {k: v for k, v in pz.items() if k != "letters"}
        safe.append(q)
    with open(manifest, "w") as fh:
        json.dump({"puzzles": safe, "meta": meta}, fh, indent=1)

    if render.WARNINGS:
        print("LAYOUT WARNINGS:")
        for w in render.WARNINGS:
            print("  -", w)
    else:
        print("layout check: every clue column fits its page")

    print(f"\nwrote {out_pdf}")
    print(f"wrote {manifest}")
    print(f"total {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
