"""game_advisor.py - Game Theory Advisor, a console helper for everyday decisions.

You describe a situation (English or Russian); the program recognises which
classic game-theory model it resembles, builds a payoff matrix, finds the
equilibrium and prints short, practical advice. Fully offline, standard
library only.

Usage:
    python3 game-advisor/game_advisor.py                 # interactive
    python3 game-advisor/game_advisor.py --text "..."    # description from argument
    python3 game-advisor/game_advisor.py --text "..." --defaults
    python3 game-advisor/game_advisor.py --selftest
"""
import argparse
import copy
import sys
import textwrap
from typing import Dict, List, Optional, Tuple

Matrix = List[List[Tuple[float, float]]]  # matrix[row][col] = (you, other)

# --------------------------------------------------------------------------
# Game library. Rows = your action, columns = the other person's action.
# "coop" is the cell (row, col) that is the mutual cooperative/compromise cell.
# --------------------------------------------------------------------------
GAMES: Dict[str, dict] = {
    "pd": {
        "name": "Prisoner's Dilemma",
        "actions": ["Cooperate", "Defect"],
        "matrix": [[(3, 3), (0, 5)], [(5, 0), (1, 1)]],
        "coop": (0, 0),
        "keywords": ["dishes", "chores", "cleaning", "share costs", "both could slack",
                     "group project effort", "who pays", "tidy up", "посуда", "посуду",
                     "уборка", "уборку", "делить", "делим", "общие расходы", "лень"],
        "advice": [
            "Slacking looks better for each of you alone, and that is exactly how "
            "both of you end up worse off.",
            "Make cooperation the easy default: agree on a clear split (a rota, a "
            "schedule) so nobody has to guess what the other will do.",
            "Do your part first; it is cheap and shows you are willing to cooperate.",
        ],
        "phrase": "Let's set a simple rota for this so neither of us has to keep "
                  "score. I'll take the first turn.",
    },
    "chicken": {
        "name": "Chicken (standoff)",
        "actions": ["Yield", "Stand firm"],
        "matrix": [[(3, 3), (2, 4)], [(4, 2), (0, 0)]],
        "coop": (0, 0),
        "keywords": ["argu", "quarrel", "who backs down", "stubborn", "refuse to apologize",
                     "standoff", "conflict", "ссора", "ссорим", "спор", "не уступает",
                     "упрям", "конфликт"],
        "advice": [
            "If both of you stand firm, you both lose the most; the stubborn side "
            "only 'wins' when the other gives in.",
            "Do not escalate to the point of no return. A small, early concession "
            "costs far less than a long standoff.",
            "Yield on the issue, not on respect: present it as your choice and ask "
            "for something small in return.",
        ],
        "phrase": "I don't want us to keep fighting about this. I'll give way on "
                  "this one - can we handle the next one differently?",
    },
    "stag": {
        "name": "Stag Hunt (trust and coordination)",
        "actions": ["Trust", "Play safe"],
        "matrix": [[(5, 5), (0, 3)], [(3, 0), (3, 3)]],
        "coop": (0, 0),
        "keywords": ["team", "together", "project", "rely", "depend", "trust",
                     "plan jointly", "команда", "команде", "вместе", "проект",
                     "довериться", "надеяться"],
        "advice": [
            "The best result needs both of you to commit; the safe option is "
            "guaranteed but smaller.",
            "Reduce uncertainty: ask the other person to confirm their part and "
            "agree on small checkpoints.",
            "If you cannot get a clear commitment, secure a safe fallback for "
            "your own part.",
        ],
        "phrase": "I'm in if you're in. Can we agree who does what and check in on Friday?",
    },
    "battle": {
        "name": "Battle of the Sexes (coordination with different preferences)",
        "actions": ["Option A", "Option B"],
        "matrix": [[(3, 2), (0, 0)], [(0, 0), (2, 3)]],
        "coop": None,
        "keywords": ["where to go", "movie", "restaurant", "weekend", "vacation",
                     "choose together", "куда пойти", "кино", "ресторан", "выходные",
                     "отпуск"],
        "advice": [
            "You both want to do something together; the worst outcome is not "
            "agreeing at all.",
            "Decide quickly instead of arguing: 'both A' and 'both B' are both "
            "stable, so the choice is about fairness.",
            "Alternate: your pick this time, theirs next time (or flip a coin).",
        ],
        "phrase": "Let's do your choice this time and mine next time - deal?",
    },
    "ultimatum": {
        "name": "Ultimatum / negotiation",
        "actions": [],
        "matrix": None,
        "coop": None,
        "keywords": ["take it or leave it", "offer", "salary", "price", "bill", "negotiate",
                     "split money", "предложение", "зарплата", "цена", "торг", "счёт", "счет"],
        "advice": [],
        "phrase": "",
    },
}
GAME_ORDER = ["pd", "chicken", "stag", "battle", "ultimatum"]
DISCLAIMER = ("Note: this is a simplified model, not a substitute for talking "
              "to the person.")


