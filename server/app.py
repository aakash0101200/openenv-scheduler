"""
FastAPI application for the Campus Scheduler Environment.

WHY one line?
    openenv-core's create_app() automatically generates ALL the HTTP and
    WebSocket endpoints you need:
        GET  /health     → judges ping this to confirm the Space is live
        POST /reset      → start a new episode
        POST /step       → send an action, get an observation + reward
        GET  /state      → get current episode metadata
        GET  /docs       → interactive Swagger UI (auto-generated)
        GET  /web        → built-in browser UI for manual testing

    You do NOT write these routes yourself — the framework handles it.

Usage (local dev):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

Usage (production / HF Space via Dockerfile):
    uvicorn server.app:app --host 0.0.0.0 --port 8000
"""

import sys
import os

# Add the project root to path so server/ can import from root models.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_app

from server.campus_environment import CampusEnvironment
from models import CampusAction, CampusObservation

# ── Create the FastAPI app ────────────────────────────────────────────────────
# Pass the CLASS (not an instance) so the framework can create one session
# per connected client (required when SUPPORTS_CONCURRENT_SESSIONS = True).
import json
import gradio as gr

def _format_observation(data):
    lines = []
    obs = data.get("observation", {})
    if isinstance(obs, dict) and obs.get("system_message"):
        lines.append(f"### Current State\n> **{obs['system_message']}**\n")
        
    reward = data.get("reward")
    done = data.get("done")
    if reward is not None:
        lines.append(f"**Reward:** `{reward}` {'(Passing 🎉)' if reward == 1.0 else ''}")
    if done is not None:
        lines.append(f"**Done:** `{done}`")
    return "\n".join(lines) if lines else "*No observation data found.*"

def custom_gradio_builder(web_manager, action_fields, metadata, is_chat_env, title, quick_start_md):
    display_title = "Campus Scheduler Dashboard"

    async def reset_env(task_choice):
        task_level = 1
        if "Medium" in task_choice: task_level = 2
        elif "Hard" in task_choice: task_level = 3
        try:
            data = await web_manager.reset_environment({"config": {"task_level": task_level}})
            obs_md = _format_observation(data)
            return (obs_md, json.dumps(data, indent=2), f"Scenario '{task_choice}' loaded successfully.")
        except Exception as e:
            return ("", "", f"Error: {e}")

    def _step_with_action(action_data):
        async def _run():
            try:
                data = await web_manager.step_environment(action_data)
                obs_md = _format_observation(data)
                return (obs_md, json.dumps(data, indent=2), "Action executed successfully.")
            except Exception as e:
                return ("", "", f"Error: {e}")
        return _run

    def get_state_sync():
        try:
            return json.dumps(web_manager.get_state(), indent=2)
        except Exception as e:
            return f"Error: {e}"

    with gr.Blocks(title=display_title, theme=gr.themes.Soft()) as demo:
        with gr.Accordion("📝 Instructions & Quick Start Guide", open=False):
            gr.Markdown(quick_start_md or "Welcome to the OpenEnv Guided Dashboard.")
            if metadata and getattr(metadata, "readme_content", None):
                gr.Markdown(metadata.readme_content)

        gr.Markdown("## 🎓 Dynamic Campus Scheduler")
        with gr.Row():
            task_dropdown = gr.Dropdown(
                choices=["Task 1 (Easy)", "Task 2 (Medium)", "Task 3 (Hard)"],
                value="Task 1 (Easy)",
                label="Select Scenario",
                interactive=True,
                scale=2
            )
            reset_btn = gr.Button("🔄 Load Scenario & Reset", variant="primary", scale=1)

        obs_display = gr.Markdown(value="*Select a scenario and click Load to begin.*")

        gr.Markdown("---")
        gr.Markdown("## Action Control Panel")
        
        step_inputs = []
        with gr.Row():
            for field in action_fields:
                name = field["name"]
                field_type = field.get("type", "text")
                label = name.replace("_", " ").title()
                
                if field_type == "select":
                    inp = gr.Dropdown(choices=field.get("choices", []), label=label, allow_custom_value=True)
                else:
                    inp = gr.Textbox(label=label, placeholder=field.get("placeholder", ""))
                step_inputs.append(inp)
                
        with gr.Row():
            step_btn = gr.Button("🚀 Execute Action", variant="primary")
            state_btn = gr.Button("📊 Internal System State", variant="secondary")

        status = gr.Textbox(label="Status Logging", interactive=False)
        
        with gr.Accordion("Raw JSON Developer Output", open=False):
            raw_json = gr.Code(label="JSON", language="json", interactive=False)

        async def step_form(*values):
            action_data = {}
            for i, field in enumerate(action_fields):
                if i >= len(values): break
                val = values[i]
                if val is not None and val != "":
                    action_data[field["name"]] = val
            return await _step_with_action(action_data)()

        # Map the UI events
        reset_btn.click(fn=reset_env, inputs=[task_dropdown], outputs=[obs_display, raw_json, status])
        step_btn.click(fn=step_form, inputs=step_inputs, outputs=[obs_display, raw_json, status])
        state_btn.click(fn=get_state_sync, outputs=[raw_json])

    return demo

app = create_app(
    CampusEnvironment,
    CampusAction,
    CampusObservation,
    env_name="campus_scheduler",
    gradio_builder=custom_gradio_builder,
)

def main():
    """Entry point for: uv run server  (defined in pyproject.toml scripts)."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
