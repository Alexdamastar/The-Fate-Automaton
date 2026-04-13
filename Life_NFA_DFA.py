import webbrowser
import os
from automaton.core import nfa_to_dfa
from payload.builder import build_payload
from scenarios.data import DEFAULT_SCENARIO_KEY, SCENARIOS
from templates.renderer import build_html

# ─────────────────────────────────────────────
#  ENTRY POINT

def main():
    payload = build_payload(SCENARIOS, DEFAULT_SCENARIO_KEY)
    html = build_html(payload)

    out_path = os.path.join(os.path.dirname(__file__), "fate_automaton.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    scenario = SCENARIOS[DEFAULT_SCENARIO_KEY]
    nfa_data = scenario["nfa"]

    print("=" * 60)
    print("  FATE AUTOMATON - NFA / DFA Visualizer")
    print("=" * 60)
    print(f"\n  Scenarios available: {len(SCENARIOS)}")
    print(f"  Default scenario: {scenario['title']}")
    print(f"\n  NFA states  : {len(nfa_data['states'])}")
    print(f"  NFA transitions: {len(nfa_data['transitions'])}  (including epsilon-moves)")

    dfa_states, _, dfa_accepting, dfa_trans = nfa_to_dfa(
        nfa_data["start"], nfa_data["transitions"], nfa_data["accepting"]
    )
    print(f"\n  DFA states  : {len(dfa_states)}  (after subset construction)")
    print(f"  DFA transitions: {len(dfa_trans)}")
    print(f"  DFA accepting: {dfa_accepting}")
    print(f"\n  Output -> {out_path}")
    print("\n  Opening browser...\n")

    webbrowser.open(f"file://{os.path.abspath(out_path)}")

if __name__ == "__main__":
    main()

