import openenv
from typing import Tuple, Any
from env_models import Action, Observation, Reward, ActionType

class SchedulerEnv:
    def __init__(self):
        # Unified Mock Database
        self.rooms = {
            "101": ["10:00 AM"], "102": [], "103": [], "Auditorium": ["2:00 PM"]
        }
        self.classes = {
            "CS101": {"prof": "Smith", "room": "101", "time": "10:00 AM", "status": "active"},
            "MATH201": {"prof": "Smith", "room": "102", "time": "11:00 AM", "status": "active"},
            "PHY301": {"prof": "Jones", "room": "Auditorium", "time": "2:00 PM", "status": "active"}
        }
        self.notifications = []
        self.task_level = 1
        self.is_done = False
        self.system_message = "System initialized."
        self.set_task(1)

    def set_task(self, level: int):
        self.task_level = level
        self.is_done = False
        self.notifications.clear()
        if level == 1:
            self.active_task = "Task 1 (Easy): Room 101 broken. Move CS101 to empty room at 10:00 AM. Then SUBMIT_TASK."
        elif level == 2:
            self.active_task = "Task 2 (Medium): Prof. Smith is sick. Cancel all their classes, notify students, then SUBMIT_TASK."
        elif level == 3:
            self.active_task = "Task 3 (Hard): Auditorium booked. Move PHY301 to empty room/time, notify students, then SUBMIT_TASK."
        self.system_message = f"Started {self.active_task}"

    def _init_db(self):
        """Reset only the campus database to its original state."""
        self.rooms = {
            "101": ["10:00 AM"], "102": [], "103": [], "Auditorium": ["2:00 PM"]
        }
        self.classes = {
            "CS101": {"prof": "Smith", "room": "101", "time": "10:00 AM", "status": "active"},
            "MATH201": {"prof": "Smith", "room": "102", "time": "11:00 AM", "status": "active"},
            "PHY301": {"prof": "Jones", "room": "Auditorium", "time": "2:00 PM", "status": "active"}
        }
        self.notifications = []
        self.is_done = False

    def reset(self) -> Observation:
        """Reset the environment database, then re-apply the current task."""
        self._init_db()
        self.set_task(self.task_level)
        return self.state()

    def state(self) -> Observation:
        return Observation(
            system_message=self.system_message, active_task=self.active_task,
            query_results=None, is_done=self.is_done
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, dict[str, Any]]:
        reward_val, reason = 0.0, "Action processed."

        if action.action_type == ActionType.QUERY_SCHEDULE:
            res = [{"class": k, **v} for k, v in self.classes.items() if v["prof"] == action.professor_id]
            self.system_message = f"Schedule for {action.professor_id}: {res}"
            reward_val, reason = 0.2, "Queried schedule."

        elif action.action_type == ActionType.QUERY_EMPTY_ROOMS:
            empty = [r for r, slots in self.rooms.items() if action.time_slot not in slots]
            self.system_message = f"Empty rooms at {action.time_slot}: {empty}"
            reward_val, reason = 0.2, "Queried empty rooms."

        elif action.action_type == ActionType.MOVE_CLASS:
            if action.room_id in self.rooms and action.class_id in self.classes and action.time_slot not in self.rooms[action.room_id]:
                old_room = self.classes[action.class_id]["room"]
                old_time = self.classes[action.class_id]["time"]
                # Free the old slot and claim the new one
                if old_time in self.rooms.get(old_room, []):
                    self.rooms[old_room].remove(old_time)
                self.rooms[action.room_id].append(action.time_slot)
                self.classes[action.class_id].update({"room": action.room_id, "time": action.time_slot})
                self.system_message = f"Moved {action.class_id} to {action.room_id} at {action.time_slot}."
                reward_val, reason = 0.5, "Successfully moved class."
            else:
                self.system_message = "Failed: Room occupied or invalid."
                reward_val, reason = -1.0, "Double-booking penalty."

        elif action.action_type == ActionType.CANCEL_CLASS:
            if action.class_id in self.classes:
                self.classes[action.class_id]["status"] = "cancelled"
                self.system_message = f"Cancelled {action.class_id}."
                reward_val, reason = 0.3, "Class cancelled."

        elif action.action_type == ActionType.NOTIFY_STUDENTS:
            self.notifications.append(action.class_id)
            self.system_message = f"Notified students of {action.class_id}."
            reward_val, reason = 0.2, "Students notified."

        elif action.action_type == ActionType.SUBMIT_TASK:
            self.is_done = True
            success = False
            if self.task_level == 1:
                success = self.classes["CS101"]["room"] != "101"
            elif self.task_level == 2:
                success = (
                    self.classes["CS101"]["status"] == "cancelled"
                    and self.classes["MATH201"]["status"] == "cancelled"
                    and "CS101" in self.notifications
                )
            elif self.task_level == 3:
                success = (
                    self.classes["PHY301"]["room"] != "Auditorium"
                    and "PHY301" in self.notifications
                )
            reward_val = 1.0 if success else 0.0
            reason = "Final Grade Applied."

        return self.state(), Reward(value=reward_val, reason=reason), self.is_done, {}