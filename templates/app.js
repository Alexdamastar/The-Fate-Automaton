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
  net.on('click', params => {
    if (params.nodes && params.nodes.length > 0) {
      const domPointer = params.pointer && params.pointer.DOM ? params.pointer.DOM : null;
      showStateTooltip(type, params.nodes[0], containerId, domPointer);
      return;
    }
    hideStateTooltip();
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

function hideStateTooltip() {
  const box = document.getElementById('state-tooltip');
  if (!box) return;
  box.classList.remove('active');
}

function showStateTooltip(machineType, stateId, containerId, domPointer) {
  const box = document.getElementById('state-tooltip');
  const title = document.getElementById('state-tooltip-title');
  const text = document.getElementById('state-tooltip-text');
  const chip = document.getElementById('state-tooltip-chip');
  const container = document.getElementById(containerId);
  if (!box || !title || !text || !chip || !container || !domPointer) return;

  const scenario = getScenario();
  const details = scenario[machineType]?.stateDetails || {};
  const body = details[stateId] || 'No description available for this state yet.';
  const modeLabel = machineType.toUpperCase();

  title.textContent = stateId;
  chip.textContent = `${scenario.title} - ${modeLabel}`;
  text.textContent = body;
  box.classList.add('active');

  const rect = container.getBoundingClientRect();
  const anchorX = rect.left + domPointer.x;
  const anchorY = rect.top + domPointer.y;
  const padding = 12;
  const gap = 14;
  const tooltipWidth = box.offsetWidth || 320;
  const tooltipHeight = box.offsetHeight || 150;

  let left = anchorX - tooltipWidth / 2;
  left = Math.max(padding, Math.min(left, window.innerWidth - tooltipWidth - padding));

  let top = anchorY - tooltipHeight - gap;
  if (top < padding) {
    top = Math.min(window.innerHeight - tooltipHeight - padding, anchorY + gap);
  }

  box.style.left = `${left}px`;
  box.style.top = `${top}px`;
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
  hideStateTooltip();
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
    hideStateTooltip();
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
