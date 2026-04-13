import json
import webbrowser
import os
from collections import deque

# ──────────────────────────────────────────────
#  NFA DEFINITION  (Life Decisions → Death)
# ──────────────────────────────────────────────
#
#  States represent stages of your life.
#  Transitions are labelled with a "decision".
#  ε (epsilon) transitions are labelled "ε".
#  Accepting / "fatal" state = DEATH
#
#  The NFA is nondeterministic:
#    - Some decisions can lead to multiple states.
#    - ε-transitions happen silently (without choosing).

SCENARIOS = {
  "fateful-baseball": {
    "title": "The Baseball Detour",
    "description": "A harmless outing can spiral through bad influence and risk into fatal outcomes.",
    "nfa": {
      "states": [
        "Alive",
        "BaseballGame",
        "MeetStranger",
        "Infatuated",
        "BadInfluence",
        "HospitalVisit",
        "RecklessMoment",
        "CloseCall",
        "FinalChoice",
        "DEATH",
      ],
      "start": "Alive",
      "accepting": {"DEATH"},
      # (from_state, symbol, to_state)
      # symbol = decision label; "ε" = epsilon (free / silent move)
      "transitions": [
        ("Alive", "Go to baseball game", "BaseballGame"),
        ("Alive", "Stay home", "Alive"),
        ("BaseballGame", "Meet someone", "MeetStranger"),
        ("BaseballGame", "ε", "Alive"),
        ("MeetStranger", "Exchange numbers", "Infatuated"),
        ("MeetStranger", "Walk away", "Alive"),
        ("Infatuated", "ε", "BadInfluence"),
        ("Infatuated", "Keep distance", "Alive"),
        ("BadInfluence", "Follow their lead", "RecklessMoment"),
        ("BadInfluence", "Late night drive", "HospitalVisit"),
        ("BadInfluence", "Ignore warning signs", "RecklessMoment"),
        ("HospitalVisit", "ε", "CloseCall"),
        ("HospitalVisit", "Leave AMA", "RecklessMoment"),
        ("RecklessMoment", "Point of no return", "FinalChoice"),
        ("RecklessMoment", "Survive by luck", "CloseCall"),
        ("CloseCall", "Learn nothing", "BadInfluence"),
        ("CloseCall", "Change course", "Alive"),
        ("FinalChoice", "Accept the risk", "DEATH"),
        ("FinalChoice", "ε", "DEATH"),
      ],
    },
  },
  "after-party-drive": {
    "title": "The After-Party Drive",
    "description": "Trying to keep up can loop through risky behavior; some exits are safe, others fatal.",
    "nfa": {
      "states": [
        "Alive",
        "LateParty",
        "PeerPressure",
        "ImpairedDrive",
        "Checkpoint",
        "CrashRisk",
        "Recovery",
        "FinalChoice",
        "DEATH",
      ],
      "start": "Alive",
      "accepting": {"DEATH"},
      "transitions": [
        ("Alive", "Go out late", "LateParty"),
        ("Alive", "Stay home", "Alive"),
        ("LateParty", "Follow the crowd", "PeerPressure"),
        ("LateParty", "Leave early", "Alive"),
        ("PeerPressure", "ε", "ImpairedDrive"),
        ("PeerPressure", "Call a ride", "Recovery"),
        ("ImpairedDrive", "Speed", "CrashRisk"),
        ("ImpairedDrive", "Take back roads", "Checkpoint"),
        ("Checkpoint", "Panic", "CrashRisk"),
        ("Checkpoint", "Cooperate", "Recovery"),
        ("CrashRisk", "Lose control", "FinalChoice"),
        ("CrashRisk", "Near miss", "Recovery"),
        ("Recovery", "Learn and change", "Alive"),
        ("Recovery", "Repeat pattern", "PeerPressure"),
        ("FinalChoice", "Accept the risk", "DEATH"),
        ("FinalChoice", "ε", "DEATH"),
      ],
    },
  },
  "road-rage-spiral": {
    "title": "The Road-Rage Spiral",
    "description": "A small traffic conflict can escalate through pride and impulsive choices into irreversible outcomes.",
    "nfa": {
      "states": [
        "Alive",
        "TrafficDelay",
        "Provoked",
        "ChaseImpulse",
        "AggressiveManeuver",
        "NearMiss",
        "PoliceStop",
        "Recovery",
        "FinalChoice",
        "DEATH",
      ],
      "start": "Alive",
      "accepting": {"DEATH"},
      "transitions": [
        ("Alive", "Drive during rush hour", "TrafficDelay"),
        ("Alive", "Stay calm", "Alive"),
        ("TrafficDelay", "Get cut off", "Provoked"),
        ("TrafficDelay", "Let it go", "Alive"),
        ("Provoked", "Tailgate", "ChaseImpulse"),
        ("Provoked", "Breathe and reset", "Recovery"),
        ("Provoked", "ε", "ChaseImpulse"),
        ("ChaseImpulse", "Weave through lanes", "AggressiveManeuver"),
        ("ChaseImpulse", "Back off", "NearMiss"),
        ("AggressiveManeuver", "Run red light", "FinalChoice"),
        ("AggressiveManeuver", "Get pulled over", "PoliceStop"),
        ("NearMiss", "Learn from scare", "Recovery"),
        ("NearMiss", "Escalate again", "Provoked"),
        ("PoliceStop", "Cooperate", "Recovery"),
        ("PoliceStop", "Drive off in panic", "FinalChoice"),
        ("Recovery", "Change habits", "Alive"),
        ("Recovery", "Hold a grudge", "Provoked"),
        ("FinalChoice", "Accept the risk", "DEATH"),
        ("FinalChoice", "ε", "DEATH"),
      ],
    },
  },
}

