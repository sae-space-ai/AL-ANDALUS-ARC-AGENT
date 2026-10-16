"""
AL-ANDALUS ARC AGENT — Static Verification Tests
=================================================
These tests verify the agent's structure and logic without requiring
the actual ARC-AGI-3 game engine or API access.

Run: python -m pytest tests/test_agent_static.py -v
"""
from __future__ import annotations

import sys
import os
import importlib.util
from unittest.mock import MagicMock, patch
from enum import Enum
from typing import Any

# ── Mock the arcengine module for static testing ─────────────────────────────

class MockGameState(Enum):
    NOT_PLAYED = "not_played"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    WIN = "win"


class MockGameAction(Enum):
    RESET = 0
    ACTION1 = 1
    ACTION2 = 2
    ACTION3 = 3
    ACTION4 = 4
    ACTION5 = 5
    ACTION6 = 6
    ACTION7 = 7

    def is_simple(self) -> bool:
        return self != MockGameAction.ACTION6

    def is_complex(self) -> bool:
        return self == MockGameAction.ACTION6

    def set_data(self, data: dict) -> None:
        self._data = data

    @property
    def name(self) -> str:
        return super().name


class MockFrameData:
    def __init__(self, game_id="", frame=None, state=None, levels_completed=0,
                 win_levels=1, guid="", full_reset=False, available_actions=None):
        self.game_id = game_id
        self.frame = frame or [[0] * 64 for _ in range(64)]
        self.state = state or MockGameState.NOT_PLAYED
        self.levels_completed = levels_completed
        self.win_levels = win_levels
        self.guid = guid
        self.full_reset = full_reset
        self.available_actions = available_actions or [1, 2, 3, 4, 5, 6, 7]


# Create mock modules
mock_arcengine = MagicMock()
mock_arcengine.FrameData = MockFrameData
mock_arcengine.GameAction = MockGameAction
mock_arcengine.GameState = MockGameState

# Mock agents.agent
class MockAgent:
    MAX_ACTIONS = 80
    action_counter = 0

    def __init__(self, *args, **kwargs):
        self.game_id = kwargs.get('game_id', 'test_game')
        self.frames = [MockFrameData()]

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def cleanup(self, scorecard=None):
        pass


mock_agents = MagicMock()
mock_agents_agent = MagicMock()
mock_agents_agent.Agent = MockAgent

# Install mocks
sys.modules['arcengine'] = mock_arcengine
sys.modules['agents'] = mock_agents
sys.modules['agents.agent'] = mock_agents_agent

# ── Now import the agent ─────────────────────────────────────────────────────

# Add agent directory to path
agent_dir = os.path.join(os.path.dirname(__file__), '..', 'agent')
sys.path.insert(0, os.path.abspath(agent_dir))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_agent_file_exists():
    """Verify the agent file exists."""
    agent_path = os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    assert os.path.exists(agent_path), f"Agent file not found at {agent_path}"


def test_agent_imports():
    """Verify the agent can be imported without errors."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    assert spec is not None, "Could not create module spec"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, 'MyAgent'), "MyAgent class not found"


def test_myagent_class_structure():
    """Verify MyAgent has required methods."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    MyAgent = module.MyAgent
    assert hasattr(MyAgent, '__init__'), "Missing __init__"
    assert hasattr(MyAgent, 'is_done'), "Missing is_done"
    assert hasattr(MyAgent, 'choose_action'), "Missing choose_action"
    assert hasattr(MyAgent, 'MAX_ACTIONS'), "Missing MAX_ACTIONS"


def test_is_done_on_win():
    """Verify is_done returns True on WIN state."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    MyAgent = module.MyAgent
    agent = MyAgent.__new__(MyAgent)
    agent.game_id = "test"

    win_frame = MockFrameData(state=MockGameState.WIN)
    assert agent.is_done([], win_frame) == True


def test_is_done_on_playing():
    """Verify is_done returns False on PLAYING state."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    MyAgent = module.MyAgent
    agent = MyAgent.__new__(MyAgent)
    agent.game_id = "test"

    playing_frame = MockFrameData(state=MockGameState.PLAYING)
    assert agent.is_done([], playing_frame) == False


def test_choose_action_on_not_played():
    """Verify RESET is returned when game is NOT_PLAYED."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    MyAgent = module.MyAgent
    agent = MyAgent.__new__(MyAgent)
    agent.game_id = "test"
    agent.action_counter = 0
    agent.actions_taken = 0
    agent.last_frame = None
    agent.last_frame_hash = None
    agent.last_state = None
    agent.last_levels = 0
    agent.total_levels_completed = 0
    agent.game_started = False
    agent.phase = "init"
    agent.changes_detected = 0
    agent.progress_events = 0
    agent.memory = module.ActionMemory()
    agent.explorer = None
    agent.planner = module.Planner()
    agent.analyzer = module.FrameAnalyzer()

    not_played_frame = MockFrameData(state=MockGameState.NOT_PLAYED)
    action = agent.choose_action([], not_played_frame)
    assert action == MockGameAction.RESET


def test_choose_action_on_game_over():
    """Verify RESET is returned when game is GAME_OVER."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    MyAgent = module.MyAgent
    agent = MyAgent.__new__(MyAgent)
    agent.game_id = "test"
    agent.action_counter = 0
    agent.actions_taken = 0
    agent.last_frame = None
    agent.last_frame_hash = None
    agent.last_state = None
    agent.last_levels = 0
    agent.total_levels_completed = 0
    agent.game_started = True
    agent.phase = "explore"
    agent.changes_detected = 0
    agent.progress_events = 0
    agent.memory = module.ActionMemory()
    agent.explorer = module.Explorer([MockGameAction.ACTION1, MockGameAction.ACTION2])
    agent.planner = module.Planner()
    agent.analyzer = module.FrameAnalyzer()

    game_over_frame = MockFrameData(state=MockGameState.GAME_OVER)
    action = agent.choose_action([], game_over_frame)
    assert action == MockGameAction.RESET


