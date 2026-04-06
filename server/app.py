import sys
import os
from fastapi.responses import HTMLResponse

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_app
from server.campus_environment import CampusEnvironment
from models import CampusAction, CampusObservation

# 1. Create the base app using the framework
app = create_app(
    CampusEnvironment,
    CampusAction,
    CampusObservation,
    env_name="campus_scheduler",
)

# 2. Add a custom Dashboard as the root (/) to allow Task Selection
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Campus Scheduler Controller</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>.terminal { background: #1a1a1a; color: #00ff41; font-family: monospace; }</style>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-4xl mx-auto space-y-6">
            <div class="bg-white p-6 rounded-xl shadow-md border-t-4 border-indigo-600">
                <h1 class="text-2xl font-bold mb-4">🎓 Campus Scheduler Dashboard</h1>
                
                <div class="flex gap-4 items-end border-b pb-6 mb-6">
                    <div class="flex-1">
                        <label class="block text-sm font-bold text-gray-700">Choose Your Task:</label>
                        <select id="taskIdx" class="w-full mt-1 p-2 border rounded bg-gray-50">
                            <option value="0">Task 1: Room Maintenance (Easy)</option>
                            <option value="1">Task 2: Professor Sick Leave (Medium)</option>
                            <option value="2">Task 3: Cascading Conflict (Hard)</option>
                        </select>
                    </div>
                    <button onclick="resetToTask()" class="bg-indigo-600 text-white px-6 py-2 rounded font-bold hover:bg-indigo-700">
                        Reset to Selected Task
                    </button>
                </div>

                <div id="log" class="terminal p-4 rounded-lg h-64 overflow-y-auto mb-4 text-sm">
                    [SYSTEM] Environment ready. Select a task and click Reset.
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div class="bg-gray-50 p-3 rounded border">
                        <span class="font-bold text-gray-500 uppercase block">Status</span>
                        <div id="status">Waiting...</div>
                    </div>
                    <div class="bg-gray-50 p-3 rounded border">
                        <span class="font-bold text-gray-500 uppercase block">Total Reward</span>
                        <div id="reward" class="text-xl font-bold text-green-600">0.0</div>
                    </div>
                </div>
            </div>
            
            <div class="text-center text-gray-400 text-xs">
                Built with OpenEnv Core • API Documentation available at <a href="/docs" class="underline">/docs</a>
            </div>
        </div>

        <script>
            async function resetToTask() {
                const idx = document.getElementById('taskIdx').value;
                const log = document.getElementById('log');
                
                log.innerHTML += `<div class="text-yellow-400 mt-2">--- Initializing Task ${parseInt(idx)+1} ---</div>`;
                
                const response = await fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ task_index: parseInt(idx) })
                });
                
                const data = await response.json();
                log.innerHTML += `<div>[TASK] ${data.observation.active_task}</div>`;
                document.getElementById('status').innerText = "Task Started";
                document.getElementById('reward').innerText = "0.0";
                log.scrollTop = log.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()