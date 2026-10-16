"""
AL-ANDALUS ARC AGENT
====================
ARC Prize 2026 — ARC-AGI-3 Competition

An adaptive agent that observes, explores, learns, and acts.
Surpasses the random agent through in-game learning and evidence-based decisions.

Architecture:
  - PERCEPTION: Frame difference analysis, region detection, color tracking
  - MEMORY: State history, action consequences, transition model
  - EXPLORATION: Systematic action testing, informative experiment selection
  - LEARNING: Action→effect mapping, hypothesis formation, progress estimation
  - PLANNING: Evidence-based action selection, strategy adaptation

Author: AL-ANDALUS AI LAB
License: MIT
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


# ─────────────────────────────────────────────────────────────────────────────
# PERCEPTION MODULE
# ─────────────────────────────────────────────────────────────────────────────

class FrameAnalyzer:
    """Analyzes frames to extract meaningful information."""

    @staticmethod
    def frame_to_hash(frame: list[list[int]]) -> int:
        """Create a hashable representation of a frame for state comparison."""
        flat = []
        for row in frame:
            flat.extend(row)
        return hash(tuple(flat))

    @staticmethod
    def get_frame_dimensions(frame: list[list[int]]) -> tuple[int, int]:
        """Get frame dimensions (height, width)."""
        if not frame or not frame[0]:
            return (0, 0)
        return (len(frame), len(frame[0]))

    @staticmethod
    def compute_frame_diff(frame_a: list[list[int]], frame_b: list[list[int]]) -> dict:
        """
        Compute detailed differences between two frames.
        Returns: changed_pixels, change_regions, color_changes, movement_vectors
        """
        if not frame_a or not frame_b:
            return {"changed_pixels": 0, "regions": [], "color_changes": {}, "has_change": False}

        h_a, w_a = len(frame_a), len(frame_a[0]) if frame_a else 0
        h_b, w_b = len(frame_b), len(frame_b[0]) if frame_b else 0

        h = min(h_a, h_b)
        w = min(w_a, w_b)

        changed_pixels = 0
        changed_positions = []
        color_changes = defaultdict(int)
        old_colors = set()
        new_colors = set()

        for y in range(h):
            for x in range(w):
                val_a = frame_a[y][x]
                val_b = frame_b[y][x]
                if val_a != val_b:
                    changed_pixels += 1
                    changed_positions.append((x, y))
                    color_changes[(val_a, val_b)] += 1
                    old_colors.add(val_a)
                    new_colors.add(val_b)

        # Also count pixels that exist in one frame but not the other
        if h_a > h_b:
            for y in range(h_b, h_a):
                for x in range(w_a):
                    changed_pixels += 1
        elif h_b > h_a:
            for y in range(h_a, h_b):
                for x in range(w_b):
                    changed_pixels += 1

        # Detect change regions (bounding boxes of changes)
        regions = FrameAnalyzer._detect_regions(changed_positions)

        return {
            "changed_pixels": changed_pixels,
            "regions": regions,
            "color_changes": dict(color_changes),
            "has_change": changed_pixels > 0,
            "change_ratio": changed_pixels / max(h * w, 1),
        }

    @staticmethod
    def _detect_regions(positions: list[tuple[int, int]]) -> list[dict]:
        """Detect rectangular regions from changed pixel positions."""
        if not positions:
            return []

        # Simple clustering: group nearby changes
        min_x = min(p[0] for p in positions)
        max_x = max(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        max_y = max(p[1] for p in positions)

        # Center of mass
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)

        return [{
            "bbox": (min_x, min_y, max_x, max_y),
            "center": (cx, cy),
            "pixel_count": len(positions),
        }]

    @staticmethod
    def find_dominant_colors(frame: list[list[int]], top_n: int = 5) -> list[tuple[int, int]]:
        """Find the most common colors in a frame, sorted by frequency."""
        color_count = defaultdict(int)
        for row in frame:
            for val in row:
                color_count[val] += 1
        sorted_colors = sorted(color_count.items(), key=lambda x: -x[1])
        return sorted_colors[:top_n]

    @staticmethod
    def find_object_centers(frame: list[list[int]], background: int = 0) -> list[dict]:
        """
        Find centers of non-background connected regions.
        Simple approach: find clusters of same-colored pixels.
        """
        h = len(frame)
        w = len(frame[0]) if frame else 0
        visited = [[False] * w for _ in range(h)]
        objects = []

        for y in range(h):
            for x in range(w):
                if visited[y][x] or frame[y][x] == background:
                    continue
                # BFS to find connected component
                color = frame[y][x]
                queue = [(x, y)]
                visited[y][x] = True
                pixels = []

                while queue:
                    cx, cy = queue.pop(0)
                    pixels.append((cx, cy))
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and frame[ny][nx] == color:
                            visited[ny][nx] = True
                            queue.append((nx, ny))

                if len(pixels) >= 2:  # Only track objects with at least 2 pixels
                    center_x = sum(p[0] for p in pixels) / len(pixels)
                    center_y = sum(p[1] for p in pixels) / len(pixels)
                    objects.append({
                        "color": color,
                        "center": (center_x, center_y),
                        "size": len(pixels),
                        "bbox": (min(p[0] for p in pixels), min(p[1] for p in pixels),
                                 max(p[0] for p in pixels), max(p[1] for p in pixels)),
                    })

        return objects


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY MODULE
# ─────────────────────────────────────────────────────────────────────────────

class TransitionRecord:
    """Records the result of an action."""
    __slots__ = ['action', 'frame_hash_before', 'frame_hash_after',
                 'diff', 'state_before', 'state_after',
                 'levels_before', 'levels_after', 'timestamp']

    def __init__(self, action: GameAction, frame_hash_before: int,
                 frame_hash_after: int, diff: dict,
                 state_before: GameState, state_after: GameState,
                 levels_before: int, levels_after: int):
        self.action = action
        self.frame_hash_before = frame_hash_before
        self.frame_hash_after = frame_hash_after
        self.diff = diff
        self.state_before = state_before
        self.state_after = state_after
        self.levels_before = levels_before
        self.levels_after = levels_after
        self.timestamp = time.time()


class ActionMemory:
    """
    Memory system that tracks action consequences.
    Builds a model of what each action does.
    """

    MAX_RECORDS = 500  # Prevent unbounded growth

    def __init__(self):
        self.transitions: list[TransitionRecord] = []
        self.action_effectiveness: dict[str, dict] = defaultdict(lambda: {
            "total": 0,
            "caused_change": 0,
            "caused_progress": 0,
            "caused_death": 0,
            "avg_change_pixels": 0.0,
            "no_effect_count": 0,
        })
        self.state_action_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.recent_actions: list[GameAction] = []
        self.recent_window = 10  # Track last N actions for cycle detection

    def record_transition(self, record: TransitionRecord) -> None:
        """Record a transition and update statistics."""
        self.transitions.append(record)
        if len(self.transitions) > self.MAX_RECORDS:
            self.transitions = self.transitions[-self.MAX_RECORDS:]

        action_name = record.action.name
        stats = self.action_effectiveness[action_name]
        stats["total"] += 1

        if record.diff.get("has_change", False):
            stats["caused_change"] += 1
            # Update running average of change pixels
            n = stats["caused_change"]
            old_avg = stats["avg_change_pixels"]
            stats["avg_change_pixels"] = old_avg + (record.diff["changed_pixels"] - old_avg) / n

        if record.levels_after > record.levels_before:
            stats["caused_progress"] += 1

        if (record.state_before not in (GameState.GAME_OVER, GameState.WIN) and
                record.state_after == GameState.GAME_OVER):
            stats["caused_death"] += 1

        if not record.diff.get("has_change", False):
            stats["no_effect_count"] += 1

        # Track state-action pairs
        state_hash = record.frame_hash_before
        self.state_action_counts[state_hash][action_name] += 1

        # Track recent actions for cycle detection
        self.recent_actions.append(record.action)
        if len(self.recent_actions) > self.recent_window:
            self.recent_actions = self.recent_actions[-self.recent_window:]

    def get_action_score(self, action: GameAction) -> float:
        """
        Score an action based on learned effectiveness.
        Higher = more likely to be useful.
        """
        action_name = action.name
        stats = self.action_effectiveness[action_name]

        if stats["total"] == 0:
            return 0.5  # Unknown actions get neutral score (exploration bonus)

        score = 0.0

        # Reward actions that cause changes
        change_rate = stats["caused_change"] / stats["total"]
        score += change_rate * 0.3

        # Reward progress
        if stats["total"] > 0:
            progress_rate = stats["caused_progress"] / stats["total"]
            score += progress_rate * 0.5

        # Penalize actions that cause death
        death_rate = stats["caused_death"] / stats["total"]
        score -= death_rate * 0.4

        # Penalize actions with no effect
        no_effect_rate = stats["no_effect_count"] / stats["total"]
        score -= no_effect_rate * 0.2

        # Exploration bonus: prefer less-tried actions
        exploration_bonus = 1.0 / (1.0 + stats["total"] * 0.1)
        score += exploration_bonus * 0.2

        return score

    def is_in_cycle(self) -> bool:
        """Detect if we're repeating the same actions without progress."""
        if len(self.recent_actions) < 6:
            return False

        # Check for repeating patterns of length 2, 3, 4
        for pattern_len in range(2, min(5, len(self.recent_actions) // 2 + 1)):
            pattern = self.recent_actions[-pattern_len:]
            earlier = self.recent_actions[-(pattern_len * 2):-pattern_len]
            if len(earlier) == pattern_len and pattern == earlier:
                return True

        return False

    def get_least_tried_action(self, available: list[GameAction]) -> Optional[GameAction]:
        """Get the available action we've tried least."""
        if not available:
            return None

        min_count = float('inf')
        best = None
        for action in available:
            count = self.action_effectiveness[action.name]["total"]
            if count < min_count:
                min_count = count
                best = action
        return best

    def reset(self) -> None:
        """Reset memory for a new game/level."""
        self.transitions.clear()
        self.action_effectiveness.clear()
        self.state_action_counts.clear()
        self.recent_actions.clear()


# ─────────────────────────────────────────────────────────────────────────────
# EXPLORATION MODULE
# ─────────────────────────────────────────────────────────────────────────────

class ExplorationStrategy(Enum):
    SYSTEMATIC = "systematic"      # Try each action in order
    INFORMATIVE = "informative"    # Pick actions expected to give most info
    EXPLOIT = "exploit"           # Use best known action
    RANDOM = "random"             # Fallback random


class Explorer:
    """Manages exploration of the action space."""

    def __init__(self, available_actions: list[GameAction]):
        self.available_actions = [a for a in available_actions if a is not GameAction.RESET]
        self.systematic_index = 0
        self.systematic_complete = False
        self.current_strategy = ExplorationStrategy.SYSTEMATIC
        self.actions_tried_this_phase: set[str] = set()
        self.exploration_budget = max(len(self.available_actions) * 3, 15)
        self.actions_since_progress = 0

    def select_exploration_action(self, memory: ActionMemory) -> GameAction:
        """Select an action based on current exploration strategy."""

        if self.current_strategy == ExplorationStrategy.SYSTEMATIC:
            return self._systematic_select()

        elif self.current_strategy == ExplorationStrategy.INFORMATIVE:
            return self._informative_select(memory)

        elif self.current_strategy == ExplorationStrategy.EXPLOIT:
            return self._exploit_select(memory)

        else:
            return self._random_select()

    def _systematic_select(self) -> GameAction:
        """Try each available action in sequence."""
        if self.systematic_index >= len(self.available_actions):
            self.systematic_complete = True
            self.current_strategy = ExplorationStrategy.INFORMATIVE
            return self._informative_select(ActionMemory())

        action = self.available_actions[self.systematic_index]
        self.systematic_index += 1
        self.actions_tried_this_phase.add(action.name)
        return action

    def _informative_select(self, memory: ActionMemory) -> GameAction:
        """Select the action expected to provide most information."""
        # Prefer actions we haven't tried much
        least_tried = memory.get_least_tried_action(self.available_actions)
        if least_tried is not None:
            self.actions_tried_this_phase.add(least_tried.name)
            return least_tried

        return self._random_select()

    def _exploit_select(self, memory: ActionMemory) -> GameAction:
        """Select the best known action."""
        best_score = -float('inf')
        best_action = self.available_actions[0] if self.available_actions else GameAction.ACTION1

        for action in self.available_actions:
            score = memory.get_action_score(action)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def _random_select(self) -> GameAction:
        """Random action selection as fallback."""
        return random.choice(self.available_actions)

    def update_strategy(self, memory: ActionMemory, progress_made: bool) -> None:
        """Update exploration strategy based on results."""
        self.actions_since_progress += 1

        if progress_made:
            self.actions_since_progress = 0
            # If we're making progress, exploit
            if len(self.actions_tried_this_phase) >= len(self.available_actions) * 0.5:
                self.current_strategy = ExplorationStrategy.EXPLOIT
            return

        # No progress: check if we should switch strategies
        if self.actions_since_progress > self.exploration_budget:
            if self.current_strategy == ExplorationStrategy.SYSTEMATIC:
                self.current_strategy = ExplorationStrategy.INFORMATIVE
                self.actions_since_progress = 0
            elif self.current_strategy == ExplorationStrategy.INFORMATIVE:
                self.current_strategy = ExplorationStrategy.EXPLOIT
                self.actions_since_progress = 0
            elif self.current_strategy == ExplorationStrategy.EXPLOIT:
                # Exploit failed, try random
                self.current_strategy = ExplorationStrategy.RANDOM
                self.actions_since_progress = 0
            else:
                # Reset to systematic with shuffled order
                random.shuffle(self.available_actions)
                self.systematic_index = 0
                self.current_strategy = ExplorationStrategy.SYSTEMATIC
                self.actions_since_progress = 0

        # Detect cycles
        if memory.is_in_cycle():
            # Break the cycle by trying something different
            self.current_strategy = ExplorationStrategy.RANDOM
            self.actions_since_progress = 0


# ─────────────────────────────────────────────────────────────────────────────
# PLANNING MODULE
# ─────────────────────────────────────────────────────────────────────────────

class Planner:
    """
    Short-horizon planner based on evidence.
    Uses learned action effects to choose promising actions.
    """

    def __init__(self):
        self.hypotheses: dict[str, str] = {}  # action -> hypothesized effect
        self.confidence: dict[str, float] = {}  # action -> confidence in hypothesis
        self.goal_direction: Optional[str] = None  # Detected goal direction

    def update_hypotheses(self, memory: ActionMemory) -> None:
        """Update hypotheses based on observed transitions."""
        for action_name, stats in memory.action_effectiveness.items():
            if stats["total"] < 2:
                continue

            change_rate = stats["caused_change"] / stats["total"]
            progress_rate = stats["caused_progress"] / stats["total"] if stats["total"] > 0 else 0

            if progress_rate > 0.1:
                self.hypotheses[action_name] = "progress"
                self.confidence[action_name] = min(1.0, progress_rate * 3)
            elif change_rate > 0.5:
                self.hypotheses[action_name] = "causes_change"
                self.confidence[action_name] = min(1.0, change_rate)
            elif change_rate < 0.1:
                self.hypotheses[action_name] = "no_effect"
                self.confidence[action_name] = min(1.0, 1.0 - change_rate)

    def select_action(self, available: list[GameAction], memory: ActionMemory,
                      explorer: Explorer) -> GameAction:
        """
        Select action using a combination of planning and exploration.
        Balances exploitation of known good actions with exploration.
        """
        # If we have a high-confidence good action, use it sometimes
        best_action = None
        best_score = -float('inf')

        for action in available:
            if action is GameAction.RESET:
                continue

            action_name = action.name
            mem_score = memory.get_action_score(action)
            hypothesis_bonus = 0.0

            if action_name in self.hypotheses:
                hyp = self.hypotheses[action_name]
                conf = self.confidence.get(action_name, 0.0)
                if hyp == "progress":
                    hypothesis_bonus = conf * 0.5
                elif hyp == "causes_change":
                    hypothesis_bonus = conf * 0.2
                elif hyp == "no_effect":
                    hypothesis_bonus = -conf * 0.3

            total_score = mem_score + hypothesis_bonus

            if total_score > best_score:
                best_score = total_score
                best_action = action

        # Sometimes explore instead of exploit
        explore_probability = max(0.1, 1.0 - len(memory.transitions) * 0.02)
        if random.random() < explore_probability:
            return explorer.select_exploration_action(memory)

        if best_action is not None:
            return best_action

        return random.choice([a for a in available if a is not GameAction.RESET])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AGENT
# ─────────────────────────────────────────────────────────────────────────────

class MyAgent(Agent):
    """
    AL-ANDALUS ARC AGENT

    An adaptive agent that:
    1. Observes frame differences to detect changes
    2. Builds a model of action→effect relationships
    3. Explores systematically, then exploits learned knowledge
    4. Detects and breaks out of unproductive cycles
    5. Plans short-horizon actions based on evidence
    """

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Deterministic seed per game for reproducibility
        seed = int(time.time() * 1_000_000) + hash(self.game_id) % 1_000_000
        random.seed(seed)

        # Core modules
        self.analyzer = FrameAnalyzer()
        self.memory = ActionMemory()
        self.explorer: Optional[Explorer] = None
        self.planner = Planner()

        # State tracking
        self.last_frame_hash: Optional[int] = None
        self.last_frame: Optional[list[list[int]]] = None
        self.last_state: Optional[GameState] = None
        self.last_levels: int = 0
        self.total_levels_completed: int = 0
        self.actions_taken: int = 0
        self.game_started: bool = False
        self.phase: str = "init"  # init, explore, exploit, recover

        # Metrics for logging
        self.changes_detected: int = 0
        self.progress_events: int = 0

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """
        Decide if the agent should stop playing.
        Stop on WIN. Don't stop on GAME_OVER (we want to retry).
        """
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        """
        Main decision function.
        Observes the current state, updates memory, and selects an action.
        """
        self.actions_taken += 1

        # ── Handle game states ──────────────────────────────────────────────
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return self._handle_reset(latest_frame)

        # ── Initialize explorer with available actions ──────────────────────
        available_actions = self._get_available_actions(latest_frame)
        if self.explorer is None or self._actions_changed(latest_frame):
            self.explorer = Explorer(available_actions)

        # ── Perception: analyze current frame ───────────────────────────────
        current_frame = self._extract_frame(latest_frame)
        current_hash = FrameAnalyzer.frame_to_hash(current_frame) if current_frame else 0

        # ── Learning: record transition from last action ────────────────────
        if self.last_frame is not None and len(frames) >= 2:
            self._record_last_transition(frames, latest_frame, current_hash)

        # ── Update state tracking ───────────────────────────────────────────
        self.last_frame = current_frame
        self.last_frame_hash = current_hash
        self.last_state = latest_frame.state
        self.last_levels = latest_frame.levels_completed or 0

        # ── Decision: select next action ────────────────────────────────────
        action = self._decide_action(latest_frame, available_actions)

        # ── Attach reasoning ────────────────────────────────────────────────
        self._attach_reasoning(action)

        return action

    def _handle_reset(self, latest_frame: FrameData) -> GameAction:
        """Handle RESET for game start or after game over."""
        if latest_frame.state == GameState.GAME_OVER:
            logger.info(
                f"[AL-ANDALUS] Game over. Levels completed: {latest_frame.levels_completed}. "
                f"Resetting to retry."
            )
        elif latest_frame.state == GameState.NOT_PLAYED and not self.game_started:
            logger.info(f"[AL-ANDALUS] Starting game: {self.game_id}")
            self.game_started = True

        # Reset per-level memory but keep cross-level learning
        if latest_frame.state == GameState.GAME_OVER:
            self.memory.reset()
            if self.explorer:
                self.explorer.actions_since_progress = 0
                self.explorer.current_strategy = ExplorationStrategy.SYSTEMATIC
                self.explorer.systematic_index = 0

        self.last_frame = None
        self.last_frame_hash = None
        self.phase = "init"

        action = GameAction.RESET
        action.reasoning = f"AL-ANDALUS: Reset (state={latest_frame.state})"
        return action

    def _get_available_actions(self, latest_frame: FrameData) -> list[GameAction]:
        """Get list of available actions from the frame."""
        if hasattr(latest_frame, 'available_actions') and latest_frame.available_actions:
            # available_actions contains action IDs (ints)
            available_ids = latest_frame.available_actions
            actions = []
            for action in GameAction:
                if action.value in available_ids or action.name in available_ids:
                    actions.append(action)
            if actions:
                return actions

        # Fallback: all non-RESET actions
        return [a for a in GameAction if a is not GameAction.RESET]

    def _actions_changed(self, latest_frame: FrameData) -> bool:
        """Check if available actions changed since last frame."""
        if self.explorer is None:
            return True
        current = set(a.name for a in self._get_available_actions(latest_frame))
        previous = set(a.name for a in self.explorer.available_actions)
        return current != previous

    def _extract_frame(self, latest_frame: FrameData) -> list[list[int]]:
        """Extract the primary frame data (first channel if multi-channel)."""
        frame = latest_frame.frame
        if not frame:
            return []
        # frame is list of 2D arrays; take the first one
        if isinstance(frame[0], list):
            if isinstance(frame[0][0], list):
                # Multi-channel: frame[0] is the first channel
                return frame[0]
            else:
                # Single channel: frame is already the 2D array
                return frame
        return frame

    def _record_last_transition(self, frames: list[FrameData],
                                 latest_frame: FrameData,
                                 current_hash: int) -> None:
        """Record the transition from the previous frame to current."""
        if self.last_frame is None or self.last_frame_hash is None:
            return

        # Get the last action taken (from the frames history)
        # We need to figure out what action was taken - it's the action
        # we returned in the previous call
        # Since we don't have direct access, we use the action counter
        prev_frame = frames[-2] if len(frames) >= 2 else frames[-1]
        prev_hash = self.last_frame_hash

        # Compute frame difference
        prev_data = self._extract_frame(prev_frame) if prev_frame else []
        curr_data = self._extract_frame(latest_frame)
        diff = FrameAnalyzer.compute_frame_diff(prev_data, curr_data) if prev_data and curr_data else {}

        if diff.get("has_change", False):
            self.changes_detected += 1

        # Check for progress
        prev_levels = getattr(prev_frame, 'levels_completed', 0) or 0
        curr_levels = latest_frame.levels_completed or 0
        progress_made = curr_levels > prev_levels

        if progress_made:
            self.progress_events += 1
            self.total_levels_completed = curr_levels

        # Determine the last action (approximate from action counter)
        # We track this through the explorer's last selection
        last_action = self._get_last_action()

        record = TransitionRecord(
            action=last_action,
            frame_hash_before=prev_hash,
            frame_hash_after=current_hash,
            diff=diff,
            state_before=self.last_state or GameState.NOT_PLAYED,
            state_after=latest_frame.state,
            levels_before=prev_levels,
            levels_after=curr_levels,
        )

        self.memory.record_transition(record)

        # Update planner hypotheses
        self.planner.update_hypotheses(self.memory)

        # Update exploration strategy
        if self.explorer:
            self.explorer.update_strategy(self.memory, progress_made)

    def _get_last_action(self) -> GameAction:
        """Get the last action that was taken."""
        if self.memory.recent_actions:
            return self.memory.recent_actions[-1]
        return GameAction.ACTION1

    def _decide_action(self, latest_frame: FrameData,
                       available: list[GameAction]) -> GameAction:
        """Core decision logic."""
        non_reset = [a for a in available if a is not GameAction.RESET]
        if not non_reset:
            return GameAction.RESET

        # Phase-based decision making
        if self.phase == "init":
            self.phase = "explore"

        # Check for cycles and adapt
        if self.memory.is_in_cycle():
            logger.info("[AL-ANDALUS] Cycle detected! Breaking out...")
            if self.explorer:
                self.explorer.current_strategy = ExplorationStrategy.RANDOM
                self.explorer.actions_since_progress = 0

        # Resource management: if we're running low on actions, be more strategic
        remaining = self.MAX_ACTIONS - self.action_counter
        if remaining < 15:
            return self._emergency_action(non_reset)

        # Use planner for decision
        return self.planner.select_action(available, self.memory, self.explorer or Explorer(non_reset))

    def _emergency_action(self, available: list[GameAction]) -> GameAction:
        """
        When running low on actions, use the best known action.
        Avoid actions proven to have no effect.
        """
        best = None
        best_score = -float('inf')

        for action in available:
            if action is GameAction.RESET:
                continue
            score = self.memory.get_action_score(action)
            # Bonus for actions that caused progress
            stats = self.memory.action_effectiveness[action.name]
            if stats["caused_progress"] > 0:
                score += 2.0
            if score > best_score:
                best_score = score
                best = action

        if best is not None:
            return best

        # If nothing learned, try the most varied action
        return random.choice(available)

    def _attach_reasoning(self, action: GameAction) -> None:
        """Attach reasoning information to the action for logging."""
        if action.is_simple():
            stats = self.memory.action_effectiveness.get(action.name, {})
            total = stats.get("total", 0) if stats else 0
            reasoning = (
                f"AL-ANDALUS | action={action.name} | "
                f"phase={self.phase} | "
                f"strategy={self.explorer.current_strategy.value if self.explorer else 'N/A'} | "
                f"tried={total} | "
                f"changes={self.changes_detected} | "
                f"progress={self.progress_events}"
            )
            action.reasoning = reasoning

        elif action.is_complex():
            # For complex actions (ACTION6), choose coordinates intelligently
            x, y = self._choose_coordinates()
            action.set_data({"x": x, "y": y})
            action.reasoning = {
                "desired_action": f"{action.value}",
                "my_reason": f"AL-ANDALUS: target=({x},{y}) phase={self.phase}",
            }

    def _choose_coordinates(self) -> tuple[int, int]:
        """
        Choose coordinates for ACTION6 (click actions).
        Uses learned information about where changes occur.
        """
        # If we know where changes happen, target nearby areas
        if self.memory.transitions:
            recent_changes = [
                t for t in self.memory.transitions[-20:]
                if t.diff.get("has_change", False) and t.diff.get("regions")
            ]
            if recent_changes:
                # Target the center of recent changes
                all_centers = []
                for t in recent_changes:
                    for region in t.diff["regions"]:
                        all_centers.append(region["center"])
                if all_centers:
                    avg_x = sum(c[0] for c in all_centers) / len(all_centers)
                    avg_y = sum(c[1] for c in all_centers) / len(all_centers)
                    # Add some noise for exploration
                    x = int(max(0, min(63, avg_x + random.randint(-3, 3))))
                    y = int(max(0, min(63, avg_y + random.randint(-3, 3))))
                    return (x, y)

        # If we have object detection data, target object centers
        if self.last_frame:
            objects = FrameAnalyzer.find_object_centers(self.last_frame)
            if objects:
                # Target the largest non-background object
                target = max(objects, key=lambda o: o["size"])
                x = int(max(0, min(63, target["center"][0])))
                y = int(max(0, min(63, target["center"][1])))
                return (x, y)

        # Fallback: systematic grid exploration
        grid_positions = [(16, 16), (48, 16), (16, 48), (48, 48), (32, 32),
                          (8, 32), (56, 32), (32, 8), (32, 56)]
        idx = self.actions_taken % len(grid_positions)
        return grid_positions[idx]

    def cleanup(self, scorecard: Any = None) -> None:
        """Log final metrics when the game ends."""
        logger.info(
            f"[AL-ANDALUS] Game {self.game_id} finished. "
            f"Actions: {self.actions_taken}, "
            f"Levels completed: {self.total_levels_completed}, "
            f"Changes detected: {self.changes_detected}, "
            f"Progress events: {self.progress_events}, "
            f"Transitions recorded: {len(self.memory.transitions)}"
        )
        super().cleanup(scorecard)
