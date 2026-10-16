import { useState } from 'react'

const TABS = ['Overview', 'Architecture', 'Agent Code', 'Kaggle Cell', 'Tests', 'Status'] as const
type Tab = typeof TABS[number]

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">
      {/* Header */}
      <header className="border-b border-amber-900/40 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-amber-500 to-red-700 flex items-center justify-center text-sm font-bold">
              AA
            </div>
            <div>
              <h1 className="text-lg font-bold text-amber-400">AL-ANDALUS ARC AGENT</h1>
              <p className="text-xs text-gray-500">ARC Prize 2026 — ARC-AGI-3 Competition</p>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            <span className="text-green-400">●</span> v1.0.0
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm whitespace-nowrap transition-colors border-b-2 ${
                activeTab === tab
                  ? 'border-amber-500 text-amber-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'Overview' && <OverviewTab />}
        {activeTab === 'Architecture' && <ArchitectureTab />}
        {activeTab === 'Agent Code' && <AgentCodeTab />}
        {activeTab === 'Kaggle Cell' && <KaggleCellTab />}
        {activeTab === 'Tests' && <TestsTab />}
        {activeTab === 'Status' && <StatusTab />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-600">
        AL-ANDALUS AI LAB — Built for ARC Prize 2026
      </footer>
    </div>
  )
}

function OverviewTab() {
  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-bold text-amber-400 mb-4">Mission</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <p className="text-gray-300 leading-relaxed">
            Build an adaptive AI agent that competes in ARC-AGI-3 by observing unknown games,
            exploring available actions, learning from consequences, and making evidence-based decisions.
          </p>
          <p className="text-gray-300 leading-relaxed mt-3">
            <strong className="text-amber-300">Primary objective:</strong> Surpass the official Random Agent
            through in-game learning and intelligent action selection.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-gray-200 mb-4">Key Principles</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: 'Observe', desc: 'Analyze frame differences, detect regions, track colors and movement' },
            { title: 'Explore', desc: 'Systematically test actions, select informative experiments' },
            { title: 'Learn', desc: 'Build action→effect model, distinguish progress from noise' },
            { title: 'Act', desc: 'Choose evidence-based actions, adapt strategy when stuck' },
          ].map(item => (
            <div key={item.title} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-amber-400 font-bold mb-2">{item.title}</h3>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-gray-200 mb-4">Compliance</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <ul className="space-y-2 text-sm text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Inherits from official Agent base class
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Implements is_done() and choose_action() per specification
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Uses FrameData, GameAction, GameState from arcengine
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Reads available_actions from latest_frame
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Uses set_data() for complex actions (ACTION6 coordinates)
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              RESET only on NOT_PLAYED or GAME_OVER states
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              MAX_ACTIONS = 80 (matches framework default)
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              No external API calls, no internet dependency
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              Compatible with Kaggle notebook submission format
            </li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-gray-200 mb-4">File Structure</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 font-mono text-sm">
          <pre className="text-gray-300">{`agent/
├── my_agent.py          # Full agent implementation
└── kaggle_cell.py       # Self-contained Kaggle notebook cell

tests/
└── test_agent_static.py # Static verification tests (no game engine needed)

README.md                # This documentation`}</pre>
        </div>
      </section>
    </div>
  )
}

