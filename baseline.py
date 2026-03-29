from scheduler_env import SchedulerEnv
from env_models import Action, ActionType

def mock_ai_logic(obs, task_level):
    """
    Simulates the decision-making of an AI agent.
    It reads the 'system_message' and chooses the next logical Action.
    """
    msg = obs.system_message.lower()
    
    # Task 1: Room Reallocation (Easy)
    if task_level == 1:
        if "empty rooms" not in msg:
            return Action(action_type=ActionType.QUERY_EMPTY_ROOMS, time_slot="10:00 AM")
        if "empty rooms" in msg and "moved" not in msg:
            return Action(action_type=ActionType.MOVE_CLASS, class_id="CS101", room_id="102", time_slot="10:00 AM")
        return Action(action_type=ActionType.SUBMIT_TASK)
        
    # Task 2: Professor Sick Leave (Medium)
    elif task_level == 2:
        if "schedule for" not in msg and "cancelled" not in msg:
            return Action(action_type=ActionType.QUERY_SCHEDULE, professor_id="Smith")
        if "schedule for" in msg and "cs101" in msg and "cancelled" not in msg:
            return Action(action_type=ActionType.CANCEL_CLASS, class_id="CS101")
        if "cancelled cs101" in msg and "math201" not in msg:
            return Action(action_type=ActionType.CANCEL_CLASS, class_id="MATH201")
        if "cancelled" in msg and "notified" not in msg:
            return Action(action_type=ActionType.NOTIFY_STUDENTS, class_id="CS101")
        return Action(action_type=ActionType.SUBMIT_TASK)

    # Task 3: Cascading Conflict (Hard)
    elif task_level == 3:
        if "empty rooms" not in msg:
            return Action(action_type=ActionType.QUERY_EMPTY_ROOMS, time_slot="2:00 PM")
        if "empty rooms" in msg and "moved" not in msg:
            return Action(action_type=ActionType.MOVE_CLASS, class_id="PHY301", room_id="103", time_slot="2:00 PM")
        if "moved" in msg and "notified" not in msg:
            return Action(action_type=ActionType.NOTIFY_STUDENTS, class_id="PHY301")
        return Action(action_type=ActionType.SUBMIT_TASK)

    return Action(action_type=ActionType.SUBMIT_TASK)

def run_baseline():
    env = SchedulerEnv()
    for level in [1, 2, 3]:
        print(f"\n🚀 --- Starting Task Level {level} ---")
        env.set_task(level)
        obs = env.reset()
        
        # Max 10 steps per task
        for step_num in range(1, 11):
            action = mock_ai_logic(obs, level)
            print(f"Step {step_num} | Action: {action.action_type.value}")
            
            obs, reward, done, _ = env.step(action)
            print(f"       -> Message: {obs.system_message}")
            
            if done:
                print(f"✅ Level {level} Complete! Final Reward: {reward.value}")
                break

if __name__ == "__main__":
    run_baseline()