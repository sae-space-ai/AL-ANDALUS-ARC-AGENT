# AL-ANDALUS ARC AGENT

**ARC Prize 2026 — ARC-AGI-3 Competition**

An adaptive AI agent that observes unknown games, explores available actions, learns from consequences, and makes evidence-based decisions.

## Objective

Surpass the official Random Agent through in-game learning and intelligent action selection.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MyAgent (Agent)                       │
│                                                         │
│  FrameAnalyzer ──→ ActionMemory ──→ Planner            │
│       │                │                │               │
│       └────────────────┼────────────────┘               │
│                        │                                │
│                   Explorer                              │
│           (Systematic → Informative → Exploit → Random) │
└─────────────────────────────────────────────────────────┘
```

### Modules

| Module | Purpose |
|--------|---------|
| **FrameAnalyzer** | Pixel diff, region detection, object finding |
| **ActionMemory** | Transition records, effectiveness scores, cycle detection |
| **Explorer** | Systematic → Informative → Exploit → Random strategies |
| **Planner** | Hypothesis-based action selection with exploration/exploitation balance |

## Files

```
agent/
├── my_agent.py          # Full agent (for ARC-AGI-3-Agents framework)
└── kaggle_cell.py       # Self-contained Kaggle notebook cell

tests/
└── test_agent_static.py # Static verification (no game engine needed)
```

## Quick Start

### Local Development (with ARC-AGI-3-Agents framework)

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git
cd ARC-AGI-3-Agents
cp /path/to/agent/my_agent.py agents/my_agent.py
export ARC_API_KEY="your_key"
uv run main.py --agent=myagent --game=ls20
```

### Kaggle Submission (with Kaggle Starter)

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter.git
cd ARC-AGI-3-Kaggle-Starter
cp /path/to/agent/my_agent.py agent/my_agent.py
make setup
make play-local       # Test locally
make submit           # Push to Kaggle
```

### Static Tests

```bash
python tests/test_agent_static.py
```

## API Compliance

- ✅ Inherits from `Agent` base class
- ✅ Implements `is_done(frames, latest_frame) -> bool`
- ✅ Implements `choose_action(frames, latest_frame) -> GameAction`
- ✅ Uses `FrameData`, `GameAction`, `GameState` from `arcengine`
- ✅ Reads `available_actions` from `latest_frame`
- ✅ Uses `set_data()` for complex actions (ACTION6)
- ✅ RESET only on NOT_PLAYED or GAME_OVER
- ✅ MAX_ACTIONS = 80
- ✅ No external API calls
- ✅ No internet dependency

## Strategy

1. **Perceive**: Analyze frame differences between consecutive observations
2. **Explore**: Systematically try each available action, then shift to informative selection
3. **Learn**: Build action→effect model, track what causes changes/progress/death
4. **Plan**: Use hypotheses with confidence levels to guide action selection
5. **Adapt**: Detect cycles, switch strategies, enter emergency mode when low on actions

## Dependencies

- Python ≥ 3.12
- `arcengine` 0.9.3
- `arc-agi` (latest)
- No GPU required

## Status

| Component | Status |
|-----------|--------|
| Agent code | ✅ Complete |
| Static tests | ✅ Passing |
| API compliance | ✅ Verified |
| Kaggle cell | ✅ Ready |
| Local testing | ⏳ Requires ARC_API_KEY |
| Kaggle submission | ⏳ Pending local validation |

## License

MIT