function ArchitectureTab() {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-amber-400 mb-4">Agent Architecture</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-4">Module Diagram</h3>
        <pre className="text-xs text-gray-400 overflow-x-auto">{`
┌─────────────────────────────────────────────────────────────────┐
│                        MyAgent (Agent)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  PERCEPTION  │  │    MEMORY    │  │     PLANNING         │  │
│  │              │  │              │  │                      │  │
│  │ FrameAnalyzer│──│ ActionMemory │──│      Planner         │  │
│  │              │  │              │  │                      │  │
│  │ • Frame diff │  │ • Transitions│  │ • Hypotheses         │  │
│  │ • Regions    │  │ • Statistics │  │ • Confidence         │  │
│  │ • Objects    │  │ • Scores     │  │ • Action selection   │  │
│  │ • Colors     │  │ • Cycles     │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                  │                    │                │
│         └──────────────────┼────────────────────┘                │
│                            │                                     │
│                   ┌────────┴────────┐                            │
│                   │   EXPLORATION   │                            │
│                   │                 │                            │
│                   │    Explorer     │                            │
│                   │                 │                            │
│                   │ • Systematic    │                            │
│                   │ • Informative   │                            │
│                   │ • Exploit       │                            │
│                   │ • Random        │                            │
│                   └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
`}</pre>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-amber-400 font-bold mb-3">Perception (FrameAnalyzer)</h3>
          <ul className="text-sm text-gray-400 space-y-2">
            <li>• Computes pixel-level differences between frames</li>
            <li>• Detects change regions with bounding boxes</li>
            <li>• Finds connected object components</li>
            <li>• Tracks dominant colors</li>
            <li>• Creates frame hashes for state comparison</li>
          </ul>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-amber-400 font-bold mb-3">Memory (ActionMemory)</h3>
          <ul className="text-sm text-gray-400 space-y-2">
            <li>• Records action→outcome transitions</li>
            <li>• Tracks per-action effectiveness scores</li>
            <li>• Detects repetitive action cycles</li>
            <li>• Maintains running averages of change magnitude</li>
            <li>• Bounded to 500 records (prevents memory leak)</li>
          </ul>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-amber-400 font-bold mb-3">Exploration (Explorer)</h3>
          <ul className="text-sm text-gray-400 space-y-2">
            <li>• <strong>Systematic:</strong> Try each action in order</li>
            <li>• <strong>Informative:</strong> Pick least-tried actions</li>
            <li>• <strong>Exploit:</strong> Use best scoring action</li>
            <li>• <strong>Random:</strong> Fallback when stuck</li>
            <li>• Auto-transitions between strategies</li>
          </ul>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-amber-400 font-bold mb-3">Planning (Planner)</h3>
          <ul className="text-sm text-gray-400 space-y-2">
            <li>• Maintains hypotheses about action effects</li>
            <li>• Assigns confidence to each hypothesis</li>
            <li>• Balances exploration vs exploitation</li>
            <li>• Adapts exploration probability over time</li>
            <li>• Emergency mode when actions are running low</li>
          </ul>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-4">Decision Flow</h3>
        <pre className="text-xs text-gray-400 overflow-x-auto">{`
choose_action(latest_frame)
    │
    ├── state == NOT_PLAYED or GAME_OVER?
    │       └── YES → RESET (with memory reset on GAME_OVER)
    │
    ├── Extract available_actions from frame
    │
    ├── Perception: analyze current frame
    │       └── Compute diff from previous frame
    │
    ├── Learning: record transition
    │       ├── Update action effectiveness
    │       ├── Update planner hypotheses
    │       └── Update exploration strategy
    │
    ├── Decision: select action
    │       ├── Check for cycles → break if detected
    │       ├── Check remaining actions → emergency mode if low
    │       └── Planner.select_action() with exploration/exploitation balance
    │
    └── Attach reasoning and return action
`}</pre>
      </div>
    </div>
  )
}

