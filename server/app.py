import uvicorn
from fastapi import FastAPI
from scheduler_env import SchedulerEnv
from env_models import Action

app = FastAPI(title="Dynamic Rescheduling Assistant API")
env = SchedulerEnv()

@app.post("/reset")
def reset():
    return env.reset()

@app.get("/state")
def state():
    return env.state()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()