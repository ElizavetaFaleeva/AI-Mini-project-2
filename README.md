# Game Theory Advisor

Game Theory Advisor is a console program that helps with everyday communication decisions: dividing chores,
resolving a conflict, choosing where to go together, negotiating a deal. You describe a situation in a few
sentences (English, Latin letters only) and ask for advice. The program recognises which classic game-theory model
the situation resembles, builds a payoff matrix, finds the equilibrium, and prints a short, practical piece of
advice. It works fully offline, uses only the Python standard library, and needs no extra data.

## Requirements

- Python 3.8 or newer
- No extra packages, no internet connection, no data files

## How to run

Run these commands from the project folder (the one containing `game_advisor.py`):

```bash
python3 game_advisor.py                                   # interactive mode
python3 game_advisor.py --text "we argue who should wash the dishes"   # description from the command line
python3 game_advisor.py --text "we argue who should wash the dishes" --defaults   # skip follow-up questions
python3 game_advisor.py --selftest                        # run the built-in checks
python3 game_advisor.py --help                            # show all options
```

| Option | Meaning |
|--------|---------|
| *(none)* | Interactive mode: asks for the description, then two follow-up questions, then prints the advice. Afterwards asks "Another situation? (y/n)". |
| `--text "..."` | Use this description instead of asking for it. |
| `--defaults` | Skip the follow-up questions (assumes: not repeated, care = 3). |
| `--selftest` | Run the assert checks, print `All self-tests passed`, exit with code 0. |

### Interactive example

```text
$ python3 game_advisor.py
Describe your situation: my roommate and I argue about who does the dishes
Will you deal with this person again many times? (y/n): y
How much do you care about the relationship, 1 (not at all) to 5 (very much)? [1-5]: 4
```

The program then prints the detected situation, the payoff matrix, the analysis and the advice.
If no keyword is recognised, it shows a numbered menu of the five models and asks you to pick one.

## Input rules (validation)

- The description must be English text: any letter that is not Latin (for example Cyrillic) is rejected.
- At least 3 words and at most 1000 characters; empty or symbol-only input is rejected.
  In interactive mode you get 3 attempts, then the program exits with code 1.
- Follow-up answers: `y/yes/n/no` for the yes/no question, a whole number from 1 to 5 for the relationship question.
  Invalid answers are asked again.
- Ctrl+C or Ctrl+D (end of input) exits politely, without a traceback.

## Example output

Command: `python3 game_advisor.py --text "we argue every day who should wash the dishes" --defaults`

```text
Detected situation: Prisoner's Dilemma (matched: dishes)

+----------------+------------------+---------------+
|                | Other: Cooperate | Other: Defect |
+----------------+------------------+---------------+
| You: Cooperate | (3, 3)           | (0, 5)        |
+----------------+------------------+---------------+
| You: Defect    | (5, 0)           | (1, 1)        |
+----------------+------------------+---------------+
(payoffs: you, other person - higher is better)

Analysis
  - Dominant strategy for you: Defect
  - Dominant strategy for the other person: Defect
  - Pure Nash equilibria: (Defect / Defect)
  - The equilibrium (Defect / Defect) is NOT Pareto efficient: both could be better off elsewhere.

Advice
  - Slacking looks better for each of you alone, and that is exactly how both
    of you end up worse off.
  - Make cooperation the easy default: agree on a clear split (a rota, a
    schedule) so nobody has to guess what the other will do.
  - Do your part first; it is cheap and shows you are willing to cooperate.
  - This looks like a one-off, so reputation matters less - but staying fair
    costs little.

What you could say:
  "Let's set a simple rota for this so neither of us has to keep score. I'll
  take the first turn."

Note: this is a simplified model, not a substitute for talking to the person.
```

Self-test:

```text
$ python3 game_advisor.py --selftest
All self-tests passed
```

## How it works

1. **Classification.** The text is lowercased and compared with keyword lists (substring match). The game with the
   most matches wins; ties go to the game listed first. Models: Prisoner's Dilemma (chores, costs), Chicken
   (arguments, standoffs), Stag Hunt (teamwork, trust), Battle of the Sexes (choosing together), and Ultimatum /
   negotiation (offers, prices, salary).
2. **Payoff matrix.** Each 2x2 game has a fixed matrix of (you, other) payoffs. Your answers adjust it: if you will
   meet the person again, and the more you care about the relationship, the more the mutual cooperative outcome is worth.
3. **Analysis.** The program finds dominant strategies, pure Nash equilibria, a mixed equilibrium (when one exists)
   and checks whether the outcome is Pareto efficient.
4. **Advice.** Three to five bullet points plus an example sentence you can say to the other person. The Ultimatum
   case has no matrix: it uses backward induction and suggests proposing roughly 40-50% depending on your answers.

## Limitations

- These are simplified textbook models; real situations are more complicated.
- Recognition is keyword-based, so unusual wording may fall back to the manual menu.
- English only (Latin letters).
- The advice is a thinking aid, not a substitute for talking to the person.

## Project files

| File | Purpose |
|------|---------|
| `game_advisor.py` | The program (single file, standard library only). |
| `PROJECT.md` | The specification the program was built from. |
| `ai-workflow/` | Agent definitions and debugging notes from the AI-assisted workflow. |

## How this project was built (AI usage)

- **Specification and agents:** an OpenCode agent team was created for the project: `code-writer`, `runner`
  (runs tests and sample commands) and `game-reviewer` (read-only review of the game theory); the course agents
  `debugger` and `doc-writer` were used as provided. Their definitions are in `ai-workflow/agents/`.
- **Code:** OpenCode's code-writing call kept timing out on a 400-line file, so the first full draft of
  `game_advisor.py` was generated by an AI assistant (Claude) outside OpenCode from `PROJECT.md`. It was then run and
  tested, reviewed by `game-reviewer` and edited by `code-writer`.
- **Debugging:** `debugger` found and fixed a keyword issue in round 1. That fix turned out to be too narrow, because it
  broke the `negotiat` stem; this was found and fixed in round 2 with an AI assistant (Claude), together with two
  other issues. See `ai-workflow/debug_round_1.md` and `ai-workflow/debug_round_2.md`.
- **Latin-only input** and **this README** were written with the AI assistant (Claude) because the OpenCode model budget
  was exhausted; the README examples are real program output and every command above was run before publishing.
- Every AI-generated change was run and tested by the author before being committed.
