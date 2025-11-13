import asyncio, json, os, uuid
from datetime import datetime
from typing import Dict, Any

class TaskManager:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.tasks: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
        os.makedirs(os.path.dirname(state_file) or '.', exist_ok=True)
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        data = json.loads(line)
                        self.tasks[data["id"]] = data
            except Exception:
                pass

    async def _persist(self, task_id: str):
        async with self.lock:
            with open(self.state_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(self.tasks[task_id], ensure_ascii=False) + "\n")

    def create_task(self, description: str) -> str:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "description": description,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.tasks[task_id] = task
        # persist initial record synchronously
        with open(self.state_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
        return task_id

    async def update_task(self, task_id: str, status: str, result: Any = None):
        if task_id not in self.tasks:
            return
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        if result is not None:
            self.tasks[task_id]["result"] = result
        await self._persist(task_id)

    def get_task(self, task_id: str):
        return self.tasks.get(task_id)

    def all_tasks(self):
        return list(self.tasks.values())
