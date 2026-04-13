from collections import deque


def epsilon_closure(states, transitions):
    """Compute ε-closure of a set of states."""
    closure = set(states)
    queue = deque(states)
    while queue:
        s = queue.popleft()
        for (frm, sym, to) in transitions:
            if frm == s and sym == "ε" and to not in closure:
                closure.add(to)
                queue.append(to)
    return frozenset(closure)


def move(states, symbol, transitions):
    """Compute the set of states reachable from states on symbol."""
    result = set()
    for s in states:
        for (frm, sym, to) in transitions:
            if frm == s and sym == symbol:
                result.add(to)
    return result


def nfa_to_dfa(nfa_start, nfa_transitions, nfa_accepting):
    alphabet = sorted({sym for (_, sym, _) in nfa_transitions if sym != "ε"})

    start_closure = epsilon_closure([nfa_start], nfa_transitions)
    dfa_states = {}  # frozenset -> label string
    dfa_transitions = []
    seen_transitions = set()
    dfa_accepting = set()

    def label(fs):
        """Human-readable label for a DFA subset state."""
        parts = sorted(fs)
        if len(parts) == 1:
            return parts[0]
        return "{" + ", ".join(parts) + "}"

    queue = deque([start_closure])
    visited = {start_closure}
    dfa_states[start_closure] = label(start_closure)

    if start_closure & nfa_accepting:
        dfa_accepting.add(start_closure)

    while queue:
        current = queue.popleft()
        for sym in alphabet:
            reached = move(current, sym, nfa_transitions)
            if not reached:
                continue
            closure = epsilon_closure(reached, nfa_transitions)
            if closure not in dfa_states:
                dfa_states[closure] = label(closure)
            if closure not in visited:
                visited.add(closure)
                queue.append(closure)
            if closure & nfa_accepting:
                dfa_accepting.add(closure)
            transition = (dfa_states[current], sym, dfa_states[closure])
            if transition not in seen_transitions:
                seen_transitions.add(transition)
                dfa_transitions.append(transition)

    ordered = [dfa_states[start_closure]] + [
        v for k, v in dfa_states.items() if k != start_closure
    ]
    return (
        list(dict.fromkeys(ordered)),
        dfa_states[start_closure],
        {dfa_states[k] for k in dfa_accepting},
        dfa_transitions,
    )


def build_dfa_state_details(dfa_states, nfa_state_details):
    """Generate readable descriptions for DFA states from NFA state details."""
    details = {}

    for state in dfa_states:
        if state.startswith("{") and state.endswith("}"):
            parts = [p.strip() for p in state[1:-1].split(",") if p.strip()]
            part_descriptions = [
                f"{part}: {nfa_state_details.get(part, 'No description available.')}"
                for part in parts
            ]
            details[state] = (
                "Merged DFA subset state. The machine is tracking these NFA possibilities at once: "
                + " | ".join(part_descriptions)
            )
        else:
            details[state] = (
                "Single DFA state. "
                + nfa_state_details.get(state, "No description available.")
            )

    return details
