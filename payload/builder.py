from automaton.core import build_dfa_state_details, nfa_to_dfa


def build_payload(scenarios, default_scenario_key):
    scenarios_payload = {}

    for key, scenario in scenarios.items():
        nfa = scenario["nfa"]
        nfa_state_details = nfa.get("state_details", {})
        dfa_states, dfa_start, dfa_accepting, dfa_transitions = nfa_to_dfa(
            nfa["start"], nfa["transitions"], nfa["accepting"]
        )
        dfa_state_details = build_dfa_state_details(dfa_states, nfa_state_details)

        scenarios_payload[key] = {
            "title": scenario["title"],
            "description": scenario["description"],
            "nfa": {
                "states": nfa["states"],
                "start": nfa["start"],
                "accepting": sorted(nfa["accepting"]),
                "stateDetails": nfa_state_details,
                "transitions": [
                    {"from": f, "label": l, "to": t}
                    for f, l, t in nfa["transitions"]
                ],
            },
            "dfa": {
                "states": dfa_states,
                "start": dfa_start,
                "accepting": sorted(dfa_accepting),
                "stateDetails": dfa_state_details,
                "transitions": [
                    {"from": f, "label": l, "to": t}
                    for f, l, t in dfa_transitions
                ],
            },
        }

    return {
        "defaultScenario": default_scenario_key,
        "scenarios": scenarios_payload,
    }
