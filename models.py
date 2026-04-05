"""
Campus Scheduler Environment — Data Models

Defines the typed contract between the AI agent and the environment.
These three classes (CampusAction, CampusObservation, CampusState) are what
the agent sees and what the environment returns — nothing else.

WHY Pydantic models?
 - Type safety: if the agent sends a wrong field name, it fails immediately
 - Auto-generates JSON schema for the /docs page on the HF Space
 - The openenv-core framework uses these to build WebSocket message formats
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from openenv.core.env_server import Action, Observation, State


# ── Action Types ────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    """All legal moves the AI agent can make in the campus environment."""
    QUERY_SCHEDULE    = "query_schedule"     # Look up a professor's classes
    QUERY_EMPTY_ROOMS = "query_empty_rooms"  # Find free rooms at a time slot
    MOVE_CLASS        = "move_class"         # Relocate a class to another room/time
    CANCEL_CLASS      = "cancel_class"       # Mark a class as cancelled
    NOTIFY_STUDENTS   = "notify_students"    # Send notification to enrolled students
    SUBMIT_TASK       = "submit_task"        # Signal task is complete (triggers grading)


# ── Action (what the agent sends TO the environment) ────────────────────────

class CampusAction(Action):
    """
    The action an AI agent wants to take in the campus scheduling system.

    Only `action_type` is required. The other fields are optional and only
    needed for certain action types:
      - query_schedule    → professor_id
      - query_empty_rooms → time_slot
      - move_class        → class_id, room_id, time_slot
      - cancel_class      → class_id
      - notify_students   → class_id
      - submit_task       → (no extra fields needed)
    """
    action_type:  ActionType    = ActionType.SUBMIT_TASK
    class_id:     Optional[str] = None   # e.g. "CS101", "MATH201"
    room_id:      Optional[str] = None   # e.g. "102", "Auditorium"
    time_slot:    Optional[str] = None   # e.g. "10:00 AM", "2:00 PM"
    professor_id: Optional[str] = None   # e.g. "Smith", "Jones"


# ── Observation (what the environment returns TO the agent) ─────────────────

class CampusObservation(Observation):
    """
    Everything the AI agent can see after taking an action.

    Inherits from openenv Observation, which already has:
      - done:   bool          — True when the agent has submitted the task
      - reward: float | None  — The partial reward from the last action

    We add:
      - system_message: human-readable result of the last action
      - active_task:    the problem description for the current task level
      - query_results:  data returned from QUERY_* actions (or None)
    """
    system_message: str                             = "System initialized."
    active_task:    str                             = ""
    query_results:  Optional[List[Dict[str, Any]]] = None


# ── State (internal bookkeeping, not shown to agent) ────────────────────────

class CampusState(State):
    """
    Internal environment state (episode metadata).

    Inherits from openenv State, which already has:
      - episode_id: Optional[str]  — unique ID for this episode
      - step_count: int            — how many steps have been taken

    We add:
      - task_level: which of the 3 tasks is currently active (1, 2, or 3)
    """
    task_level: int = 1