function AgentCodeTab() {
  const [copied, setCopied] = useState(false)

  const code = `"""
AL-ANDALUS ARC AGENT
====================
ARC Prize 2026 — ARC-AGI-3 Competition

An adaptive agent that observes, explores, learns, and acts.
"""
from __future__ import annotations

import random
import time
import logging
from typing import Any, Optional
from collections import defaultdict
from enum import Enum

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent

logger = logging.getLogger(__name__)


class FrameAnalyzer:
    """Analyzes frames to extract meaningful information."""

    @staticmethod
    def frame_to_hash(frame: list[list[int]]) -> int:
        flat = []
        for row in frame:
            flat.extend(row)
        return hash(tuple(flat))

    @staticmethod
    def compute_frame_diff(frame_a, frame_b) -> dict:
        """Compute detailed differences between two frames."""
        if not frame_a or not frame_b:
            return {"changed_pixels": 0, "regions": [], "has_change": False}
        h = min(len(frame_a), len(frame_b))
        w = min(len(frame_a[0]) if frame_a else 0,
                len(frame_b[0]) if frame_b else 0)
        changed_pixels = 0
        changed_positions = []
        for y in range(h):
            for x in range(w):
                if frame_a[y][x] != frame_b[y][x]:
                    changed_pixels += 1
                    changed_positions.append((x, y))
        regions = []
        if changed_positions:
            cx = sum(p[0] for p in changed_positions) / len(changed_positions)
            cy = sum(p[1] for p in changed_positions) / len(changed_positions)
            regions = [{"center": (cx, cy), "pixel_count": len(changed_positions)}]
        return {"changed_pixels": changed_pixels, "regions": regions,
                "has_change": changed_pixels > 0}

    @staticmethod
    def find_object_centers(frame, background=0):
        """Find centers of non-background connected regions."""
        # ... (BFS connected components)
        pass


class ActionMemory:
    """Memory system that tracks action consequences."""
    MAX_RECORDS = 500

    def __init__(self):
        self.transitions = []
        self.action_effectiveness = defaultdict(lambda: {
            "total": 0, "caused_change": 0, "caused_progress": 0,
            "caused_death": 0, "no_effect_count": 0
        })
        self.recent_actions = []

    def record_transition(self, record):
        """Record and update statistics."""
        # ... (update effectiveness scores)
        pass

    def get_action_score(self, action) -> float:
        """Score action based on learned effectiveness."""
        # Rewards: change_rate, progress_rate
        # Penalties: death_rate, no_effect_rate
        # Bonus: exploration (less tried = higher)
        pass

    def is_in_cycle(self) -> bool:
        """Detect repeating action patterns."""
        pass


class Explorer:
    """Manages exploration of the action space."""
    # Strategies: SYSTEMATIC → INFORMATIVE → EXPLOIT → RANDOM
    pass


class Planner:
    """Short-horizon planner based on evidence."""
    # Maintains hypotheses with confidence levels
    # Balances exploration probability vs exploitation
    pass


class MyAgent(Agent):
    """AL-ANDALUS ARC AGENT: Adaptive observe-explore-learn-act agent."""

    MAX_ACTIONS = 80

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize all modules
        self.memory = ActionMemory()
        self.explorer = None
        self.planner = Planner()
        # ... state tracking

    def is_done(self, frames, latest_frame) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames, latest_frame) -> GameAction:
        # 1. Handle NOT_PLAYED / GAME_OVER → RESET
        # 2. Extract available actions
        # 3. Perceive: analyze frame differences
        # 4. Learn: record transition, update memory
        # 5. Plan: select action via planner + explorer
        # 6. Attach reasoning
        pass`

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-amber-400">agent/my_agent.py</h2>
        <button
          onClick={handleCopy}
          className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 hover:bg-gray-700 transition-colors"
        >
          {copied ? '✓ Copied' : 'Copy Code'}
        </button>
      </div>
      <p className="text-sm text-gray-400">
        Full agent implementation. See the <code className="text-amber-400">agent/my_agent.py</code> file for the complete source.
      </p>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 overflow-auto max-h-[70vh]">
        <pre className="text-xs text-gray-300 whitespace-pre-wrap">{code}</pre>
      </div>
      <p className="text-xs text-gray-500">
        Note: This is a summary view. The full implementation with all methods is in <code>agent/my_agent.py</code>.
      </p>
    </div>
  )
}

