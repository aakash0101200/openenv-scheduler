from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

# --- ENUMS ---
class ActionType(str, Enum):
    QUERY_SCHEDULE = "query_schedule"
    QUERY_EMPTY_ROOMS = "query_empty_rooms"
    MOVE_CLASS = "move_class"
    CANCEL_CLASS = "cancel_class"
    NOTIFY_STUDENTS = "notify_students"
    SUBMIT_TASK = "submit_task" # Tell the environment the agent is done

# --- ACTION SPACE ---
class Action(BaseModel):
    """The action the AI agent wants to take in the system."""
    action_type: ActionType = Field(..., description="The type of action to execute.")
    
    # Optional parameters depending on the action type
    class_id: Optional[str] = Field(None, description="ID of the class to modify (e.g., 'CS101').")
    room_id: Optional[str] = Field(None, description="ID of the room to query or move to (e.g., '101').")
    time_slot: Optional[str] = Field(None, description="Time slot to query or move to (e.g., '10:00 AM').")
    professor_id: Optional[str] = Field(None, description="ID of the professor to query.")
    message: Optional[str] = Field(None, description="Content of the email to students.")

# --- OBSERVATION SPACE ---
class Observation(BaseModel):
    """What the AI agent sees after taking an action."""
    system_message: str = Field(..., description="Result of the last action (e.g., 'Class moved successfully' or 'Error: Room full').")
    active_task: str = Field(..., description="The current problem the agent needs to solve.")
    query_results: Optional[List[Dict[str, Any]]] = Field(None, description="Data returned from query actions.")
    is_done: bool = Field(..., description="Whether the task has been completed.")

# --- REWARD SPACE ---
class Reward(BaseModel):
    """The feedback signal sent back to the agent."""
    value: float = Field(..., description="Score between -1.0 and 1.0.")
    reason: str = Field(..., description="Why this score was given.")