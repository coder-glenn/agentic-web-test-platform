
import asyncio
from .planner import Planner
from .executor import Executor
from .storage import Storage
from fastapi import current_app

class AgentService:
    def __init__(self, llm=None):
        self.storage = Storage()
        self.planner = Planner(llm=llm)
        # executor will be created lazily because we need access to app.state.ws_manager
        self._tasks = {}
        self._executor = None

    def _ensure_executor(self):
        if self._executor is None:
            # current_app may not be available at import time; guard
            ws_manager = None
            try:
                ws_manager = current_app.state.ws_manager
            except Exception:
                ws_manager = None
            self._executor = Executor(storage=self.storage, ws_manager=ws_manager)

    async def submit(self, nl_request: str) -> str:
        ir = self.planner.plan(nl_request)
        self._ensure_executor()
        task = asyncio.create_task(self._executor.run_ir(ir))
        self._tasks[ir.id] = task
        return ir.id

    async def status(self, id: str):
        task = self._tasks.get(id)
        if not task:
            return {'status': 'unknown'}
        if task.done():
            return {'status': 'done'}
        return {'status': 'running'}
