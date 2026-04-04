from scheduler_env import SchedulerEnv
from env_models import Action, ActionType


# Predefined action sequences for each task level.
# Each list is the exact steps the mock agent will take.
TASK_PLANS = {
    1: [
        Action(action_type=ActionType.QUERY_EMPTY_ROOMS, time_slot="10:00 AM"),
        Action(action_type=ActionType.MOVE_CLASS, class_id="CS101", room_id="102", time_slot="10:00 AM"),
        Action(action_type=ActionType.SUBMIT_TASK),
    ],
    2: [
        Action(action_type=ActionType.QUERY_SCHEDULE, professor_id="Smith"),
        Action(action_type=ActionType.CANCEL_CLASS, class_id="CS101"),
        Action(action_type=ActionType.CANCEL_CLASS, class_id="MATH201"),
        Action(action_type=ActionType.NOTIFY_STUDENTS, class_id="CS101"),
        Action(action_type=ActionType.NOTIFY_STUDENTS, class_id="MATH201"),
        Action(action_type=ActionType.SUBMIT_TASK),
    ],
    3: [
        Action(action_type=ActionType.QUERY_EMPTY_ROOMS, time_slot="2:00 PM"),
        Action(action_type=ActionType.MOVE_CLASS, class_id="PHY301", room_id="103", time_slot="3:00 PM"),
        Action(action_type=ActionType.NOTIFY_STUDENTS, class_id="PHY301"),
        Action(action_type=ActionType.SUBMIT_TASK),
    ],
}


def run_baseline():
    """Run the mock AI agent through all 3 task levels and print results."""
    env = SchedulerEnv()
    all_passed = True

    for level in [1, 2, 3]:
        print(f"\n🚀 --- Starting Task Level {level} ---")
        env.set_task(level)
        obs = env.reset()

        plan = TASK_PLANS[level]
        for step_num, action in enumerate(plan, start=1):
            print(f"  Step {step_num} | Action: {action.action_type.value}")

            obs, reward, done, _ = env.step(action)
            print(f"           -> {obs.system_message}")

            if done:
                status = "✅ PASSED" if reward.value == 1.0 else "❌ FAILED"
                print(f"{status} | Level {level} | Final Reward: {reward.value} | {reward.reason}")
                if reward.value != 1.0:
                    all_passed = False
                break

    print("\n" + ("=" * 50))
    print("🏁 Baseline Complete:", "All tasks PASSED ✅" if all_passed else "Some tasks FAILED ❌")


if __name__ == "__main__":
    run_baseline()