function KaggleCellTab() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-amber-400">Kaggle Notebook Integration</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Usage Instructions</h3>
        <ol className="text-sm text-gray-300 space-y-3 list-decimal list-inside">
          <li>Open your Kaggle notebook for ARC Prize 2026</li>
          <li>Create a new cell with the magic command: <code className="text-amber-400 bg-gray-800 px-1 rounded">%%writefile /tmp/my_agent.py</code></li>
          <li>Paste the contents of <code className="text-amber-400">agent/kaggle_cell.py</code></li>
          <li>Run the cell — it writes the agent file</li>
          <li>The notebook's execution cell will import and run your agent</li>
        </ol>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Key Differences from Full Version</h3>
        <ul className="text-sm text-gray-400 space-y-2">
          <li>• Self-contained: no external file dependencies</li>
          <li>• Same algorithm, same modules, same logic</li>
          <li>• Written as a single file for Kaggle's notebook format</li>
          <li>• Uses <code className="text-amber-400">%%writefile /tmp/my_agent.py</code> to avoid output file conflicts</li>
        </ul>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-4">
        <p className="text-sm text-yellow-300">
          <strong>⚠ Important:</strong> The file is written to <code>/tmp/my_agent.py</code> (not <code>/kaggle/working/</code>)
          to prevent Kaggle's submission UI from selecting it instead of <code>submission.parquet</code>.
        </p>
      </div>
    </div>
  )
}

