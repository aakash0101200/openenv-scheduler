---
title: Campus Scheduler — OpenEnv Environment
emoji: 🎓
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: AI agent for campus scheduling via OpenEnv
---

# 🎓 Dynamic Campus Scheduling Environment

> **OpenEnv Hackathon Round 1 — Real-World AI Environment**
> An AI agent acts as an emergency university registrar, resolving room conflicts,
> professor sick leave, and cascading scheduling crises in real time.

[![OpenEnv](https://img.shields.io/badge/OpenEnv--core-0.2.3-brightgreen)](https://pypi.org/project/openenv-core/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![HF Space](https://img.shields.io/badge/HF%20Space-Live-yellow)](https://huggingface.co/spaces/sky001000/campus-scheduler)

---

## 🧭 Mission

An AI agent acts as an emergency university registrar, resolving room conflicts, professor sick leave, and cascading crises in real time. The agent must resolve these issues without creating double-bookings.

---

## ⚙️ Action Space

The agent can perform the following actions:
- `query_schedule`: Look up classes taught by a professor
- `query_empty_rooms`: Find rooms free at a given time
- `move_class`: Relocate a class to a new room and time
- `cancel_class`: Mark a class as cancelled
- `notify_students`: Notify enrolled students about a change
- `submit_task`: Finalize the solution and receive grading

---

## 🏆 Scoring

- **+0.1 to +0.4**: Partial reward for progress (info gathering, valid moves, notifications)
- **-0.5**: Hard penalty for creating new double-booking conflicts
- **+1.0**: Full reward for solving the task

## 🚀 Usage

Select a scenario from the dropdown above and use the Action Controls to solve it!
