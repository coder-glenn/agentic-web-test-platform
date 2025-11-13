"""
Enhanced Agent Server — adds:
- Scenario generation (/generate_scenario)
- Self-improving testing loop (auto-repair & retry inside /run with repairer integration)
- FailureBank for storing past failures and simple similarity-based retrieval

Run: uvicorn agent_enhanced_full:app --reload --port 8000

Notes:
- Requires agent/utils/task_manager.py and agent/config.py present as defined earlier.
- Requires executor at EXECUTOR_URL (env).
- Uses OpenAI via LangChain if configured; otherwise falls back to heuristics.
"""

import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from utils.task_manager import TaskManager
from config import Config

# Optional LangChain/OpenAI imports
try:
    from langchain import LLMChain, PromptTemplate
    from langchain.llms import OpenAI
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

# Simple similarity
from difflib import SequenceMatcher

app = FastAPI(title="Agent Enhanced")

# logging
os.makedirs(Config.DATA_DIR, exist_ok=True)
logger = logging.getLogger("agent")
logger.setLevel(Config.LOG_LEVEL)
handler = logging.FileHandler(Config.LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

# task manager
task_manager = TaskManager(Config.TASK_STATE_FILE)

# failure bank (local file-based)
FAILURE_BANK_PATH = os.path.join(Config.DATA_DIR, "failure_bank.jsonl")

class GenerateScenarioRequest(BaseModel):
    nl: str
    target_url: Optional[str] = None

class RunRequest(BaseModel):
    test_ir: Dict[str, Any]
    run_id: Optional[str] = None
    auto_repair: Optional[bool] = True

class FailureRecord(BaseModel):
    job_id: str
    error: str
    failed_step: Dict[str, Any]
    artifacts: Dict[str, Any]
    timestamp: Optional[str] = None

# helpers
async def log_event(event_type: str, detail: dict):
    entry = {
        "time": datetime.utcnow().isoformat(),
        "event": event_type,
        "detail": detail
    }
    logger.info(json.dumps(entry, ensure_ascii=False))

async def call_executor(payload: dict, retries: int = Config.RETRY_COUNT):
    url = Config.EXECUTOR_URL
    last_exc = None
    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as resp:
                    body = await resp.json()
                    if resp.status == 200:
                        return body
                    else:
                        # executor returned failure info in body
                        return {"status": "failed", "detail": body}
        except Exception as e:
            last_exc = e
            if attempt < retries:
                await asyncio.sleep(Config.RETRY_DELAY)
            else:
                raise last_exc

# Failure bank functions
def add_failure_to_bank(failure: FailureRecord):
    with open(FAILURE_BANK_PATH, "a", encoding="utf-8") as f:
        record = failure.dict()
        if not record.get("timestamp"):
            record["timestamp"] = datetime.utcnow().isoformat()
        f.write(json.dumps(record, ensure_ascii=False) + "\\n")

def retrieve_similar_failures(text: str, limit: int = 3):
    results = []
    if not os.path.exists(FAILURE_BANK_PATH):
        return results
    with open(FAILURE_BANK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                sim = SequenceMatcher(None, text, json.dumps(rec.get("failed_step", ""))).ratio()
                results.append((sim, rec))
            except Exception:
                continue
    results.sort(key=lambda x: x[0], reverse=True)
    return [r for (_, r) in results[:limit]]

# Repairer (simple heuristics + LLM augmentation)
async def suggest_fixes_from_failure(failure: FailureRecord) -> List[Dict[str, Any]]:
    fixes = []
    err = failure.error.lower()
    failed_step = failure.failed_step

    # heuristic: timeout -> increase timeout or add waitFor
    if "timeout" in err or "timed out" in err:
        new_step = dict(failed_step)
        if "timeout_ms" in new_step:
            new_step["timeout_ms"] = int(new_step.get("timeout_ms", 5000) * 2)
        fixes.append({"type": "adjust_timeout", "patched_step": new_step, "confidence": 0.6, "explanation": "Increased timeout for flaky load"})
        fixes.append({"type": "insert_waitfor", "patched_step": {"action": "waitfor", "target": failed_step.get("target"), "timeout_ms": 8000}, "confidence": 0.55, "explanation": "Insert explicit waitFor before action"})

    # heuristic: selector not found -> try matching by text in DOM snapshot
    if "selector" in failed_step.get("target", {}).get("type", "") or "selector" in json.dumps(failed_step.get("target", {})):
        dom_key = failure.artifacts.get("dom_snapshot_key")
        if dom_key and os.path.exists(dom_key):
            try:
                with open(dom_key, "r", encoding="utf-8") as f:
                    dom = json.load(f)
                    html = dom.get("html", "")
                    # attempt to find button texts nearby
                    if "text=" in json.dumps(failed_step.get("target", {})):
                        pass
                    # naive: search for candidate text tokens from html
                    for token in ["submit", "确认", "下单", "login", "登录", "加入购物车"]:
                        if token in html:
                            fixes.append({"type": "selector_text_match", "patched_step": {"action": failed_step.get("action"), "target": {"type": "text", "value": token}, "timeout_ms": failed_step.get("timeout_ms", 5000)}, "confidence": 0.5, "explanation": f"Found token '{token}' in DOM"})
                            break
            except Exception:
                pass

    # LLM augmentation
    if LANGCHAIN_AVAILABLE and Config.OPENAI_API_KEY:
        try:
            prompt = (
                "Given a failed test step and artifacts, propose up to 3 concrete fix patches in JSON array format.\\n"
                f"Failed step: {json.dumps(failure.failed_step)}\\nArtifacts keys: {list(failure.artifacts.keys())}\\n"
            )
            template = PromptTemplate.from_template(prompt)
            llm = OpenAI(openai_api_key=Config.OPENAI_API_KEY, temperature=0.0)
            chain = LLMChain(llm=llm, prompt=template)
            out = chain.run({})
            parsed = json.loads(out)
            for p in parsed:
                fixes.append(p)
        except Exception:
            pass

    if not fixes:
        fixes.append({"type": "manual_investigation", "confidence": 0.2, "explanation": "No automated fix found"})
    return fixes

# Scenario generator
async def generate_scenario_from_nl(nl: str, target_url: Optional[str] = None) -> Dict[str, Any]:
    # use LLM if available
    if LANGCHAIN_AVAILABLE and Config.OPENAI_API_KEY:
        prompt = (
            "You are a Scenario Generator. Given a user request, output a TestIR JSON with detailed steps.\\n"
            f"Request: {nl}\\nTarget URL: {target_url or ''}\\nOutput only JSON."
        )
        template = PromptTemplate.from_template(prompt)
        llm = OpenAI(openai_api_key=Config.OPENAI_API_KEY, temperature=0.0)
        chain = LLMChain(llm=llm, prompt=template)
        out = chain.run({})
        try:
            return json.loads(out)
        except Exception:
            pass
    # fallback: heuristic expansion
    nl_lower = nl.lower()
    tid = f"scenario_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    steps = []
    if "checkout" in nl_lower or "purchase" in nl_lower or "下单" in nl_lower:
        steps = [
            {"action": "goto", "target": {"type": "url", "value": target_url or "https://example.com"}},
            {"action": "click", "target": {"type": "selector", "value": "#product-1"}},
            {"action": "click", "target": {"type": "selector", "value": "#add-to-cart"}},
            {"action": "goto", "target": {"type": "url", "value": "https://example.com/cart"}},
            {"action": "click", "target": {"type": "selector", "value": "#checkout"}},
            {"action": "assert", "target": {"type": "text", "value": "Order Confirmed"}}
        ]
    else:
        steps = [
            {"action": "goto", "target": {"type": "url", "value": target_url or "https://example.com"}},
            {"action": "waitfor", "target": {"type": "selector", "value": "role=main"}, "timeout_ms": 5000}
        ]
    return {"test_id": tid, "description": nl, "steps": steps}

# Public endpoints
@app.post("/generate_scenario")
async def generate_scenario(req: GenerateScenarioRequest):
    scenario = await generate_scenario_from_nl(req.nl, req.target_url)
    await log_event("scenario_generated", {"nl": req.nl, "test_id": scenario.get("test_id")})
    return scenario

@app.post("/run", summary="Run TestIR with auto-repair loop")
async def run(req: RunRequest):
    # register task
    desc = req.test_ir.get("description", "") if isinstance(req.test_ir, dict) else ""
    task_id = task_manager.create_task(desc)
    await task_manager.update_task(task_id, "running")
    await log_event("task_created", {"id": task_id, "desc": desc})

    run_id = req.run_id or f"run_{task_id[:8]}"
    payload = {"run_id": run_id, "test_ir": req.test_ir}

    # attempt execution and auto-repair loop
    max_attempts = Config.RETRY_COUNT + 1
    attempt = 0
    last_error = None
    current_ir = req.test_ir
    while attempt < max_attempts:
        attempt += 1
        await log_event("executor_call", {"task_id": task_id, "attempt": attempt})
        try:
            resp = await call_executor(payload)
        except Exception as e:
            last_error = str(e)
            await log_event("executor_error", {"task_id": task_id, "error": last_error})
            # if executor unreachable, fail
            await task_manager.update_task(task_id, "failed", {"error": last_error})
            raise HTTPException(status_code=502, detail=last_error)

        # executor returns body; if includes status failed, inspect detail
        if isinstance(resp, dict) and resp.get("status") in ("failed", "error"):
            detail = resp.get("detail") or resp
            err = detail.get("error") if isinstance(detail, dict) else str(detail)
            failed_step = detail.get("failed_step") if isinstance(detail, dict) else {}
            artifacts = detail.get("artifacts") if isinstance(detail, dict) else {}

            # record to failure bank
            failure_record = FailureRecord(job_id=run_id, error=str(err), failed_step=failed_step or {}, artifacts=artifacts or {})
            add_failure_to_bank(failure_record)
            await log_event("failure_recorded", {"task_id": task_id, "error": str(err)})

            # if auto_repair enabled, try to get fixes
            if req.auto_repair:
                fixes = await suggest_fixes_from_failure(failure_record)
                await log_event("fixes_proposed", {"task_id": task_id, "fixes": fixes})
                # apply first applicable fix (very conservative: modify step in current_ir)
                applied = False
                for f in fixes:
                    if f.get("type") == "adjust_timeout" and f.get("patched_step"):
                        # find matching step in current_ir and replace
                        for s in current_ir.get("steps", []):
                            if s.get("action") == failed_step.get("action"):
                                s.update(f.get("patched_step"))
                                applied = True
                                break
                    if f.get("type") == "insert_waitfor" and f.get("patched_step"):
                        # insert waitfor before failed step
                        new_steps = []
                        inserted = False
                        for s in current_ir.get("steps", []):
                            if not inserted and s.get("action") == failed_step.get("action"):
                                new_steps.append(f.get("patched_step"))
                                inserted = True
                            new_steps.append(s)
                        if inserted:
                            current_ir["steps"] = new_steps
                            applied = True
                    if f.get("type") == "selector_text_match" and f.get("patched_step"):
                        for s in current_ir.get("steps", []):
                            if s.get("action") == failed_step.get("action"):
                                s.update(f.get("patched_step"))
                                applied = True
                                break
                    if applied:
                        # update payload for next attempt
                        payload = {"run_id": run_id, "test_ir": current_ir}
                        await log_event("fix_applied", {"task_id": task_id, "fix": f})
                        break
                if not applied:
                    await log_event("no_fix_applied", {"task_id": task_id})
                    last_error = err
                    break
                else:
                    # retry loop continues
                    continue
            else:
                # not auto repair -> finish as failed
                await task_manager.update_task(task_id, "failed", {"error": err})
                return {"task_id": task_id, "status": "failed", "error": err}
        else:
            # success
            await task_manager.update_task(task_id, "completed", resp)
            await log_event("task_completed", {"task_id": task_id, "result": resp})
            return {"task_id": task_id, "status": "completed", "result": resp}

    # if loop exits with last_error
    await task_manager.update_task(task_id, "failed", {"error": last_error})
    await log_event("task_failed", {"task_id": task_id, "error": last_error})
    raise HTTPException(status_code=500, detail=str(last_error))

@app.get("/tasks")
async def list_tasks():
    return task_manager.all_tasks()

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
