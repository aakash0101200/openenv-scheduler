---
title: Campus Scheduler
emoji: 🎓
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: university scheduling
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
* **Classroom flooding:** Students have nowhere to go.
* **Professor sick leave:** Classes must be cancelled and students notified.
* **Double-booking:** A chain of rescheduling must happen without new conflicts.

**Why this is hard for AI:** The agent must plan ahead, respect constraints (no double-booking), and complete multi-step tasks in the correct order.

---

## ⚙️ Action Space

| Action | Required Fields | Description |
| :--- | :--- | :--- |
| `query_schedule` | `professor_id` | Look up all classes taught by a professor |
| `query_empty_rooms` | `time_slot` | Find all rooms free at a given time |
| `move_class` | `class_id`, `room_id`, `time_slot` | Relocate a class to a new room and time |
| `cancel_class` | `class_id` | Mark a class as cancelled |
| `notify_students` | `class_id` | Notify enrolled students about a change |
| `submit_task` | *(none)* | Signal task complete → triggers grading |

---

## 🏆 Reward Function

| Event | Reward | Rationale |
| :--- | :--- | :--- |
| Query schedule/rooms | **+0.1** | Rewards information-gathering |
| Move class (success) | **+0.4** | Rewards conflict-free relocation |
| Cancel class | **+0.2** | Rewards appropriate cancellation |
| Notify students | **+0.15** | Rewards communication steps |
| `submit_task` (correct) | **+1.0** | Full reward for completion |
| Move class (conflict) | **-0.5** | Hard penalty for new double-bookings |

---

## 🚀 How to Run

### Prerequisites
```bash
pip install openenv-core[core]>=0.2.2 openai>=1.0.0
