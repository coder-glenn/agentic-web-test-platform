# AI Test Platform — Finalized with Reports

This repository includes an AI-driven automated web testing platform (MVP → enhanced). Key features:

- Agent (FastAPI + LangChain optional) that generates tests from NL, runs them, and self-repairs.
- Executor (Playwright) that executes TestIR and returns artifacts.
- Frontend (React + Vite) for generating scenarios, running tests, and viewing reports.
- Persistent JSONL logs and Failure Bank for learning and analytics.

## New: Intelligent Report Dashboard
- Endpoint: `GET /report` on Agent
- Frontend: Reports view in the React app
- Metrics computed from `data/agent.log.jsonl`, `data/tasks.jsonl`, `data/failure_bank.jsonl`
- LLM-based summary if `OPENAI_API_KEY` is provided

## Quickstart
1. Ensure `docker-compose.yml` in repo root (previously generated).
2. Copy `agent/`, `executor/`, `frontend/` folders into repo as provided in canvas.
3. (Optional) create `.env` with `OPENAI_API_KEY`.
4. Run: `docker-compose up --build`
5. Open frontend: `http://localhost:5173`

## Agent Endpoints
- `POST /generate_scenario` — input `{ nl, target_url? }`, returns TestIR.
- `POST /run` — input `{ test_ir, run_id?, auto_repair? }` runs and returns task status/result.
- `GET /tasks` and `GET /tasks/{id}` — task management.
- `GET /report` — returns metrics and AI summary.

## Files to check
- `agent/config.py` — configuration
- `agent/agent_enhanced_full.py` — main agent logic
- `agent/report_generator.py` — metrics + summary
- `agent/utils/task_manager.py` — task persistence
- `executor/executor_service.py` — Playwright executor
- `frontend/src/App.tsx` — includes Reports view

## Notes on accuracy & checks
- All Python modules in `agent/` are intended to run with working dir set to `agent/` (Docker image sets WORKDIR accordingly).
- If you run the agent locally (not via Docker), ensure `PYTHONPATH` includes the `agent/` folder or run `python -m agent.agent_enhanced_full` appropriately.
- LLM features are optional and guarded by presence of `OPENAI_API_KEY` and LangChain availability.

## Next steps (Agent-focused)
1. Replace Failure Bank with vector DB + embeddings for better retrieval.
2. Expand repair strategies (visual matching, element path heuristics).
3. Add 'proposed-fix' review workflow (UI approval before applying).
4. Add experiments for model fine-tuning from high-quality repair cases.