DEFAULT_SCENARIO_KEY = "fateful-baseball"

# ──────────────────────────────────────────────
#  SUBSET CONSTRUCTION  (NFA → DFA)
# ──────────────────────────────────────────────

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
    """Compute the set of states reachable from `states` on `symbol`."""
    result = set()
    for s in states:
        for (frm, sym, to) in transitions:
            if frm == s and sym == symbol:
                result.add(to)
    return result

def nfa_to_dfa(nfa_start, nfa_transitions, nfa_accepting):
    alphabet = sorted({sym for (_, sym, _) in nfa_transitions if sym != "ε"})

    start_closure = epsilon_closure([nfa_start], nfa_transitions)
    dfa_states = {}          # frozenset → label string
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

    # Build unique state list preserving start first
    ordered = [dfa_states[start_closure]] + [
        v for k, v in dfa_states.items() if k != start_closure
    ]
    return (
        list(dict.fromkeys(ordered)),
        dfa_states[start_closure],
        {dfa_states[k] for k in dfa_accepting},
        dfa_transitions,
    )

# ──────────────────────────────────────────────
#  PACKAGE DATA FOR THE BROWSER
# ──────────────────────────────────────────────

def build_payload():
  scenarios_payload = {}

  for key, scenario in SCENARIOS.items():
    nfa = scenario["nfa"]
    dfa_states, dfa_start, dfa_accepting, dfa_transitions = nfa_to_dfa(
      nfa["start"], nfa["transitions"], nfa["accepting"]
    )

    scenarios_payload[key] = {
      "title": scenario["title"],
      "description": scenario["description"],
      "nfa": {
        "states": nfa["states"],
        "start": nfa["start"],
        "accepting": sorted(nfa["accepting"]),
        "transitions": [
          {"from": f, "label": l, "to": t}
          for f, l, t in nfa["transitions"]
        ],
      },
      "dfa": {
        "states": dfa_states,
        "start": dfa_start,
        "accepting": sorted(dfa_accepting),
        "transitions": [
          {"from": f, "label": l, "to": t}
          for f, l, t in dfa_transitions
        ],
      },
    }

  return {
    "defaultScenario": DEFAULT_SCENARIO_KEY,
    "scenarios": scenarios_payload,
  }


