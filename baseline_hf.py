import os
import json
from huggingface_hub import InferenceClient
from scheduler_env import SchedulerEnv
from env_models import Action

# Uses the token you generated earlier
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

def run_hf_agent(level):
    env = SchedulerEnv()
    env.set_task(level)
    obs = env.reset()
    
    print(f"\n🌟 --- HF AI Agent: Level {level} ---")
    
    for _ in range(10):
        prompt = f"System State: {obs.model_dump_json()}\nTask: {obs.active_task}\nRespond ONLY with a JSON Action object."
        
        # Calling a free open-source model (Mistral or Llama)
        response = client.chat_completion(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        try:
            # Basic parsing of the model's text response to JSON
            content = response.choices[0].message.content
            action_data = json.loads(content[content.find("{"):content.rfind("}")+1])
            action = Action(**action_data)
        except:
            print("⚠️ AI hallucinated. Falling back to SUBMIT_TASK.")
            action = Action(action_type="submit_task")

        print(f"🤖 AI Action: {action.action_type}")
        obs, reward, done, _ = env.step(action)
        
        if done:
            print(f"✅ Score: {reward.value}")
            break

if __name__ == "__main__":
    # Run this by setting: $env:HF_TOKEN="your_token"
    for i in [1, 2, 3]:
        run_hf_agent(i)