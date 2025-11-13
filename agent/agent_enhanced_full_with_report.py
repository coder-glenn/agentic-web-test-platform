"""
Enhanced Agent Server with /report endpoint
- Uses report_generator.compute_metrics and generate_summary
- Exposes GET /report returning metrics + summary
"""

import os
import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, Optional
from utils.task_manager import TaskManager
from config import Config
from report_generator import compute_metrics, generate_summary

# Optional LangChain/OpenAI presence used inside report_generator

app = FastAPI(title="Agent Enhanced with Reports")

# logging
os.makedirs(Config.DATA_DIR, exist_ok=True)
logger = logging.getLogger("agent")
logger.setLevel(Config.LOG_LEVEL)
handler = logging.FileHandler(Config.LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

# task manager
task_manager = TaskManager(Config.TASK_STATE_FILE)

class RunRequest(BaseModel):
    test_ir: Dict[str, Any]
    run_id: Optional[str] = None
    auto_repair: Optional[bool] = True

@app.get("/report")
async def get_report():
    metrics = compute_metrics(Config.DATA_DIR)
    summary = generate_summary(metrics, openai_api_key=Config.OPENAI_API_KEY)
    return {"metrics": metrics, "summary": summary}

# re-export run endpoints from enhanced agent (simple wrapper)
@app.post("/run")
async def run(req: RunRequest):
    # delegate to previous enhanced run implementation if exists
    # To avoid duplicating code, import the original run from agent_enhanced_full if available
    try:
        from agent_enhanced_full import run as original_run
        return await original_run(req)
    except Exception:
        raise HTTPException(status_code=500, detail="Original run implementation not found. Please ensure agent_enhanced_full.py is present.")

@app.get("/tasks")
async def list_tasks():
    return task_manager.all_tasks()

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
