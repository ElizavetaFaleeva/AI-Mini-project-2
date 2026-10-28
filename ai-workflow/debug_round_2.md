# Debug round 2

Found while testing edge cases after debug round 1 (tested with `python3 game_advisor.py --text ... --defaults`).

| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | `--text "we are negotiating the price"` lost the keyword `negotiat` | Round 1 "fixed" the stem `negotiat` into the full word `negotiate`, which no longer matches `negotiating` / `negotiation` (the stem was intentional, a substring match) | Restored the stem `negotiat`; added a selftest assert |
| 2 | `we argue about everything` was not recognised as Chicken | Only `argument` was a keyword after the game theory review changed `argu` to `argument` | Added `argue` and `arguing` to the Chicken keywords; added a selftest assert |
| 3 | Cyrillic input was accepted | The program had Russian keywords and no script check | `validate_description` now rejects non-Latin letters; Cyrillic keywords and `да/нет` removed |
| 4 | Latin-only check said only "use Latin letters" and a pasted description (and then the menu answer `3`) was rejected | The message did not name the offending character, and pasted text can carry invisible or terminal control characters | The error now lists the offending characters with Unicode code points; input is cleaned of control/invisible characters before validation; everyday words (walk, invite, dinner, party...) added to Battle of the Sexes |

Prevention note: keyword matching is a substring match, so a stem such as `negotiat` is deliberate; always
add an assert for each keyword form you rely on.

Checked and OK: empty text, `hi`, only symbols, 1001 characters, Ctrl+D / Ctrl+C at every prompt, invalid y/n and out-of-range numbers.
