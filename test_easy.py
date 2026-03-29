from scheduler_env import SchedulerEnv
from env_models import Action, ActionType

def run_test():
    print("🎬 Starting Environment...")
    env = SchedulerEnv()
    obs = env.reset()
    
    print("\n👀 INITIAL STATE:")
    print(f"Task: {obs.active_task}")
    print(f"Message: {obs.system_message}")

    print("\n🤖 AGENT ACTION 1: Asking for empty rooms...")
    action1 = Action(action_type=ActionType.QUERY_EMPTY_ROOMS)
    obs, reward, done, _ = env.step(action1)
    
    print(f"Result: {obs.system_message}")
    print(f"Reward: {reward.value} | Is Done? {done}")

    print("\n🤖 AGENT ACTION 2: Moving CS101 to Room 102...")
    action2 = Action(
        action_type=ActionType.MOVE_CLASS, 
        class_id="CS101", 
        room_id="102"
    )
    obs, reward, done, _ = env.step(action2)
    
    print(f"Result: {obs.system_message}")
    print(f"Reward: {reward.value} | Is Done? {done}")

if __name__ == "__main__":
    run_test()