# --------------------------------------------------------------------------
# Pure logic (easy to test)
# --------------------------------------------------------------------------
def validate_description(text: str) -> Tuple[bool, str]:
    """Check a situation description; return (ok, message)."""
    if text is None or not text.strip():
        return False, "The description is empty. Please describe your situation."
    if len(text) > 1000:
        return False, "The description is too long (max 1000 characters)."
    if len(text.split()) < 3:
        return False, "Please write at least 3 words so I can understand the situation."
    if not any(ch.isalpha() for ch in text):
        return False, "The description should contain words, not only symbols."
    return True, ""


def classify(text: str) -> Tuple[Optional[str], List[str]]:
    """Return (game_key, matched_keywords); game_key is None if nothing matches."""
    low = text.lower()
    best_key, best_hits = None, []
    for key in GAME_ORDER:
        hits = [kw for kw in GAMES[key]["keywords"] if kw in low]
        if len(hits) > len(best_hits):  # strict '>' keeps the earlier game on ties
            best_key, best_hits = key, hits
    return best_key, best_hits


def find_pure_nash(m: Matrix) -> List[Tuple[int, int]]:
    """Return all cells where neither player gains by switching alone."""
    result = []
    for r in range(2):
        for c in range(2):
            row_ok = m[r][c][0] >= m[1 - r][c][0]
            col_ok = m[r][c][1] >= m[r][1 - c][1]
            if row_ok and col_ok:
                result.append((r, c))
    return result


def dominant_strategy(m: Matrix, player: int) -> Optional[int]:
    """Return the index of a strictly dominant action for player 0 (you) or 1 (other)."""
    for a in range(2):
        if player == 0:
            better = all(m[a][c][0] > m[1 - a][c][0] for c in range(2))
        else:
            better = all(m[r][a][1] > m[r][1 - a][1] for r in range(2))
        if better:
            return a
    return None


def pareto_efficient(m: Matrix) -> List[Tuple[int, int]]:
    """Return cells that no other cell beats for one player without hurting the other."""
    cells = [(r, c) for r in range(2) for c in range(2)]
    efficient = []
    for (r, c) in cells:
        a, b = m[r][c]
        dominated = any(
            m[r2][c2][0] >= a and m[r2][c2][1] >= b and
            (m[r2][c2][0] > a or m[r2][c2][1] > b)
            for (r2, c2) in cells if (r2, c2) != (r, c))
        if not dominated:
            efficient.append((r, c))
    return efficient


def mixed_nash_2x2(m: Matrix) -> Optional[Tuple[float, float]]:
    """Return (p, q): p = chance YOU play action 0, q = chance the OTHER plays action 0.

    Each side mixes so that the opponent is indifferent. None if undefined
    or if the probabilities are not strictly between 0 and 1.
    """
    u = [[m[r][c][0] for c in range(2)] for r in range(2)]
    v = [[m[r][c][1] for c in range(2)] for r in range(2)]
    den_q = (u[0][0] - u[1][0]) + (u[1][1] - u[0][1])
    den_p = (v[0][0] - v[0][1]) + (v[1][1] - v[1][0])
    if den_q == 0 or den_p == 0:
        return None
    q = (u[1][1] - u[0][1]) / den_q
    p = (v[1][1] - v[1][0]) / den_p
    if 0 < p < 1 and 0 < q < 1:
        return p, q
    return None


def adjust_matrix(key: str, repeated: bool, care: int) -> Matrix:
    """Copy the game's matrix and boost the mutual cooperative cell."""
    m = copy.deepcopy(GAMES[key]["matrix"])
    coop = GAMES[key]["coop"]
    if coop is not None:
        bonus = (1 if repeated else 0) + (care - 3) * 0.5
        r, c = coop
        m[r][c] = (m[r][c][0] + bonus, m[r][c][1] + bonus)
    return m