function TestsTab() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-amber-400">Static Verification Tests</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Test Suite: tests/test_agent_static.py</h3>
        <p className="text-sm text-gray-400 mb-4">
          These tests verify agent structure and logic without requiring the actual game engine.
          They mock the arcengine and agents.agent modules.
        </p>

        <div className="space-y-2">
          {[
            { name: 'test_agent_file_exists', desc: 'Verifies agent/my_agent.py exists', status: 'pass' },
            { name: 'test_agent_imports', desc: 'Verifies module imports without errors', status: 'pass' },
            { name: 'test_myagent_class_structure', desc: 'Verifies required methods exist', status: 'pass' },
            { name: 'test_is_done_on_win', desc: 'Verifies is_done returns True on WIN', status: 'pass' },
            { name: 'test_is_done_on_playing', desc: 'Verifies is_done returns False on PLAYING', status: 'pass' },
            { name: 'test_choose_action_on_not_played', desc: 'Verifies RESET on NOT_PLAYED', status: 'pass' },
            { name: 'test_choose_action_on_game_over', desc: 'Verifies RESET on GAME_OVER', status: 'pass' },
            { name: 'test_frame_analyzer_diff', desc: 'Verifies frame difference detection', status: 'pass' },
            { name: 'test_frame_analyzer_no_diff', desc: 'Verifies no-change detection', status: 'pass' },
            { name: 'test_action_memory_scoring', desc: 'Verifies action scoring logic', status: 'pass' },
            { name: 'test_cycle_detection', desc: 'Verifies cycle detection works', status: 'pass' },
            { name: 'test_no_cycle', desc: 'Verifies no false positives', status: 'pass' },
            { name: 'test_explorer_strategies', desc: 'Verifies exploration strategies', status: 'pass' },
            { name: 'test_max_actions_limit', desc: 'Verifies MAX_ACTIONS = 80', status: 'pass' },
            { name: 'test_kaggle_cell_exists', desc: 'Verifies Kaggle cell file exists', status: 'pass' },
            { name: 'test_kaggle_cell_has_myagent', desc: 'Verifies Kaggle cell has MyAgent', status: 'pass' },
          ].map(test => (
            <div key={test.name} className="flex items-center gap-3 py-2 border-b border-gray-800 last:border-0">
              <span className="text-green-400 text-xs">✓</span>
              <code className="text-xs text-amber-300 flex-1">{test.name}</code>
              <span className="text-xs text-gray-500">{test.desc}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Integration Tests (NOT_RUN)</h3>
        <p className="text-sm text-gray-400 mb-3">
          These tests require the actual ARC-AGI-3 game engine and API access:
        </p>
        <ul className="text-sm text-gray-500 space-y-1">
          <li>• <code>make verify-local</code> — Smoke test on 2 games</li>
          <li>• <code>make play-local</code> — Full run on all 25 games</li>
          <li>• Comparison vs Random Agent (same seed conditions)</li>
          <li>• Level completion tracking</li>
          <li>• Action efficiency metrics</li>
        </ul>
        <p className="text-xs text-yellow-400 mt-3">
          ⚠ These require: ARC_API_KEY, arc-agi package, and game data access.
        </p>
      </div>
    </div>
  )
}

function StatusTab() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-amber-400">Project Status</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-900/20 border border-green-800/50 rounded-lg p-4">
          <h3 className="text-green-400 font-bold text-sm mb-2">COMPLETED</h3>
          <ul className="text-xs text-gray-300 space-y-1">
            <li>✓ Agent architecture designed</li>
            <li>✓ MyAgent class implemented</li>
            <li>✓ FrameAnalyzer module</li>
            <li>✓ ActionMemory module</li>
            <li>✓ Explorer module</li>
            <li>✓ Planner module</li>
            <li>✓ Kaggle cell prepared</li>
            <li>✓ Static tests passing</li>
            <li>✓ API compliance verified</li>
          </ul>
        </div>

        <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-4">
          <h3 className="text-yellow-400 font-bold text-sm mb-2">PENDING</h3>
          <ul className="text-xs text-gray-300 space-y-1">
            <li>○ Local play testing</li>
            <li>○ Random Agent comparison</li>
            <li>○ Per-game strategy tuning</li>
            <li>○ ACTION6 coordinate optimization</li>
            <li>○ Multi-level memory persistence</li>
            <li>○ Kaggle submission</li>
          </ul>
        </div>

        <div className="bg-red-900/20 border border-red-800/50 rounded-lg p-4">
          <h3 className="text-red-400 font-bold text-sm mb-2">BLOCKED</h3>
          <ul className="text-xs text-gray-300 space-y-1">
            <li>✗ Requires ARC_API_KEY</li>
            <li>✗ Requires arc-agi package</li>
            <li>✗ Requires game environment data</li>
            <li>✗ Cannot run in this environment</li>
          </ul>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Dependencies</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-800">
              <th className="text-left py-2">Package</th>
              <th className="text-left py-2">Version</th>
              <th className="text-left py-2">Status</th>
            </tr>
          </thead>
          <tbody className="text-gray-300">
            <tr className="border-b border-gray-800/50">
              <td className="py-2"><code>arcengine</code></td>
              <td className="py-2">0.9.3</td>
              <td className="py-2 text-yellow-400">Required at runtime</td>
            </tr>
            <tr className="border-b border-gray-800/50">
              <td className="py-2"><code>arc-agi</code></td>
              <td className="py-2">latest</td>
              <td className="py-2 text-yellow-400">Required at runtime</td>
            </tr>
            <tr className="border-b border-gray-800/50">
              <td className="py-2"><code>python</code></td>
              <td className="py-2">≥3.12</td>
              <td className="py-2 text-green-400">Standard</td>
            </tr>
            <tr>
              <td className="py-2"><code>numpy</code></td>
              <td className="py-2">any</td>
              <td className="py-2 text-green-400">Standard</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-200 mb-3">Next Steps</h3>
        <ol className="text-sm text-gray-300 space-y-2 list-decimal list-inside">
          <li>Clone ARC-AGI-3-Kaggle-Starter repository</li>
          <li>Copy <code className="text-amber-400">agent/my_agent.py</code> into the starter kit</li>
          <li>Set ARC_API_KEY environment variable</li>
          <li>Run <code className="text-amber-400">make verify-local</code> for smoke test</li>
          <li>Run <code className="text-amber-400">make play-local</code> for full evaluation</li>
          <li>Compare results against Random Agent baseline</li>
          <li>Iterate on strategy based on per-game results</li>
          <li>Submit via <code className="text-amber-400">make submit</code> when confident</li>
        </ol>
      </div>
    </div>
  )
}

export default App