# ──────────────────────────────────────────────
#  HTML TEMPLATE
# ──────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Fate Automaton — Life Decisions & Death</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link  href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;1,300&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0806;
    --panel:    #110e0b;
    --border:   #2a2018;
    --gold:     #c9a84c;
    --gold2:    #f0d080;
    --red:      #8b1a1a;
    --red2:     #c0392b;
    --muted:    #5a4e3a;
    --text:     #d4c4a0;
    --epsilon:  #3a6b5a;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Crimson Pro', Georgia, serif;
    font-weight: 300;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── HEADER ── */
  header {
    padding: 2rem 3rem 1.2rem;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(180deg, #150f08 0%, var(--bg) 100%);
    position: relative;
    overflow: hidden;
  }
  header::before {
    content: "☠";
    position: absolute;
    right: 2.5rem; top: 50%; transform: translateY(-50%);
    font-size: 5rem;
    opacity: .06;
    pointer-events: none;
  }
  header h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.6rem, 3vw, 2.8rem);
    font-weight: 900;
    letter-spacing: .04em;
    color: var(--gold2);
    line-height: 1.1;
  }
  header p {
    margin-top: .4rem;
    font-size: 1rem;
    font-style: italic;
    color: var(--muted);
    max-width: 60ch;
  }

  .scenario-picker {
    margin-top: .9rem;
    display: flex;
    gap: .7rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .scenario-picker label {
    font-size: .85rem;
    color: var(--muted);
    letter-spacing: .06em;
    text-transform: uppercase;
  }
  .scenario-picker select {
    background: #1c1710;
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: .95rem;
    padding: .35rem .55rem;
  }
  .scenario-note {
    color: var(--gold);
    font-size: .92rem;
    font-style: italic;
  }

  /* ── TAB BAR ── */
  nav {
    display: flex;
    gap: 0;
    padding: 0 3rem;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  nav button {
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    color: var(--muted);
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    letter-spacing: .06em;
    padding: .85rem 1.6rem;
    cursor: pointer;
    transition: color .2s, border-color .2s;
    text-transform: uppercase;
  }
  nav button.active {
    color: var(--gold2);
    border-bottom-color: var(--gold);
  }
  nav button:hover:not(.active) { color: var(--text); }

  /* ── MAIN LAYOUT ── */
  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 1.5rem 3rem 2rem;
    gap: 1.2rem;
    min-height: 0;
  }

  .view {
    display: none;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
  }
  .view.active {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  /* ── LEGEND ── */
  .legend {
    display: flex; gap: 1.5rem; flex-wrap: wrap;
    font-size: .85rem; color: var(--muted);
  }
  .legend-item { display: flex; align-items: center; gap: .45rem; }
  .dot {
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid transparent; flex-shrink: 0;
  }
  .dot.start   { background: #1a3a1a; border-color: #4caf50; }
  .dot.death   { background: var(--red); border-color: var(--red2); }
  .dot.subset  { background: #1a2a3a; border-color: #4a90d9; }
  .dot.normal  { background: #1c1710; border-color: var(--gold); }
  .line-eps    { width: 24px; height: 2px; background: var(--epsilon); }
  .line-trans  { width: 24px; height: 2px; background: var(--gold); }

  /* ── GRAPH CONTAINER ── */
  .graph-wrap {
    flex: 1 1 auto;
    min-height: clamp(560px, 72vh, 1020px);
    height: auto;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--panel);
    position: relative;
    overflow: hidden;
  }
  .graph-wrap::after {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,.5) 100%);
    pointer-events: none;
  }
  .vis-network { border: none !important; }

  /* ── EXPLANATION PANEL ── */
  .explain {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.2rem 1.6rem;
    font-size: .95rem;
    line-height: 1.75;
  }
  .explain h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    color: var(--gold2);
    margin-bottom: .5rem;
    font-weight: 700;
  }
  .explain em { color: var(--gold); font-style: normal; }
  .explain .tag {
    display: inline-block;
    background: #1c1710;
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: .05rem .4rem;
    font-size: .82rem;
    color: var(--muted);
    font-family: monospace;
    margin: 0 .15rem;
  }

  /* ── BOTH VIEW ── */
  .both-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
  }
  .both-grid .graph-wrap { min-height: clamp(430px, 56vh, 760px); }

  @media (max-width: 900px) {
    .graph-wrap { min-height: clamp(420px, 62vh, 760px); }
    .both-grid .graph-wrap { min-height: clamp(320px, 48vh, 580px); }
  }
  .both-label {
    font-family: 'Playfair Display', serif;
    font-size: .9rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .4rem;
  }

  /* ── CONTROLS ── */
  .controls {
    display: flex; gap: .8rem; align-items: center; flex-wrap: wrap;
  }
  .btn {
    background: #1c1710;
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'Crimson Pro', serif;
    font-size: .9rem;
    padding: .4rem 1rem;
    border-radius: 2px;
    cursor: pointer;
    transition: border-color .2s, color .2s;
  }
  .btn:hover { border-color: var(--gold); color: var(--gold2); }
