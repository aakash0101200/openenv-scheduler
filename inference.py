import os
import json
from openai import OpenAI
from scheduler_env import SchedulerEnv
from env_models import Action

def run_inference():
    # 1. Mandatory Environment Variables
    api_base = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    hf_token = os.getenv("HF_TOKEN")

    if not all([api_base, model_name, hf_token]):
        print("❌ Error: Missing mandatory environment variables (API_BASE_URL, MODEL_NAME, HF_TOKEN).")
        return

    # 2. Setup OpenAI Client (Using HF endpoint)
    client = OpenAI(
        api_key=hf_token,
        base_url=api_base,
    )

    env = SchedulerEnv()

    # 3. Run all 3 tasks
    for level in [1, 2, 3]:
        env.set_task(level)
        obs = env.reset()
        
        # MANDATORY LOG: START
        print(f"[START] Task {level}")

        for step in range(1, 15):
            system_prompt = (
                "You are an AI college scheduling assistant. "
                "Respond ONLY with a valid JSON matching the Action schema."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"State: {obs.model_dump_json()}"}
            ]

            try:
                # Using the OpenAI client as required
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_format={"type": "json_object"} 
                )
                
                action_data = json.loads(response.choices[0].message.content)
                action = Action(**action_data)
            except Exception as e:
                # Fallback to prevent crash
                action = Action(action_type="submit_task")

            # MANDATORY LOG: STEP
            print(f"[STEP] Action: {action.action_type.value} | Params: {action.model_dump(exclude_none=True)}")
            
            obs, reward, done, _ = env.step(action)
            
            if done:
                # MANDATORY LOG: END
                print(f"[END] Final Score: {reward.value}")
                break

if __name__ == "__main__":
    run_inference()