"""
Python MCP Executor PoC
Implements a minimal Playwright-based executor that can interpret TestIR and perform browser automation.
This replaces the TypeScript MCP adapter with a Python service for easier integration with LangChain agents.

Endpoints:
- POST /exec: accepts { run_id, test_ir } and executes via Playwright.
- Optionally saves screenshots, DOM snapshot, HAR file under ./artifacts.

Requirements:
    pip install fastapi uvicorn playwright
    playwright install chromium

Run:
    uvicorn executor_service:app --port 3000

This service can be called by the Agent (agent_server.py) at EXECUTOR_URL.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import os
import json
import uuid
from datetime import datetime

from playwright.async_api import async_playwright

app = FastAPI(title="Python MCP Executor PoC")

ARTIFACT_DIR = os.path.abspath("./artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# -----------------------------
# Data models
# -----------------------------

class Step(BaseModel):
    action: str
    target: Optional[Dict[str, Any]] = None
    value: Optional[str] = None
    timeout_ms: Optional[int] = 5000

class TestIR(BaseModel):
    test_id: str
    description: Optional[str] = None
    steps: List[Step]
    meta: Optional[Dict[str, Any]] = {}

class ExecRequest(BaseModel):
    run_id: str
    test_ir: TestIR

class ExecResponse(BaseModel):
    run_id: str
    status: str
    artifacts: Optional[Dict[str, Any]] = {}
    error: Optional[str] = None

# -----------------------------
# Core execution logic
# -----------------------------

async def execute_test_ir(run_id: str, test_ir: TestIR) -> Dict[str, Any]:
    result = {"status": "success", "artifacts": {}}
    artifact_prefix = os.path.join(ARTIFACT_DIR, f"{run_id}_{test_ir.test_id}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(record_har_path=f"{artifact_prefix}.har")
            page = await context.new_page()

            for step in test_ir.steps:
                try:
                    action = step.action.lower()
                    target = step.target or {}
                    ttype = target.get("type")
                    tval = target.get("value")

                    if action == "goto":
                        await page.goto(tval, timeout=step.timeout_ms)
                    elif action == "click":
                        await page.click(tval, timeout=step.timeout_ms)
                    elif action == "type":
                        await page.fill(tval, step.value or "", timeout=step.timeout_ms)
                    elif action == "waitfor":
                        await page.wait_for_selector(tval, timeout=step.timeout_ms)
                    elif action == "assert":
                        content = await page.content()
                        if tval not in content:
                            raise AssertionError(f"Assertion failed: {tval} not found in page content")
                    elif action == "screenshot":
                        shot_path = f"{artifact_prefix}_step_{uuid.uuid4().hex[:6]}.png"
                        await page.screenshot(path=shot_path, full_page=True)
                        result["artifacts"].setdefault("screenshots", []).append(shot_path)
                    else:
                        print(f"[WARN] Unknown action: {action}")

                except Exception as step_err:
                    # Capture DOM snapshot and add failure record
                    dom_path = f"{artifact_prefix}_dom.json"
                    try:
                        dom_content = await page.content()
                        with open(dom_path, "w", encoding="utf-8") as f:
                            json.dump({"html": dom_content}, f, ensure_ascii=False)
                        result["artifacts"]["dom_snapshot_key"] = dom_path
                    except Exception as e:
                        print(f"DOM snapshot failed: {e}")

                    result.update({
                        "status": "failed",
                        "error": str(step_err),
                        "failed_step": step.dict(),
                    })
                    break

            await context.close()
            await browser.close()

        # Save HAR file
        if os.path.exists(f"{artifact_prefix}.har"):
            result["artifacts"]["har_key"] = f"{artifact_prefix}.har"

        # Timestamp and summary
        result["completed_at"] = datetime.utcnow().isoformat()
        return result

    except Exception as e:
        result.update({"status": "error", "error": str(e)})
        return result

# -----------------------------
# Endpoint
# -----------------------------

@app.post("/exec", response_model=ExecResponse)
async def exec_test_ir(req: ExecRequest):
    run_id = req.run_id or f"run_{uuid.uuid4().hex[:8]}"
    print(f"[Executor] Starting run {run_id} for test {req.test_ir.test_id}")

    res = await execute_test_ir(run_id, req.test_ir)

    if res["status"] in ("failed", "error"):
        raise HTTPException(status_code=500, detail=res)

    return ExecResponse(run_id=run_id, status=res["status"], artifacts=res.get("artifacts", {}))
