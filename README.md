---
title: Campus Scheduler — OpenEnv Environment
emoji: 🎓
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: Resolves university scheduling
---

# 🎓 Dynamic Campus Scheduling Environment

> **OpenEnv Hackathon Round 1 — Real-World AI Environment**
> An AI agent acts as an emergency university registrar, resolving room conflicts,
> professor sick leave, and cascading scheduling crises in real time.

[![OpenEnv](https://img.shields.io/badge/OpenEnv--core-0.2.3-brightgreen)](https://pypi.org/project/openenv-core/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![HF Space](https://img.shields.io/badge/HF%20Space-Live-yellow)](https://huggingface.co/spaces/sky001000/campus-scheduler)

---

## 🧭 Problem Statement

Every university's scheduling office faces cascading crises daily:
- A classroom floods → dozens of students have nowhere to go
- A professor gets sick → all their classes must be cancelled and students notified
- A venue gets double-booked → a chain of rescheduling must happen without creating new conflicts

These decisions currently require a human administrator. This environment trains an AI agent to handle them autonomously — querying available rooms, resolving conflicts, and notifying affected students — all without creating double-bookings.

**Why this is hard for AI:** The agent must plan ahead (query before acting), respect constraints (no double-booking), and complete multi-step tasks in the correct order to get a reward.

---

## ⚙️ Action Space

The agent can perform **6 action types** at each step:

| Action | Required Fields | Description |
|--------|----------------|-------------|
| `query_schedule` | `professor_id` | Look up all classes taught by a professor |
| `query_empty_rooms` | `time_slot` | Find all rooms free at a given time |
| `move_class` | `class_id`, `room_id`, `time_slot` | Relocate a class to a new room and time |
| `cancel_class` | `class_id` | Mark a class as cancelled |
| `notify_students` | `class_id` | Notify enrolled students about a change |
| `submit_task` | *(none)* | Signal task complete → triggers grading |

### Action Schema (Pydantic model extending `openenv-core Action`):
```python
class CampusAction(Action):
    action_type:  ActionType    # Required
    class_id:     Optional[str] # e.g. "CS101"
    room_id:      Optional[str] # e.g. "102" or "Auditorium"
    time_slot:    Optional[str] # e.g. "10:00 AM"
    professor_id: Optional[str] # e.g. "Smith"
```

---

## 👁️ Observation Space

After each action the agent receives a `CampusObservation`:

| Field | Type | Description |
|-------|------|-------------|
| `done` | `bool` | True when the agent has submitted the task |
| `reward` | `float \| None` | Partial reward from the last action |
| `system_message` | `str` | Human-readable result of the last action |
| `active_task` | `str` | The current problem the agent needs to solve |
| `query_results` | `list \| None` | Data returned by QUERY_* actions |

---

## 🏆 Reward Function

The reward is designed to give **partial credit for progress**, not just a binary pass/fail:

| Event | Reward | Rationale |
|-------|--------|-----------|
| Query schedule or rooms | **+0.1** | Rewards information-gathering before acting |
| Move class (success) | **+0.4** | Rewards conflict-free relocation |
| Cancel class | **+0.2** | Rewards appropriate cancellation |
| Notify students | **+0.15** | Rewards completing communication steps |
| `submit_task` (correct solution) | **+1.0** | Full reward for solving the problem |
| `submit_task` (incomplete) | **−0.2** | Penalises premature submission |
| Move class (double-booking) | **−0.5** | Hard penalty — creates a NEW conflict |
| Invalid class/room ID | **−0.2** | Penalises hallucinated identifiers |

> **Design note:** The −0.5 double-booking penalty is intentionally larger than the +0.4 move reward. In real life, a double-booked classroom is *worse* than doing nothing — it creates two sets of angry students instead of one.

---

## 📋 Task Levels

### 🟢 Task 1 — Easy: Room Reallocation
> *Room 101 is under maintenance. Move CS101 to a free room at 10:00 AM.*

**Optimal sequence:**
1. `query_empty_rooms` at 10:00 AM → sees rooms 103, Auditorium are free
2. `move_class` CS101 → Room 103, 10:00 AM
3. `submit_task`

**Success condition:** CS101 is no longer in Room 101 and is still active.

---

### 🟡 Task 2 — Medium: Professor Sick Leave
> *Prof. Smith has an emergency. Cancel all their classes and notify students.*

**Optimal sequence:**
1. `query_schedule` for Prof. Smith → sees CS101 and MATH201
2. `cancel_class` CS101
3. `cancel_class` MATH201
4. `notify_students` CS101
5. `notify_students` MATH201 *(optional but thorough)*
6. `submit_task`

**Success condition:** CS101 cancelled + MATH201 cancelled + CS101 students notified.

---

### 🔴 Task 3 — Hard: Cascading Conflict
> *The Auditorium has a double-booking. Move PHY301 to a new room AND a new time.*

**Optimal sequence:**
1. `query_empty_rooms` at various times → find a free slot
2. `move_class` PHY301 → free room, new time (NOT 2:00 PM)
3. `notify_students` PHY301
4. `submit_task`

**Success condition:** PHY301 is not in Auditorium + PHY301 students notified.

---

## 🚀 How to Run

### Prerequisites
```bash
pip install openenv-core[core]>=0.2.2 openai>=1.0.0
```

### Run the Server Locally
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Test it:
```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

### Run the Inference Script (AI Agent)
```bash
# Windows PowerShell
$env:API_BASE_URL = "https://api-inference.huggingface.co/v1/"
$env:MODEL_NAME   = "meta-llama/Meta-Llama-3-8B-Instruct"
$env:HF_TOKEN     = "hf_your_token_here"
python inference.py

# Linux/Mac
export API_BASE_URL="https://api-inference.huggingface.co/v1/"
export MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
export HF_TOKEN="hf_your_token_here"
python inference.py
```

Expected output format:
```
[START] Task 1
[STEP] Action: query_empty_rooms | Params: {"time_slot": "10:00 AM"}
[STEP] Action: move_class | Params: {"class_id": "CS101", "room_id": "103", "time_slot": "10:00 AM"}
[STEP] Action: submit_task | Params: {}
[END] Final Score: 1.0
[START] Task 2
...
[END] Final Score: 1.0
```

### Run with Docker
```bash
docker build -t campus-scheduler .
docker run -p 7860:7860 campus-scheduler
```

---

## 📁 Project Structure

```
openenv-scheduler/
├── models.py                     # Typed Action, Observation, State models
├── inference.py                  # AI agent script (mandatory, root dir)
├── openenv.yaml                  # Environment manifest (3 tasks defined)
├── pyproject.toml                # Dependencies (openenv-core[core])
├── Dockerfile                    # HuggingFace Space deployment
├── __init__.py                   # Package exports
└── server/
    ├── campus_environment.py     # Core game logic (Environment subclass)
    ├── app.py                    # FastAPI server (create_app one-liner)
    └── requirements.txt          # Docker pip dependencies
```

---

## 🏗️ Technical Architecture

```
inference.py  ──(direct Python calls)──►  CampusEnvironment
                                                │
                                         reset() / step() / state
                                                │
                (on HuggingFace Space)   FastAPI Server (create_app)
                                                │
                                    /health  /reset  /step  /state
                                         (judges ping this)
```

The environment runs as both:
- A **local Python object** (used by inference.py for testing)
- A **live HTTP API** (deployed on HF Space for the judges to validate)

---

## 📜 License

MIT — see repository for details.
