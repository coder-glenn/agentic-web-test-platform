# AI Web Test Platform — Prototype

This repository is a runnable prototype of an AI-driven web automation testing platform.
It includes:
- FastAPI backend (backend/) with an AgentService, Planner (LLM stub), Executor and Playwright Adapter.
- Minimal React frontend (frontend/) using Vite.
- Example IRs and scripts.

## Quick start (local, development)

1. Create and activate python venv (Python 3.10+):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   playwright install
   ```
2. Start backend:
   ```bash
   uvicorn backend.app:app --reload --port 8000
   ```
3. Start frontend (in another terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:5173

Note: For a production-grade deployment, refer to the design doc in the canvas.