</style>
</head>
<body>

<header>
  <h1>The Fate Automaton</h1>
  <p>Every decision branches. Every branch converges. Some paths lead home — most lead nowhere good.</p>
  <div class="scenario-picker">
    <label for="scenario-select">Scenario</label>
    <select id="scenario-select"></select>
    <span id="scenario-note" class="scenario-note"></span>
  </div>
</header>

<nav>
  <button class="active" onclick="showView('nfa',this)">NFA — Life's Chaos</button>
  <button onclick="showView('dfa',this)">DFA — Determined Fate</button>
  <button onclick="showView('both',this)">Side by Side</button>
</nav>

<main>
  <!-- ── NFA VIEW ── -->
  <div id="view-nfa" class="view active">
    <div class="legend">
      <div class="legend-item"><div class="dot start"></div> Start (Alive)</div>
      <div class="legend-item"><div class="dot death"></div> Accepting / Death</div>
      <div class="legend-item"><div class="dot normal"></div> Life Stage</div>
      <div class="legend-item"><div class="line-eps"></div> ε-transition (silent)</div>
      <div class="legend-item"><div class="line-trans"></div> Decision</div>
    </div>
    <div class="controls">
      <button class="btn" onclick="fitByKey('nfa')">⟲ Fit View</button>
    </div>
    <div class="graph-wrap" id="graph-nfa"></div>
    <div class="explain">
      <h3>What is the NFA?</h3>
      A <em>Nondeterministic Finite Automaton</em> models life's uncertainty.
      From any state you may follow <em>multiple</em> possible transitions for the same choice —
      or slide silently through an <span class="tag">ε</span> (epsilon) transition without deciding anything at all.
      The machine exists in <em>all possible futures simultaneously</em>,
      which is exactly how real decisions feel: you don't know which branch you're on until it's too late.
    </div>
  </div>

  <!-- ── DFA VIEW ── -->
  <div id="view-dfa" class="view">
    <div class="legend">
      <div class="legend-item"><div class="dot start"></div> Start</div>
      <div class="legend-item"><div class="dot death"></div> Accepting / Death</div>
      <div class="legend-item"><div class="dot subset"></div> Merged Subset State</div>
      <div class="legend-item"><div class="dot normal"></div> Single State</div>
    </div>
    <div class="controls">
      <button class="btn" onclick="fitByKey('dfa')">⟲ Fit View</button>
    </div>
    <div class="graph-wrap" id="graph-dfa"></div>
    <div class="explain">
      <h3>What is the DFA?</h3>
      A <em>Deterministic Finite Automaton</em> is what fate looks like in hindsight.
      Using <em>subset construction</em>, each NFA state-set collapses into a single deterministic node.
      Epsilon ambiguity is absorbed. Branching is resolved.
      The result: <em>one path, one outcome</em> — no matter how many choices felt available.
      States shown in <span class="tag">{braces}</span> are merged NFA states, proving that your apparent freedom was always just one machine running in parallel.
    </div>
  </div>

  <!-- ── BOTH VIEW ── -->
  <div id="view-both" class="view">
    <div class="both-grid">
      <div>
        <div class="both-label">NFA — Nondeterministic</div>
        <div class="graph-wrap" id="graph-nfa2"></div>
      </div>
      <div>
        <div class="both-label">DFA — Deterministic</div>
        <div class="graph-wrap" id="graph-dfa2"></div>
      </div>
    </div>
    <div class="explain">
      <h3>NFA vs DFA</h3>
      The NFA (left) shows the <em>raw nondeterminism</em> of life — multiple transitions per symbol,
      silent ε-moves, states that blur into one another.
      The DFA (right) is the <em>mathematical truth</em>: every NFA has an equivalent DFA,
      built by tracking all possible NFA states simultaneously.
      The chaos on the left and the clarity on the right describe <em>exactly the same language</em> —
      the same set of decision sequences that end in death.
      Free will is the NFA. Fate is the DFA.
    </div>
  </div>
</main>

<script>
const APP_DATA = __DATA__;

const COLORS = {
  start:   { bg: '#1a3a1a', border: '#4caf50', font: '#a5d6a7' },
  death:   { bg: '#2a0a0a', border: '#c0392b', font: '#ef9a9a' },
  subset:  { bg: '#0f1e2e', border: '#4a90d9', font: '#90caf9' },
  normal:  { bg: '#1c1710', border: '#c9a84c', font: '#f0d080' },
};

