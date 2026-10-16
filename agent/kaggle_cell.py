"""
AL-ANDALUS ARC AGENT — Kaggle Notebook Cell
============================================
Copy this entire cell into your Kaggle notebook.
It writes the agent file and is self-contained.

Usage in Kaggle notebook:
    %%writefile /tmp/my_agent.py
    [paste this entire file content]
"""

# %%writefile /tmp/my_agent.py
"""
AL-ANDALUS ARC AGENT — ARC Prize 2026 / ARC-AGI-3
Adaptive agent: observes, explores, learns, acts.
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
    def compute_frame_diff(frame_a: list[list[int]], frame_b: list[list[int]]) -> dict:
        if not frame_a or not frame_b:
            return {"changed_pixels": 0, "regions": [], "has_change": False}
        h = min(len(frame_a), len(frame_b))
        w = min(len(frame_a[0]) if frame_a else 0, len(frame_b[0]) if frame_b else 0)
        changed_pixels = 0
        changed_positions = []
        for y in range(h):
            for x in range(w):
                if frame_a[y][x] != frame_b[y][x]:
                    changed_pixels += 1
                    changed_positions.append((x, y))
        regions = []
        if changed_positions:
            min_x = min(p[0] for p in changed_positions)
            max_x = max(p[0] for p in changed_positions)
            min_y = min(p[1] for p in changed_positions)
            max_y = max(p[1] for p in changed_positions)
            cx = sum(p[0] for p in changed_positions) / len(changed_positions)
            cy = sum(p[1] for p in changed_positions) / len(changed_positions)
            regions = [{"bbox": (min_x, min_y, max_x, max_y), "center": (cx, cy), "pixel_count": len(changed_positions)}]
        return {"changed_pixels": changed_pixels, "regions": regions, "has_change": changed_pixels > 0, "change_ratio": changed_pixels / max(h * w, 1)}

    @staticmethod
    def find_object_centers(frame: list[list[int]], background: int = 0) -> list[dict]:
        h = len(frame)
        w = len(frame[0]) if frame else 0
        visited = [[False] * w for _ in range(h)]
        objects = []
        for y in range(h):
            for x in range(w):
                if visited[y][x] or frame[y][x] == background:
                    continue
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
                if len(pixels) >= 2:
                    center_x = sum(p[0] for p in pixels) / len(pixels)
                    center_y = sum(p[1] for p in pixels) / len(pixels)
                    objects.append({"color": color, "center": (center_x, center_y), "size": len(pixels)})
        return objects


class TransitionRecord:
    __slots__ = ['action', 'frame_hash_before', 'frame_hash_after', 'diff', 'state_before', 'state_after', 'levels_before', 'levels_after']

    def __init__(self, action, frame_hash_before, frame_hash_after, diff, state_before, state_after, levels_before, levels_after):
        self.action = action
        self.frame_hash_before = frame_hash_before
        self.frame_hash_after = frame_hash_after
        self.diff = diff
        self.state_before = state_before
        self.state_after = state_after
        self.levels_before = levels_before
        self.levels_after = levels_after


class ActionMemory:
    MAX_RECORDS = 500

    def __init__(self):
        self.transitions = []
        self.action_effectiveness = defaultdict(lambda: {"total": 0, "caused_change": 0, "caused_progress": 0, "caused_death": 0, "avg_change_pixels": 0.0, "no_effect_count": 0})
        self.recent_actions = []
        self.recent_window = 10

    def record_transition(self, record):
        self.transitions.append(record)
        if len(self.transitions) > self.MAX_RECORDS:
            self.transitions = self.transitions[-self.MAX_RECORDS:]
        stats = self.action_effectiveness[record.action.name]
        stats["total"] += 1
        if record.diff.get("has_change", False):
            stats["caused_change"] += 1
            n = stats["caused_change"]
            old_avg = stats["avg_change_pixels"]
            stats["avg_change_pixels"] = old_avg + (record.diff["changed_pixels"] - old_avg) / n
        if record.levels_after > record.levels_before:
            stats["caused_progress"] += 1
        if record.state_before not in (GameState.GAME_OVER, GameState.WIN) and record.state_after == GameState.GAME_OVER:
            stats["caused_death"] += 1
        if not record.diff.get("has_change", False):
            stats["no_effect_count"] += 1
        self.recent_actions.append(record.action)
        if len(self.recent_actions) > self.recent_window:
            self.recent_actions = self.recent_actions[-self.recent_window:]

    def get_action_score(self, action):
        stats = self.action_effectiveness[action.name]
        if stats["total"] == 0:
            return 0.5
        score = 0.0
        change_rate = stats["caused_change"] / stats["total"]
        score += change_rate * 0.3
        progress_rate = stats["caused_progress"] / stats["total"]
        score += progress_rate * 0.5
        death_rate = stats["caused_death"] / stats["total"]
        score -= death_rate * 0.4
        no_effect_rate = stats["no_effect_count"] / stats["total"]
        score -= no_effect_rate * 0.2
        exploration_bonus = 1.0 / (1.0 + stats["total"] * 0.1)
        score += exploration_bonus * 0.2
        return score

    def is_in_cycle(self):
        if len(self.recent_actions) < 6:
            return False
        for pattern_len in range(2, min(5, len(self.recent_actions) // 2 + 1)):
            pattern = self.recent_actions[-pattern_len:]
            earlier = self.recent_actions[-(pattern_len * 2):-pattern_len]
            if len(earlier) == pattern_len and pattern == earlier:
                return True
        return False

    def get_least_tried_action(self, available):
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

    def reset(self):
        self.transitions.clear()
        self.action_effectiveness.clear()
        self.recent_actions.clear()


class ExplorationStrategy(Enum):
    SYSTEMATIC = "systematic"
    INFORMATIVE = "informative"
    EXPLOIT = "exploit"
    RANDOM = "random"


class Explorer:
    def __init__(self, available_actions):
        self.available_actions = [a for a in available_actions if a is not GameAction.RESET]
        self.systematic_index = 0
        self.current_strategy = ExplorationStrategy.SYSTEMATIC
        self.actions_since_progress = 0
        self.exploration_budget = max(len(self.available_actions) * 3, 15)

    def select_exploration_action(self, memory):
        if self.current_strategy == ExplorationStrategy.SYSTEMATIC:
            if self.systematic_index < len(self.available_actions):
                action = self.available_actions[self.systematic_index]
                self.systematic_index += 1
                return action
            self.current_strategy = ExplorationStrategy.INFORMATIVE
        if self.current_strategy == ExplorationStrategy.INFORMATIVE:
            least_tried = memory.get_least_tried_action(self.available_actions)
            if least_tried:
                return least_tried
        if self.current_strategy == ExplorationStrategy.EXPLOIT:
            best_score = -float('inf')
            best_action = self.available_actions[0] if self.available_actions else GameAction.ACTION1
            for action in self.available_actions:
                score = memory.get_action_score(action)
                if score > best_score:
                    best_score = score
                    best_action = action
            return best_action
        return random.choice(self.available_actions) if self.available_actions else GameAction.ACTION1

    def update_strategy(self, memory, progress_made):
        self.actions_since_progress += 1
        if progress_made:
            self.actions_since_progress = 0
            return
        if self.actions_since_progress > self.exploration_budget:
            if self.current_strategy == ExplorationStrategy.SYSTEMATIC:
                self.current_strategy = ExplorationStrategy.INFORMATIVE
            elif self.current_strategy == ExplorationStrategy.INFORMATIVE:
                self.current_strategy = ExplorationStrategy.EXPLOIT
            elif self.current_strategy == ExplorationStrategy.EXPLOIT:
                self.current_strategy = ExplorationStrategy.RANDOM
            else:
                random.shuffle(self.available_actions)
                self.systematic_index = 0
                self.current_strategy = ExplorationStrategy.SYSTEMATIC
            self.actions_since_progress = 0
        if memory.is_in_cycle():
            self.current_strategy = ExplorationStrategy.RANDOM
            self.actions_since_progress = 0


class Planner:
    def __init__(self):
        self.hypotheses = {}
        self.confidence = {}

    def update_hypotheses(self, memory):
        for action_name, stats in memory.action_effectiveness.items():
            if stats["total"] < 2:
                continue
            change_rate = stats["caused_change"] / stats["total"]
            progress_rate = stats.get("caused_progress", 0) / stats["total"]
            if progress_rate > 0.1:
                self.hypotheses[action_name] = "progress"
                self.confidence[action_name] = min(1.0, progress_rate * 3)
            elif change_rate > 0.5:
                self.hypotheses[action_name] = "causes_change"
                self.confidence[action_name] = min(1.0, change_rate)
            elif change_rate < 0.1:
                self.hypotheses[action_name] = "no_effect"
                self.confidence[action_name] = min(1.0, 1.0 - change_rate)

    def select_action(self, available, memory, explorer):
        best_action = None
        best_score = -float('inf')
        for action in available:
            if action is GameAction.RESET:
                continue
            mem_score = memory.get_action_score(action)
            hyp_bonus = 0.0
            if action.name in self.hypotheses:
                hyp = self.hypotheses[action.name]
                conf = self.confidence.get(action.name, 0.0)
                if hyp == "progress":
                    hyp_bonus = conf * 0.5
                elif hyp == "causes_change":
                    hyp_bonus = conf * 0.2
                elif hyp == "no_effect":
                    hyp_bonus = -conf * 0.3
            total_score = mem_score + hyp_bonus
            if total_score > best_score:
                best_score = total_score
                best_action = action
        explore_prob = max(0.1, 1.0 - len(memory.transitions) * 0.02)
        if random.random() < explore_prob:
            return explorer.select_exploration_action(memory)
        if best_action:
            return best_action
        non_reset = [a for a in available if a is not GameAction.RESET]
        return random.choice(non_reset) if non_reset else GameAction.RESET


class MyAgent(Agent):
    """AL-ANDALUS ARC AGENT: Adaptive observe-explore-learn-act agent."""

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        seed = int(time.time() * 1_000_000) + hash(self.game_id) % 1_000_000
        random.seed(seed)
        self.analyzer = FrameAnalyzer()
        self.memory = ActionMemory()
        self.explorer = None
        self.planner = Planner()
        self.last_frame_hash = None
        self.last_frame = None
        self.last_state = None
        self.last_levels = 0
        self.total_levels_completed = 0
        self.actions_taken = 0
        self.game_started = False
        self.phase = "init"
        self.changes_detected = 0
        self.progress_events = 0

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        self.actions_taken += 1

        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return self._handle_reset(latest_frame)

        available_actions = self._get_available_actions(latest_frame)
        if self.explorer is None:
            self.explorer = Explorer(available_actions)

        current_frame = self._extract_frame(latest_frame)
        current_hash = FrameAnalyzer.frame_to_hash(current_frame) if current_frame else 0

        if self.last_frame is not None and len(frames) >= 2:
            self._record_transition(frames, latest_frame, current_hash)

        self.last_frame = current_frame
        self.last_frame_hash = current_hash
        self.last_state = latest_frame.state
        self.last_levels = latest_frame.levels_completed or 0

        action = self._decide_action(available_actions)
        self._attach_reasoning(action)
        return action

    def _handle_reset(self, latest_frame):
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

    def _get_available_actions(self, latest_frame):
        if hasattr(latest_frame, 'available_actions') and latest_frame.available_actions:
            available_ids = latest_frame.available_actions
            actions = []
            for action in GameAction:
                if action.value in available_ids or action.name in available_ids:
                    actions.append(action)
            if actions:
                return actions
        return [a for a in GameAction if a is not GameAction.RESET]

    def _extract_frame(self, latest_frame):
        frame = latest_frame.frame
        if not frame:
            return []
        if isinstance(frame[0], list) and isinstance(frame[0][0], list):
            return frame[0]
        return frame

    def _record_transition(self, frames, latest_frame, current_hash):
        if self.last_frame is None or self.last_frame_hash is None:
            return
        prev_frame = frames[-2] if len(frames) >= 2 else frames[-1]
        prev_data = self._extract_frame(prev_frame) if prev_frame else []
        curr_data = self._extract_frame(latest_frame)
        diff = FrameAnalyzer.compute_frame_diff(prev_data, curr_data) if prev_data and curr_data else {}
        if diff.get("has_change", False):
            self.changes_detected += 1
        prev_levels = getattr(prev_frame, 'levels_completed', 0) or 0
        curr_levels = latest_frame.levels_completed or 0
        progress_made = curr_levels > prev_levels
        if progress_made:
            self.progress_events += 1
            self.total_levels_completed = curr_levels
        last_action = self.memory.recent_actions[-1] if self.memory.recent_actions else GameAction.ACTION1
        record = TransitionRecord(
            action=last_action, frame_hash_before=self.last_frame_hash,
            frame_hash_after=current_hash, diff=diff,
            state_before=self.last_state or GameState.NOT_PLAYED,
            state_after=latest_frame.state,
            levels_before=prev_levels, levels_after=curr_levels,
        )
        self.memory.record_transition(record)
        self.planner.update_hypotheses(self.memory)
        if self.explorer:
            self.explorer.update_strategy(self.memory, progress_made)

    def _decide_action(self, available):
        non_reset = [a for a in available if a is not GameAction.RESET]
        if not non_reset:
            return GameAction.RESET
        if self.phase == "init":
            self.phase = "explore"
        if self.memory.is_in_cycle():
            if self.explorer:
                self.explorer.current_strategy = ExplorationStrategy.RANDOM
                self.explorer.actions_since_progress = 0
        remaining = self.MAX_ACTIONS - self.action_counter
        if remaining < 15:
            return self._emergency_action(non_reset)
        return self.planner.select_action(available, self.memory, self.explorer or Explorer(non_reset))

    def _emergency_action(self, available):
        best = None
        best_score = -float('inf')
        for action in available:
            if action is GameAction.RESET:
                continue
            score = self.memory.get_action_score(action)
            stats = self.memory.action_effectiveness[action.name]
            if stats["caused_progress"] > 0:
                score += 2.0
            if score > best_score:
                best_score = score
                best = action
        return best if best else random.choice(available)

    def _attach_reasoning(self, action):
        if action.is_simple():
            stats = self.memory.action_effectiveness.get(action.name, {})
            total = stats.get("total", 0) if stats else 0
            action.reasoning = f"AL-ANDALUS | {action.name} | phase={self.phase} | tried={total} | changes={self.changes_detected} | progress={self.progress_events}"
        elif action.is_complex():
            x, y = self._choose_coordinates()
            action.set_data({"x": x, "y": y})
            action.reasoning = {"desired_action": f"{action.value}", "my_reason": f"AL-ANDALUS: target=({x},{y})"}

    def _choose_coordinates(self):
        if self.memory.transitions:
            recent_changes = [t for t in self.memory.transitions[-20:] if t.diff.get("has_change", False) and t.diff.get("regions")]
            if recent_changes:
                all_centers = []
                for t in recent_changes:
                    for region in t.diff["regions"]:
                        all_centers.append(region["center"])
                if all_centers:
                    avg_x = sum(c[0] for c in all_centers) / len(all_centers)
                    avg_y = sum(c[1] for c in all_centers) / len(all_centers)
                    x = int(max(0, min(63, avg_x + random.randint(-3, 3))))
                    y = int(max(0, min(63, avg_y + random.randint(-3, 3))))
                    return (x, y)
        if self.last_frame:
            objects = FrameAnalyzer.find_object_centers(self.last_frame)
            if objects:
                target = max(objects, key=lambda o: o["size"])
                x = int(max(0, min(63, target["center"][0])))
                y = int(max(0, min(63, target["center"][1])))
                return (x, y)
        grid = [(16, 16), (48, 16), (16, 48), (48, 48), (32, 32), (8, 32), (56, 32), (32, 8), (32, 56)]
        idx = self.actions_taken % len(grid)
        return grid[idx]
