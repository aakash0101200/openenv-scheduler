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
app = create_app(
    CampusEnvironment,
    CampusAction,
    CampusObservation,
    env_name="campus_scheduler",
)


def main():
    """Entry point for: uv run server  (defined in pyproject.toml scripts)."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