const EDGE_COLOR  = '#c9a84c';
const EDGE_EPS    = '#3a6b5a';
const networks = { nfa: null, dfa: null, nfa2: null, dfa2: null };
let activeScenarioKey = APP_DATA.defaultScenario;
let activeView = 'nfa';

function nodeStyle(id, isStart, isAccepting, isSubset) {
  let c = COLORS.normal;
  if (isAccepting) c = COLORS.death;
  else if (isStart) c = COLORS.start;
  else if (isSubset) c = COLORS.subset;

  return {
    id, label: id,
    color: { background: c.bg, border: c.border, highlight: { background: c.bg, border: c.font } },
    font: { color: c.font, size: 13, face: 'Crimson Pro, Georgia, serif' },
    borderWidth: isStart || isAccepting ? 3 : 2,
    shape: isAccepting ? 'ellipse' : 'box',
    shadow: { enabled: true, color: 'rgba(0,0,0,.7)', size: 12, x: 3, y: 3 },
    margin: 10,
  };
}

function buildNodes(data, type) {
  return data.states.map(id => {
    const isStart    = id === data.start;
    const isAccepting= data.accepting.includes(id);
    const isSubset   = type === 'dfa' && id.startsWith('{');
    return nodeStyle(id, isStart, isAccepting, isSubset);
  });
}

function buildEdges(data) {
  // Group parallel edges
  const groups = {};
  data.transitions.forEach(t => {
    const key = `${t.from}||${t.to}`;
    if (!groups[key]) groups[key] = [];
    groups[key].push(t.label);
  });

  return Object.entries(groups).map(([key, labels], i) => {
    const [from, to] = key.split('||');
    const isEps = labels.every(l => l === 'ε');
    const isSelf = from === to;
    const reverseKey = `${to}||${from}`;
    const hasReverse = !!groups[reverseKey] && !isSelf;
    const isForward = from.localeCompare(to) <= 0;

    let smoothConfig = false;
    let vAdjust = 0;

    if (isSelf) {
      smoothConfig = { enabled: true, type: 'curvedCW', roundness: 0.8 };
      vAdjust = -8;
    } else if (hasReverse) {
      smoothConfig = {
        enabled: true,
        type: isForward ? 'curvedCW' : 'curvedCCW',
        roundness: 0.22,
      };
      vAdjust = isForward ? -10 : 10;
    }

    return {
      from, to,
      label: labels.join('  |  '),
      color: { color: isEps ? EDGE_EPS : EDGE_COLOR, highlight: '#f0d080' },
      font: {
        color: isEps ? '#5aaa8a' : '#b8a070',
        size: 10,
        face: 'Crimson Pro, Georgia, serif',
        align: 'horizontal',
        vadjust: vAdjust,
        strokeWidth: 3,
        strokeColor: '#0a0806',
      },
      arrows: { to: { enabled: true, scaleFactor: .7 } },
      smooth: smoothConfig,
      dashes: isEps,
      width: 1.5,
    };
  });
}

const OPTIONS = {
  autoResize: true,
  physics: {
    enabled: true,
    solver: 'repulsion',
    repulsion: {
      nodeDistance: 230,
      springLength: 190,
      springConstant: 0.045,
      damping: 0.32,
      centralGravity: 0.12,
    },
    stabilization: {
      enabled: true,
      iterations: 500,
      updateInterval: 50,
      fit: false,
    },
  },
  interaction: { hover: true, tooltipDelay: 200, zoomView: true, dragView: true },
  layout: { improvedLayout: true },
};

function makeNetwork(containerId, data, type) {
  const container = document.getElementById(containerId);
  if (!container) return null;
  const nodes = new vis.DataSet(buildNodes(data, type));
  const edges = new vis.DataSet(buildEdges(data));
  const net = new vis.Network(container, { nodes, edges }, OPTIONS);
  net.once('stabilizationIterationsDone', () => {
    net.setOptions({ physics: { enabled: false } });
    scheduleFit(net, containerId);
    setTimeout(() => scheduleFit(net, containerId), 120);
  });
  return net;
}

function getScenario() {
  return APP_DATA.scenarios[activeScenarioKey];
}

