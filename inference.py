"""
inference.py — Campus Scheduler AI Agent

MANDATORY REQUIREMENTS (from hackathon brief):
  - Must be named inference.py and placed in the ROOT directory
  - Must use openai.OpenAI client with API_BASE_URL, MODEL_NAME, HF_TOKEN env vars
  - Must emit EXACTLY: [START], [STEP], [END] to stdout
  - Runtime must be < 20 minutes on 2 vCPU / 8 GB RAM

HOW IT WORKS:
  1. The environment is created directly in Python (no HTTP needed locally)
  2. For each of the 3 tasks, we run a loop:
       - Send the current observation to the LLM as a JSON prompt
       - LLM responds with a JSON action (matching CampusAction schema)
       - We execute the action in the environment
       - Repeat until done=True or max steps reached
  3. The [START], [STEP], [END] logs are what the judges parse to score us

RUN LOCALLY:
  $env:API_BASE_URL = "https://api-inference.huggingface.co/v1/"
  $env:MODEL_NAME   = "meta-llama/Meta-Llama-3-8B-Instruct"
  $env:HF_TOKEN     = "hf_..."
  python inference.py
"""

from __future__ import annotations

import json
import os
import sys

from openai import OpenAI

# Add project root to path (needed when running from a different directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ActionType, CampusAction
from server.campus_environment import CampusEnvironment, TASKS

# ── Environment variable setup ────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1/")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Meta-Llama-3-8B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN",     "")

# ── The system prompt sent to the LLM ────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI assistant for a university scheduling system.
Your job is to resolve campus scheduling conflicts by choosing the right actions.

AVAILABLE ACTIONS (respond with exactly one JSON object per turn):

1. Query a professor's schedule:
   {"action_type": "query_schedule", "professor_id": "Smith"}

2. Find empty rooms at a time slot:
   {"action_type": "query_empty_rooms", "time_slot": "10:00 AM"}

3. Move a class to a new room and time:
   {"action_type": "move_class", "class_id": "CS101", "room_id": "102", "time_slot": "10:00 AM"}

4. Cancel a class:
   {"action_type": "cancel_class", "class_id": "CS101"}

5. Notify students about a class change:
   {"action_type": "notify_students", "class_id": "CS101"}

6. Submit your solution when done:
   {"action_type": "submit_task"}

RULES:
- Always query before acting (find empty rooms before moving a class)
- Never double-book a room at the same time
- Respond with ONLY a valid JSON object, no explanation
- Classes: CS101 (Smith, Room 101, 10:00 AM), MATH201 (Smith, Room 102, 11:00 AM), PHY301 (Jones, Auditorium, 2:00 PM)
- Rooms: 101, 102, 103, Auditorium"""


def call_llm(client: OpenAI, messages: list[dict]) -> dict:
    """
    Call the LLM and parse its JSON response into a dict.
    Falls back to submit_task if parsing fails.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=150,
            temperature=0.1,   # low temp for deterministic JSON output
        )
        content = response.choices[0].message.content.strip()

        # Extract JSON even if the model wraps it in markdown code blocks
        if "```" in content:
            start = content.find("{")
            end   = content.rfind("}") + 1
            content = content[start:end]

        return json.loads(content)

    except Exception as e:
        print(f"  [WARN] LLM parse error: {e}. Falling back to submit_task.",
              file=sys.stderr)
        return {"action_type": "submit_task"}


def run_task(env: CampusEnvironment, client: OpenAI, task_level: int) -> float:
    """
    Run one task level and return the final reward score.

    This function:
      1. Resets the environment to the specified task level
      2. Loops: ask LLM → execute action → log [STEP]
      3. Returns the final reward when done=True
    """
    # ── MANDATORY LOG: START ──────────────────────────────────────────────
    print(f"[START] Task {task_level}")

    obs = env.reset(task_level=task_level)

    # Build the conversation: system prompt + first user message
    messages = [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": (
            f"TASK: {obs.active_task}\n\n"
            f"CURRENT STATE: {obs.system_message}\n\n"
            "What is your first action? Respond with a JSON object only."
        )},
    ]

    final_score = 0.0
    max_steps = 12  # keep well under the 20-minute limit

    for step_num in range(1, max_steps + 1):
        # Get action from LLM
        action_dict = call_llm(client, messages)

        # Build a valid CampusAction (handle unknown action_types gracefully)
        try:
            action = CampusAction(**action_dict)
        except Exception:
            action = CampusAction(action_type=ActionType.SUBMIT_TASK)

        # ── MANDATORY LOG: STEP ───────────────────────────────────────────
        params = {k: v for k, v in action_dict.items() if k != "action_type" and v is not None}
        print(f"[STEP] Action: {action.action_type.value} | Params: {json.dumps(params)}")

        # Execute action in environment
        obs = env.step(action)

        # Update conversation with environment feedback
        messages.append({
            "role": "assistant",
            "content": json.dumps(action_dict),
        })
        messages.append({
            "role": "user",
            "content": (
                f"Result: {obs.system_message}\n"
                f"Reward: {obs.reward}\n"
                f"Done: {obs.done}\n\n"
                + (
                    "Task complete." if obs.done
                    else "What is your next action? Respond with a JSON object only."
                )
            ),
        })

        if obs.done:
            final_score = obs.reward if obs.reward is not None else 0.0
            break

    # ── MANDATORY LOG: END ────────────────────────────────────────────────
    print(f"[END] Final Score: {final_score}")
    return final_score


def main():
    """Run all 3 task levels and report scores."""
    # Validate environment variables
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN environment variable is not set.", file=sys.stderr)
        print("Set it with:  $env:HF_TOKEN='hf_...'", file=sys.stderr)
        sys.exit(1)

    # Set up the OpenAI client pointing to HuggingFace Inference API
    client = OpenAI(
        api_key=HF_TOKEN,
        base_url=API_BASE_URL,
    )

    # Create the environment (runs locally — no HTTP server needed)
    env = CampusEnvironment()

    total_score = 0.0
    for level in [1, 2, 3]:
        score = run_task(env, client, level)
        total_score += score

    print(f"\nTotal Score: {total_score:.1f} / 3.0")


if __name__ == "__main__":
    main()