def ultimatum_share(repeated: bool, care: int) -> int:
    """Suggested percentage of the total to propose to the other side."""
    if repeated or care >= 4:
        return 50
    if care == 3:
        return 45
    return 40


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------
def run_selftest() -> int:
    """Run all assert checks and print a success line."""
    pd, ch = GAMES["pd"]["matrix"], GAMES["chicken"]["matrix"]
    sh, bs = GAMES["stag"]["matrix"], GAMES["battle"]["matrix"]
    assert find_pure_nash(pd) == [(1, 1)]
    assert dominant_strategy(pd, 0) == 1 and dominant_strategy(pd, 1) == 1
    assert (1, 1) not in pareto_efficient(pd)
    assert sorted(find_pure_nash(ch)) == [(0, 1), (1, 0)]
    assert sorted(find_pure_nash(sh)) == [(0, 0), (1, 1)]
    assert sorted(find_pure_nash(bs)) == [(0, 0), (1, 1)]
    p, q = mixed_nash_2x2(bs)
    assert abs(p - 0.6) < 1e-9 and abs(q - 0.4) < 1e-9
    assert mixed_nash_2x2(pd) is None
    assert classify("we argue who will wash the dishes")[0] in GAMES
    assert classify("blah blah")[0] is None
    assert classify("куда пойти на выходные, кино или ресторан")[0] == "battle"
    assert validate_description("")[0] is False
    assert validate_description("   ")[0] is False
    assert validate_description("hi")[0] is False
    assert validate_description("!!! ??? ...")[0] is False
    assert validate_description("x" * 1001)[0] is False
    assert validate_description("We argue about the dishes")[0] is True
    assert adjust_matrix("pd", True, 5)[0][0] == (5, 5)
    assert adjust_matrix("battle", True, 5) == GAMES["battle"]["matrix"]
    assert ultimatum_share(False, 1) == 40 and ultimatum_share(True, 1) == 50
    print("All self-tests passed")
    return 0


# --------------------------------------------------------------------------
# Input helpers (the input function is a parameter so they can be tested)
# --------------------------------------------------------------------------
def ask_yes_no(question: str, ask=input) -> bool:
    """Ask a y/n question (y/n/yes/no/да/нет) until the answer is valid."""
    while True:
        ans = ask(question + " (y/n): ").strip().lower()
        if ans in ("y", "yes", "да"):
            return True
        if ans in ("n", "no", "нет"):
            return False
        print("Please answer y or n.")


def ask_int(question: str, low: int, high: int, ask=input) -> int:
    """Ask for an integer between low and high (inclusive) until valid."""
    while True:
        ans = ask(f"{question} [{low}-{high}]: ").strip()
        if ans.lstrip("+-").isdigit() and low <= int(ans) <= high:
            return int(ans)
        print(f"Please enter a whole number from {low} to {high}.")


def choose_game_from_menu(ask=input) -> str:
    """Let the user pick a game when the text did not match any keywords."""
    print("I could not recognise the situation. Which one is closest?")
    for i, key in enumerate(GAME_ORDER, 1):
        print(f"  {i}. {GAMES[key]['name']}")
    return GAME_ORDER[ask_int("Your choice", 1, len(GAME_ORDER), ask) - 1]


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def fmt(x: float) -> str:
    """Format a payoff number without trailing zeros."""
    return f"{x:g}"


def draw_matrix(game: dict, m: Matrix) -> str:
    """Return the payoff matrix as an ASCII table."""
    acts = game["actions"]
    heads = [f"Other: {a}" for a in acts]
    rows = [[f"({fmt(m[r][c][0])}, {fmt(m[r][c][1])})" for c in range(2)] for r in range(2)]
    labels = [f"You: {a}" for a in acts]
    w0 = max(len(s) for s in labels)
    ws = [max(len(heads[c]), len(rows[0][c]), len(rows[1][c])) for c in range(2)]
    sep = "+" + "-" * (w0 + 2) + "".join("+" + "-" * (w + 2) for w in ws) + "+"
    lines = [sep, "| " + " " * w0 + " " + "".join(f"| {heads[c].ljust(ws[c])} " for c in range(2)) + "|", sep]
    for r in range(2):
        lines.append("| " + labels[r].ljust(w0) + " " +
                     "".join(f"| {rows[r][c].ljust(ws[c])} " for c in range(2)) + "|")
        lines.append(sep)
    return "\n".join(lines + ["(payoffs: you, other person - higher is better)"])


def bullets(items: List[str]) -> None:
    """Print a list of wrapped bullet points."""
    for it in items:
        print(textwrap.fill(it, width=78, initial_indent="  - ", subsequent_indent="    "))


