"""
Campus Scheduler Environment — Core Game Logic

This is the "world" the AI lives in. The three abstract methods that
openenv-core requires us to implement are:

    reset()  → reinitialize the campus and return the first observation
    step()   → execute one agent action and return the next observation
    state    → property returning internal episode metadata

HOW IT WORKS:
    The AI agent receives an observation (what it can see), picks an action,
    and receives a new observation + a reward signal. It keeps doing this
    until it calls SUBMIT_TASK (which triggers grading) or reaches max steps.

    Tasks get harder:
    Level 1 (Easy):   One room breaks → move one class
    Level 2 (Medium): Professor sick  → cancel multiple classes + notify students
    Level 3 (Hard):   Cascading conflict → move class + resolve conflict + notify
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from openenv.core.env_server import Environment

import random

# We import from models.py at the same level (root of the project)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ActionType,
    CampusAction,
    CampusObservation,
    CampusState,
)


# ── Task Definitions ─────────────────────────────────────────────────────────

TASKS = {
    1: (
        "Task 1 (Easy): Room 101 is under maintenance. "
        "Move CS101 to a free room at 10:00 AM. Then call SUBMIT_TASK."
    ),
    2: (
        "Task 2 (Medium): Prof. Smith has a family emergency. "
        "Cancel ALL of Prof. Smith's classes (CS101 and MATH201) "
        "and notify the students for each. Then call SUBMIT_TASK."
    ),
    3: (
        "Task 3 (Hard): The Auditorium has a double-booking conflict. "
        "Move PHY301 to a free room at a NEW time slot (not 2:00 PM). "
        "Notify the affected students. Then call SUBMIT_TASK."
    ),
}


# ── The Environment ──────────────────────────────────────────────────────────

class CampusEnvironment(Environment):
    """
    A simulated university scheduling system.

    The AI agent acts as an emergency registrar that must resolve
    scheduling conflicts using the available action types.
    """

    # Allows multiple agents to connect to the same server simultaneously.
    # The openenv framework creates one instance per session when True.
    SUPPORTS_CONCURRENT_SESSIONS = True

    # ── Initialization ────────────────────────────────────────────────────

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._state = CampusState()
        self._task_level = 1
        self._init_db()

    def _init_db(self):
        """Reset the campus database to its clean starting state."""
        # room_id → list of time slots that are currently booked
        self._rooms: dict = {
            "101":        ["10:00 AM"],   # CS101 is here (broken room)
            "102":        ["11:00 AM"],   # MATH201 is here
            "103":        [],             # empty
            "Auditorium": ["2:00 PM"],    # PHY301 is here
        }

        # class_id → {prof, room, time, status, enrolled}
        self._classes: dict = {
            "CS101":   {"prof": "Smith", "room": "101",        "time": "10:00 AM", "status": "active"},
            "MATH201": {"prof": "Smith", "room": "102",        "time": "11:00 AM", "status": "active"},
            "PHY301":  {"prof": "Jones", "room": "Auditorium", "time": "2:00 PM",  "status": "active"},
        }

        # Set of class_ids whose students have been notified
        self._notifications: set = set()

        self._is_done = False
        self._last_reward: float = 0.0
        self._system_message = "Campus system ready."

    # ── OpenEnv Required Methods ──────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_level: Optional[int] = None,   # default task level
        **kwargs: Any,
    ) -> CampusObservation:
        """
        Reinitialize the campus database and start a new episode.
        
        Args:
            task_level: 1 = Easy, 2 = Medium, 3 = Hard. Defaults to randomly selected if None.
        """
        # The OpenEnv Web UI passes the selected task from openenv.yaml under the "config" key
        config = kwargs.get("config", {})
        if isinstance(config, dict):
            if "task_level" in config:
                task_level = config["task_level"]
            elif "name" in config:
                name = str(config["name"]).lower()
                if "medium" in name:
                    task_level = 2
                elif "hard" in name:
                    task_level = 3
                elif "easy" in name:
                    task_level = 1
                    
        # If no explicit task was requested, pick a random task
        if task_level is None:
            task_level = random.randint(1, 3)
            
        self._init_db()
        self._task_level = max(1, min(3, int(task_level)))  # clamp to 1–3
        self._state = CampusState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_level=self._task_level,
        )
        self._system_message = f"New episode started. {TASKS[self._task_level]}"
        return self._make_obs()

    def step(
        self,
        action: CampusAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> CampusObservation:
        """
        Execute one agent action and return the resulting observation.

        Every action earns a small partial reward. The big reward comes
        from submitting a correct solution via SUBMIT_TASK.
        """
        self._state.step_count += 1
        reward = 0.0
        query_results = None

        atype = action.action_type

        # ── QUERY_SCHEDULE ─────────────────────────────────────────────
        if atype == ActionType.QUERY_SCHEDULE:
            prof = action.professor_id or ""
            results = [
                {"class": cid, **cdata}
                for cid, cdata in self._classes.items()
                if cdata["prof"] == prof
            ]
            query_results = results
            self._system_message = (
                f"Schedule for Prof. {prof}: "
                f"{[r['class'] for r in results]} — "
                f"{len(results)} class(es) found."
            )
            reward = 0.1  # reward info-gathering

        # ── QUERY_EMPTY_ROOMS ──────────────────────────────────────────
        elif atype == ActionType.QUERY_EMPTY_ROOMS:
            slot = action.time_slot or ""
            empty = [r for r, slots in self._rooms.items() if slot not in slots]
            query_results = [{"room": r} for r in empty]
            self._system_message = (
                f"Empty rooms at {slot}: {empty}"
            )
            reward = 0.1  # reward info-gathering

        # ── MOVE_CLASS ─────────────────────────────────────────────────
        elif atype == ActionType.MOVE_CLASS:
            cid  = action.class_id or ""
            rid  = action.room_id or ""
            slot = action.time_slot or ""

            if cid not in self._classes:
                self._system_message = f"Error: Class '{cid}' does not exist."
                reward = -0.2
            elif rid not in self._rooms:
                self._system_message = f"Error: Room '{rid}' does not exist."
                reward = -0.2
            elif slot in self._rooms[rid]:
                # Double-booking — hard penalty
                self._system_message = (
                    f"Failed: Room {rid} is already booked at {slot}. "
                    "Choose a different room or time."
                )
                reward = -0.5
            else:
                # Success — free old slot, claim new one
                old_room = self._classes[cid]["room"]
                old_time = self._classes[cid]["time"]
                if old_time in self._rooms.get(old_room, []):
                    self._rooms[old_room].remove(old_time)
                self._rooms[rid].append(slot)
                self._classes[cid].update({"room": rid, "time": slot})
                self._system_message = (
                    f"Success: {cid} moved to Room {rid} at {slot}."
                )
                reward = 0.4

        # ── CANCEL_CLASS ───────────────────────────────────────────────
        elif atype == ActionType.CANCEL_CLASS:
            cid = action.class_id or ""
            if cid not in self._classes:
                self._system_message = f"Error: Class '{cid}' does not exist."
                reward = -0.2
            elif self._classes[cid]["status"] == "cancelled":
                self._system_message = f"Note: {cid} was already cancelled."
                reward = 0.0
            else:
                self._classes[cid]["status"] = "cancelled"
                self._system_message = f"Success: {cid} has been cancelled."
                reward = 0.2

        # ── NOTIFY_STUDENTS ────────────────────────────────────────────
        elif atype == ActionType.NOTIFY_STUDENTS:
            cid = action.class_id or ""
            if cid not in self._classes:
                self._system_message = f"Error: Class '{cid}' does not exist."
                reward = -0.1
            elif cid in self._notifications:
                self._system_message = f"Note: Students of {cid} were already notified."
                reward = 0.0
            else:
                self._notifications.add(cid)
                self._system_message = (
                    f"Success: Students enrolled in {cid} have been notified."
                )
                reward = 0.15

        # ── SUBMIT_TASK ────────────────────────────────────────────────
        elif atype == ActionType.SUBMIT_TASK:
            self._is_done = True
            success, detail = self._grade_task()
            reward = 1.0 if success else -0.2
            self._system_message = (
                f"Task submitted. {'✓ PASSED' if success else '✗ FAILED'}: {detail}"
            )

        # ── UNKNOWN ACTION ─────────────────────────────────────────────
        else:
            self._system_message = f"Unknown action type: {atype}"
            reward = -0.1

        self._last_reward = reward
        obs = self._make_obs(reward=reward, query_results=query_results)
        return obs

    @property
    def state(self) -> CampusState:
        """Return current episode metadata (step count, task level, etc.)."""
        return self._state

    # ── Grading Logic ─────────────────────────────────────────────────────

    def _grade_task(self) -> tuple[bool, str]:
        """
        Check whether the agent solved the current task correctly.

        Returns:
            (success: bool, explanation: str)
        """
        lvl = self._task_level

        if lvl == 1:
            # CS101 must no longer be in Room 101 (and still active)
            c = self._classes["CS101"]
            if c["room"] != "101" and c["status"] == "active":
                return True, "CS101 successfully relocated from Room 101."
            return False, (
                "CS101 is still in Room 101." if c["room"] == "101"
                else "CS101 was cancelled instead of moved."
            )

        elif lvl == 2:
            # Both of Smith's classes cancelled AND at least CS101 students notified
            cs101_cancelled   = self._classes["CS101"]["status"]   == "cancelled"
            math201_cancelled = self._classes["MATH201"]["status"] == "cancelled"
            notified          = "CS101" in self._notifications

            if cs101_cancelled and math201_cancelled and notified:
                return True, "All of Prof. Smith's classes cancelled and students notified."
            parts = []
            if not cs101_cancelled:   parts.append("CS101 not cancelled")
            if not math201_cancelled: parts.append("MATH201 not cancelled")
            if not notified:          parts.append("students not notified")
            return False, "; ".join(parts)

        elif lvl == 3:
            # PHY301 must be in a different room AND at a different time AND students notified
            c     = self._classes["PHY301"]
            moved = c["room"] != "Auditorium"
            new_time = c["time"] != "2:00 PM"
            notified = "PHY301" in self._notifications

            if moved and notified:
                return True, "PHY301 rescheduled and students notified."
            parts = []
            if not moved:    parts.append("PHY301 still in Auditorium")
            if not notified: parts.append("students not notified")
            return False, "; ".join(parts)

        return False, "Unknown task level."

    # ── Helper ────────────────────────────────────────────────────────────

    def _make_obs(
        self,
        reward: Optional[float] = None,
        query_results=None,
    ) -> CampusObservation:
        return CampusObservation(
            done=self._is_done,
            reward=reward,
            system_message=self._system_message,
            active_task=TASKS[self._task_level],
            query_results=query_results,
        )