def test_frame_analyzer_diff():
    """Verify FrameAnalyzer detects differences."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    FrameAnalyzer = module.FrameAnalyzer

    frame_a = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    frame_b = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]

    diff = FrameAnalyzer.compute_frame_diff(frame_a, frame_b)
    assert diff["has_change"] == True
    assert diff["changed_pixels"] == 1


def test_frame_analyzer_no_diff():
    """Verify FrameAnalyzer detects no differences."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    FrameAnalyzer = module.FrameAnalyzer

    frame_a = [[0, 0, 0], [0, 0, 0]]
    frame_b = [[0, 0, 0], [0, 0, 0]]

    diff = FrameAnalyzer.compute_frame_diff(frame_a, frame_b)
    assert diff["has_change"] == False
    assert diff["changed_pixels"] == 0


def test_action_memory_scoring():
    """Verify ActionMemory scores actions correctly."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    memory = module.ActionMemory()

    # Unknown action should have neutral score
    score = memory.get_action_score(MockGameAction.ACTION1)
    assert score == 0.5

    # Record some transitions
    record1 = module.TransitionRecord(
        action=MockGameAction.ACTION1,
        frame_hash_before=100,
        frame_hash_after=200,
        diff={"has_change": True, "changed_pixels": 10, "regions": []},
        state_before=MockGameState.PLAYING,
        state_after=MockGameState.PLAYING,
        levels_before=0,
        levels_after=0,
    )
    memory.record_transition(record1)

    # After one change-causing action, score should be above neutral
    score = memory.get_action_score(MockGameAction.ACTION1)
    assert score > 0.0


def test_cycle_detection():
    """Verify cycle detection works."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    memory = module.ActionMemory()

    # Simulate repeating pattern
    for _ in range(4):
        memory.recent_actions.append(MockGameAction.ACTION1)
        memory.recent_actions.append(MockGameAction.ACTION2)

    assert memory.is_in_cycle() == True


def test_no_cycle():
    """Verify no false cycle detection."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    memory = module.ActionMemory()
    memory.recent_actions = [
        MockGameAction.ACTION1, MockGameAction.ACTION3,
        MockGameAction.ACTION2, MockGameAction.ACTION4,
        MockGameAction.ACTION5, MockGameAction.ACTION1,
    ]
    assert memory.is_in_cycle() == False


def test_explorer_strategies():
    """Verify Explorer cycles through strategies."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    actions = [MockGameAction.ACTION1, MockGameAction.ACTION2, MockGameAction.ACTION3]
    explorer = module.Explorer(actions)

    assert explorer.current_strategy == module.ExplorationStrategy.SYSTEMATIC

    # Systematic should cycle through actions
    memory = module.ActionMemory()
    a1 = explorer.select_exploration_action(memory)
    assert a1 == MockGameAction.ACTION1

    a2 = explorer.select_exploration_action(memory)
    assert a2 == MockGameAction.ACTION2

    a3 = explorer.select_exploration_action(memory)
    assert a3 == MockGameAction.ACTION3


def test_max_actions_limit():
    """Verify MAX_ACTIONS is set to 80."""
    spec = importlib.util.spec_from_file_location(
        "my_agent",
        os.path.join(os.path.dirname(__file__), '..', 'agent', 'my_agent.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.MyAgent.MAX_ACTIONS == 80


def test_kaggle_cell_exists():
    """Verify the Kaggle notebook cell file exists."""
    cell_path = os.path.join(os.path.dirname(__file__), '..', 'agent', 'kaggle_cell.py')
    assert os.path.exists(cell_path), f"Kaggle cell file not found at {cell_path}"


def test_kaggle_cell_has_myagent():
    """Verify the Kaggle cell contains MyAgent class."""
    cell_path = os.path.join(os.path.dirname(__file__), '..', 'agent', 'kaggle_cell.py')
    with open(cell_path, 'r') as f:
        content = f.read()
    assert 'class MyAgent' in content, "MyAgent class not found in Kaggle cell"
    assert 'def is_done' in content, "is_done method not found in Kaggle cell"
    assert 'def choose_action' in content, "choose_action method not found in Kaggle cell"


if __name__ == "__main__":
    # Run all tests
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"{failed} TESTS FAILED ✗")
        sys.exit(1)