def print_matrix_game(key: str, hits: List[str], repeated: bool, care: int) -> None:
    """Print detection, matrix, analysis and advice for a 2x2 game."""
    game = GAMES[key]
    m = adjust_matrix(key, repeated, care)
    acts = game["actions"]
    cell = lambda rc: f"({acts[rc[0]]} / {acts[rc[1]]})"
    print(f"\nDetected situation: {game['name']}" + (f" (matched: {', '.join(hits)})" if hits else ""))
    print("\n" + draw_matrix(game, m))
    print("\nAnalysis")
    for who, idx in (("you", 0), ("the other person", 1)):
        d = dominant_strategy(m, idx)
        print(f"  - Dominant strategy for {who}: " + (acts[d] if d is not None else "none"))
    nash = find_pure_nash(m)
    print("  - Pure Nash equilibria: " + (", ".join(cell(c) for c in nash) or "none"))
    mixed = mixed_nash_2x2(m)
    if mixed:
        p, q = mixed
        print(f"  - Mixed equilibrium: you play '{acts[0]}' {p:.0%} of the time, "
              f"the other person {q:.0%}")
    eff = pareto_efficient(m)
    bad = [c for c in nash if c not in eff]
    if bad:
        print("  - The equilibrium " + ", ".join(cell(c) for c in bad) +
              " is NOT Pareto efficient: both could be better off elsewhere.")
    elif nash:
        print("  - The equilibrium outcome is Pareto efficient (nobody can improve without hurting the other).")
    print("\nAdvice")
    extra = []
    if repeated:
        extra.append("You will meet again many times: start cooperative, mirror what the other "
                     "side does next (tit-for-tat) and forgive a single slip.")
    else:
        extra.append("This looks like a one-off, so reputation matters less - but staying fair costs little.")
    if care >= 4:
        extra.append("You value the relationship highly: favour fairness and be willing to give a bit more.")
    elif care <= 2:
        extra.append("The relationship matters less to you, so you can afford to be firmer about your interests.")
    bullets(game["advice"] + extra)
    print("\nWhat you could say:")
    print(textwrap.fill('"' + game["phrase"] + '"', width=78, initial_indent="  ", subsequent_indent="  "))


def print_ultimatum(hits: List[str], repeated: bool, care: int) -> None:
    """Print advice for the ultimatum / negotiation special case."""
    share = ultimatum_share(repeated, care)
    print(f"\nDetected situation: {GAMES['ultimatum']['name']}" +
          (f" (matched: {', '.join(hits)})" if hits else ""))
    print("\nAnalysis")
    bullets(["By backward induction, the person who receives a take-it-or-leave-it offer "
             "should accept any positive amount, so in theory you could offer almost nothing.",
             "In real life people reject offers that feel unfair (usually below ~30%), and "
             "then both sides get nothing."])
    print("\nAdvice")
    bullets([f"Propose about {share}% for the other side's benefit and keep the rest for yourself.",
             "Explain your reasoning so the offer feels fair, and leave room for a counter-offer.",
             "Know your alternative (what you do if there is no deal) before you start."])
    print("\nWhat you could say:")
    print(textwrap.fill('"Here is what I think is fair, and why. Does this work for you?"',
                        width=78, initial_indent="  ", subsequent_indent="  "))


def give_advice(text: str, use_defaults: bool, ask=input) -> None:
    """Classify the text, ask follow-ups (unless defaults) and print the advice."""
    key, hits = classify(text)
    if key is None:
        key = choose_game_from_menu(ask)
    repeated, care = False, 3
    if not use_defaults:
        repeated = ask_yes_no("Will you deal with this person again many times?", ask)
        care = ask_int("How much do you care about the relationship, 1 (not at all) to 5 (very much)?",
                       1, 5, ask)
    if key == "ultimatum":
        print_ultimatum(hits, repeated, care)
    else:
        print_matrix_game(key, hits, repeated, care)
    print("\n" + DISCLAIMER)


# --------------------------------------------------------------------------
# Command-line interface
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser."""
    p = argparse.ArgumentParser(description="Game Theory Advisor: advice for everyday "
                                            "decisions based on game theory (offline).")
    p.add_argument("--text", help="situation description (otherwise you will be asked)")
    p.add_argument("--defaults", action="store_true",
                   help="skip follow-up questions (repeated=no, care=3)")
    p.add_argument("--selftest", action="store_true", help="run built-in checks and exit")
    return p


def read_description(attempts: int = 3) -> Optional[str]:
    """Ask for a valid description (max attempts); return None if all fail."""
    for _ in range(attempts):
        text = input("Describe your situation: ")
        ok, msg = validate_description(text)
        if ok:
            return text
        print(msg)
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """Program entry point; returns the exit code."""
    args = build_parser().parse_args(argv)
    if args.selftest:
        return run_selftest()
    try:
        if args.text is not None:
            ok, msg = validate_description(args.text)
            if not ok:
                print(msg)
                return 1
            give_advice(args.text, args.defaults)
            return 0
        while True:
            text = read_description()
            if text is None:
                print("Too many invalid attempts. Goodbye.")
                return 1
            give_advice(text, args.defaults)
            if not ask_yes_no("\nAnother situation?"):
                return 0
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye! Good luck with the conversation.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
