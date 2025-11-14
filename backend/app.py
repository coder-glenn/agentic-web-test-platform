
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .agent_service import AgentService

app = FastAPI()
agent = AgentService()

# Serve artifacts (screenshots) directory so frontend can preview images.
import os
artifacts_path = os.path.join(os.path.dirname(__file__), 'artifacts')
os.makedirs(artifacts_path, exist_ok=True)
app.mount('/artifacts', StaticFiles(directory=artifacts_path), name='artifacts')

class SubmitReq(BaseModel):
    nl: str

# Simple WebSocket manager to relay logs per run id
class ConnectionManager:
    def __init__(self):
        # run_id -> set of websockets
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, run_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(run_id, set()).add(websocket)

    def disconnect(self, run_id: str, websocket: WebSocket):
        conns = self.active_connections.get(run_id)
        if conns and websocket in conns:
            conns.remove(websocket)
            if not conns:
                del self.active_connections[run_id]

    async def send_log(self, run_id: str, message: dict):
        conns = list(self.active_connections.get(run_id, []))
        to_remove = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(run_id, ws)

manager = ConnectionManager()

@app.post('/submit')
async def submit(req: SubmitReq):
    run_id = await agent.submit(req.nl)
    return {'run_id': run_id}

@app.get('/status/{run_id}')
async def status(run_id: str):
    return await agent.status(run_id)

@app.get('/result/{run_id}')
async def result(run_id: str):
    from .storage import Storage
    storage = Storage()
    try:
        res = await storage.load_result(run_id)
        return res
    except Exception as e:
        return {'error': str(e)}

@app.websocket('/ws/{run_id}')
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await manager.connect(run_id, websocket)
    try:
        while True:
            # keep connection open; we don't expect messages from client in this prototype
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)

# Expose manager to other modules (executor will import)
app.state.ws_manager = manager

if __name__ == '__main__':
    uvicorn.run('backend.app:app', host='0.0.0.0', port=8000, reload=True)
