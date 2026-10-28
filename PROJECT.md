# Game Theory Advisor - project description

## Task (README intro)
Game Theory Advisor is a console program that helps with everyday communication decisions: dividing chores, resolving a conflict, choosing where to go together, negotiating a deal. The user describes a situation in a few sentences in English (Latin letters only) and asks for advice. The program recognises which classic game-theory model the situation resembles, builds a payoff matrix, finds the equilibrium, and prints a short, practical piece of advice. It works fully offline, uses only the Python standard library, and needs no extra data.

## File
game-advisor/game_advisor.py  (run with: python3 game-advisor/game_advisor.py)

## Console interface
- No arguments: interactive mode. Prompt "Describe your situation: " via input(), then follow-up questions, then the advice. After the advice ask "Another situation? (y/n)".
- --text "..." : use this description instead of asking for it.
- --defaults : skip follow-up questions (repeated=no, care=3). Useful for tests.
- --selftest : run all assert checks, print "All self-tests passed" and exit with code 0.
- -h / --help via argparse.

## Input validation
- Description must be English text: any letter that is not Latin (for example Cyrillic) is rejected with the message "Please write the description in English using Latin letters only." followed by the offending characters (with their Unicode code points), because lookalike letters from a Russian keyboard layout are the usual cause
- Description must have at least 3 words and at most 1000 characters; empty or whitespace-only input is rejected with a friendly message and asked again (max 3 attempts in interactive mode, then exit with code 1).
- Follow-up answers: "Will you deal with this person again many times? (y/n)" accepts y/n/yes/no (case-insensitive). "How much do you care about the relationship, 1 (not at all) to 5 (very much)?" accepts only integers 1-5. Invalid answers are asked again.
- Typed or pasted text is cleaned first: terminal paste markers, control characters and invisible characters are removed.
- Ctrl+C / EOF must exit cleanly with a polite message, no traceback.

## Game library (2x2, payoffs are (you, other); rows = your action, columns = other's action)
1. Prisoner's Dilemma: actions Cooperate/Defect. CC=(3,3) CD=(0,5) DC=(5,0) DD=(1,1). Keywords: dishes, chores, cleaning, share costs, both could slack, group project effort, who pays, tidy up.
2. Chicken: actions Yield/Stand firm. YY=(3,3) YS=(2,4) SY=(4,2) SS=(0,0). Keywords: argument, argue, arguing, quarrel, who backs down, stubborn, refuse to apologize, standoff, conflict.
3. Stag Hunt: actions Trust/Play safe. TT=(5,5) TS=(0,3) ST=(3,0) SS=(3,3). Keywords: team, together, project, rely, depend, trust, plan jointly.
4. Battle of the Sexes: actions Option A/Option B. AA=(3,2) AB=(0,0) BA=(0,0) BB=(2,3). Keywords: where to go, movie, restaurant, weekend, vacation, choose together, walk, hang out, go out, invite, dinner, party.
5. Ultimatum / negotiation (special case, no matrix): Keywords: take it or leave it, offer, salary, price, bill, negotiat (stem: matches negotiate/negotiating/negotiation), split money.
6. If no game scores at least 1 keyword hit, show a numbered menu of the 5 games and let the user pick (validated).

## Classification
Lowercase the text, count keyword hits per game (substring match), pick the game with the most hits; ties -> first in the list above. Print the detected game and which keywords matched.

## Follow-up adjustments
- repeated = yes: add +1 to the payoff of the cooperative/compromise cell for both players and advise a tit-for-tat style (start cooperative, mirror the other side, forgive once).
- care (1-5): add (care - 3) * 0.5 to both players' payoff in the mutually cooperative/compromise cell (PD: CC; Chicken: YY; Stag Hunt: TT; Battle: the better-matched cell stays unchanged but advice mentions fairness/alternating choices).

## Analysis (pure functions, easy to test)
- find_pure_nash(matrix) -> list of (row, col) pairs.
- dominant_strategy(matrix, player) -> action index or None (strictly dominant).
- pareto_efficient(matrix) -> list of cells.
- mixed_nash_2x2(matrix) -> (p, q) probabilities, or None when a pure equilibrium is the only one or the formula is undefined (denominator 0).
- classify(text) -> (game_key or None, matched_keywords).
- validate_description(text) -> (ok, message).

## Output format (plain text, English)
1. "Detected situation: <game name> (matched: ...)"
2. The payoff matrix drawn with ASCII borders.
3. "Analysis": dominant strategies, Nash equilibria (pure, mixed if relevant), whether the equilibrium is Pareto efficient.
4. "Advice": 3 short bullet points + one example phrase the user can say to the other person.
5. A one-line disclaimer: this is a simplified model, not a substitute for talking to the person.

## Self-test (--selftest), at least these asserts
- Prisoner's Dilemma: unique pure Nash = (Defect, Defect); Defect is dominant for both; the Nash cell is NOT Pareto efficient.
- Chicken: exactly two pure Nash equilibria (Yield/Stand and Stand/Yield).
- Stag Hunt: two pure Nash equilibria (Trust/Trust and Safe/Safe).
- Battle of the Sexes: two pure Nash equilibria plus a mixed one with p = 0.6, q = 0.4 for the default matrix.
- classify("we argue who will wash the dishes") returns a known game; classify("blah blah") returns None.
- validate_description rejects "", "   ", "hi", accepts a normal sentence.

## Constraints
Python 3.8+, standard library only, no network, no files read or written (except nothing), single file, under ~450 lines, clear comments.