function scheduleFit(network, containerId) {
  const container = document.getElementById(containerId);
  if (!network || !container) return;

  let attempts = 0;
  const tryFit = () => {
    attempts += 1;
    const visible = container.offsetParent !== null;
    const hasSize = container.clientWidth > 0 && container.clientHeight > 0;
    if (visible && hasSize) {
      // Keep vis canvas and the visible panel dimensions in sync.
      network.setSize(`${container.clientWidth}px`, `${container.clientHeight}px`);
      network.redraw();
      network.fit({
        animation: { duration: 450, easingFunction: 'easeInOutQuad' },
        minZoomLevel: 0.2,
        maxZoomLevel: 1.6,
      });
      return;
    }
    if (attempts < 24) {
      requestAnimationFrame(tryFit);
    }
  };

  requestAnimationFrame(tryFit);
}

function resetNetworks() {
  Object.keys(networks).forEach(key => {
    if (networks[key]) {
      networks[key].destroy();
      networks[key] = null;
    }
  });
}

function ensureNetwork(key) {
  const scenario = getScenario();
  const config = {
    nfa:  { containerId: 'graph-nfa', type: 'nfa', data: scenario.nfa },
    dfa:  { containerId: 'graph-dfa', type: 'dfa', data: scenario.dfa },
    nfa2: { containerId: 'graph-nfa2', type: 'nfa', data: scenario.nfa },
    dfa2: { containerId: 'graph-dfa2', type: 'dfa', data: scenario.dfa },
  }[key];

  if (!config) return null;
  if (!networks[key]) {
    networks[key] = makeNetwork(config.containerId, config.data, config.type);
  }
  return networks[key];
}

function fitByKey(key) {
  const net = networks[key];
  if (!net) return;
  const containers = {
    nfa: 'graph-nfa',
    dfa: 'graph-dfa',
    nfa2: 'graph-nfa2',
    dfa2: 'graph-dfa2',
  };
  scheduleFit(net, containers[key]);
}

function refreshActiveView() {
  if (activeView === 'both') {
    ensureNetwork('nfa2');
    ensureNetwork('dfa2');
    fitByKey('nfa2');
    fitByKey('dfa2');
    return;
  }
  ensureNetwork(activeView);
  fitByKey(activeView);
}

function hydrateScenarioPicker() {
  const selector = document.getElementById('scenario-select');
  const note = document.getElementById('scenario-note');
  if (!selector || !note) return;

  Object.entries(APP_DATA.scenarios).forEach(([key, value]) => {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = value.title;
    selector.appendChild(option);
  });

  selector.value = activeScenarioKey;
  note.textContent = getScenario().description;

  selector.addEventListener('change', event => {
    activeScenarioKey = event.target.value;
    note.textContent = getScenario().description;
    resetNetworks();
    refreshActiveView();
  });
}

function showView(name, btn) {
  activeView = name;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  btn.classList.add('active');

  refreshActiveView();
}

hydrateScenarioPicker();
refreshActiveView();
</script>
</body>
</html>
"""

def build_html(payload):
    return HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, indent=2))


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────

def main():
    payload  = build_payload()
    html     = build_html(payload)

    out_path = os.path.join(os.path.dirname(__file__), "fate_automaton.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    scenario = SCENARIOS[DEFAULT_SCENARIO_KEY]
    nfa_data = scenario["nfa"]

    print("=" * 60)
    print("  FATE AUTOMATON — NFA / DFA Visualizer")
    print("=" * 60)
    print(f"\n  Scenarios available: {len(SCENARIOS)}")
    print(f"  Default scenario: {scenario['title']}")
    print(f"\n  NFA states  : {len(nfa_data['states'])}")
    print(f"  NFA transitions: {len(nfa_data['transitions'])}  (including ε-moves)")

    dfa_states, _, dfa_accepting, dfa_trans = nfa_to_dfa(
      nfa_data["start"], nfa_data["transitions"], nfa_data["accepting"]
    )
    print(f"\n  DFA states  : {len(dfa_states)}  (after subset construction)")
    print(f"  DFA transitions: {len(dfa_trans)}")
    print(f"  DFA accepting: {dfa_accepting}")
    print(f"\n  Output → {out_path}")
    print("\n  Opening browser…\n")

    webbrowser.open(f"file://{os.path.abspath(out_path)}")

if __name__ == "__main__":
    main()