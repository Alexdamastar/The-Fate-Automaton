# The Fate Automaton

We are the sum of every choice we've made, and every choice made for us. Just a reminder that your life is more fragile than you realize, presented through automata theory.

This project generates a single interactive HTML page that:
- visualizes each scenario as an NFA,
- builds the equivalent DFA via subset construction,
- lets you switch between scenarios and machine views,
- supports click-to-open state detail panels.

## Project Structure

- [Life_NFA_DFA.py](Life_NFA_DFA.py): entrypoint/orchestrator that builds the final HTML.
- [automaton/core.py](automaton/core.py): automaton logic (`epsilon_closure`, `move`, `nfa_to_dfa`, DFA state detail helper).
- [scenarios/data.py](scenarios/data.py): scenario definitions and default scenario key.
- [payload/builder.py](payload/builder.py): transforms scenario + DFA data into browser payload.
- [templates/app.html](templates/app.html): UI markup shell.
- [templates/styles.css](templates/styles.css): visual style.
- [templates/app.js](templates/app.js): graph rendering and UI behavior.
- [templates/renderer.py](templates/renderer.py): composes template files and injects payload.
- [fate_automaton.html](fate_automaton.html): generated artifact (not committed by default).

## Requirements

- Python 3.10+ (3.11 recommended)
- Internet connection on first load for CDN assets (vis.js and Google Fonts)

## Run

From the project root:

```powershell
python Life_NFA_DFA.py
```

This will:
1. build payload data from scenarios,
2. render the final HTML,
3. write [fate_automaton.html](fate_automaton.html),
4. open it in your default browser.

## Add or Edit a Scenario

Update [scenarios/data.py](scenarios/data.py) and add a new scenario object under `SCENARIOS` with:
- `title`
- `description`
- `nfa.states`
- `nfa.start`
- `nfa.accepting`
- `nfa.state_details`
- `nfa.transitions` (tuples: `(from_state, symbol, to_state)`)

The DFA and state detail expansion are generated automatically.

## Git Notes

- Cache files and build caches are ignored via [.gitignore](.gitignore).
- [fate_automaton.html](fate_automaton.html) is ignored because it is generated output.
- If you prefer to commit the generated HTML for demos, remove `fate_automaton.html` from [.gitignore](.gitignore).

## Troubleshooting

- If the browser page looks stale, rerun `python Life_NFA_DFA.py`.
- If labels or graphs look crowded, adjust rendering options in [templates/app.js](templates/app.js).
- If state descriptions are missing, verify `state_details` keys match state names exactly in [scenarios/data.py](scenarios/data.py).
