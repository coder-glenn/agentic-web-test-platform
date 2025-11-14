
import asyncio, os, json
from .models import TestIR, StepResult, TestResult
from .adapters.playwright_adapter import PlaywrightAdapter
from .storage import Storage

class Executor:
    def __init__(self, storage: Storage, adapter=None, ws_manager=None):
        self.adapter = adapter or PlaywrightAdapter()
        self.storage = storage
        self.ws_manager = ws_manager  # ConnectionManager from app.state

    async def _send(self, run_id: str, payload: dict):
        try:
            if self.ws_manager:
                await self.ws_manager.send_log(run_id, payload)
        except Exception:
            pass

    async def run_ir(self, ir: TestIR) -> TestResult:
        session_id = ir.id
        # ensure artifacts path exists inside backend/artifacts/<run_id>
        base_art = os.path.join(os.path.dirname(__file__), 'artifacts', session_id)
        os.makedirs(base_art, exist_ok=True)

        await self._send(session_id, {'type':'run_start', 'message':f'Run {session_id} started'})
        await self.adapter.new_session(session_id, browser=ir.meta.get('browser', 'chromium'))
        results = []
        ok = True
        for step in ir.steps:
            await self._send(session_id, {'type':'step_start', 'step':step.id, 'action':step.action, 'args':step.args})
            try:
                # if screenshot step has relative path, make it under backend/artifacts/<run_id>/...
                if step.action == 'screenshot' and 'path' in (step.args or {}):
                    # normalize path into backend/artifacts/<run_id>/<basename>
                    orig = step.args.get('path')
                    basename = os.path.basename(orig)
                    new_path = os.path.join('artifacts', session_id, basename)
                    # adapter expects relative path; but we pass absolute path
                    abs_path = os.path.join(os.path.dirname(__file__), new_path)
                    step.args['path'] = abs_path
                r = await self._run_step(session_id, step)
                results.append(r)
                await self._send(session_id, {'type':'step_end', 'step':step.id, 'ok':r.ok, 'error':r.error})
                if step.action == 'screenshot' and r.ok:
                    # construct public URL
                    public_url = f'/artifacts/{session_id}/{os.path.basename(step.args.get("path"))}'
                    await self._send(session_id, {'type':'artifact', 'step':step.id, 'url': public_url})
                if not r.ok:
                    ok = False
                    break
            except Exception as e:
                results.append(StepResult(id=step.id, ok=False, error=str(e)))
                await self._send(session_id, {'type':'step_error', 'step':step.id, 'error':str(e)})
                ok = False
                break
        artifacts = {}
        result = TestResult(id=ir.id, results=results, ok=ok, artifacts=artifacts)
        await self.storage.save_result(result)
        await self.adapter.close_session(session_id)
        await self._send(session_id, {'type':'run_end', 'ok':ok})
        return result

    async def _run_step(self, session_id: str, step) -> StepResult:
        action = step.action
        args = step.args or {}
        try:
            if action == 'goto':
                await self.adapter.goto(session_id, args['url'])
            elif action == 'click':
                await self.adapter.click(session_id, args['selector'])
            elif action == 'type':
                await self.adapter.type(session_id, args['selector'], args['text'])
            elif action == 'screenshot':
                path = args.get('path', f'artifacts/{session_id}/{step.id}.png')
                # Ensure parent dir exists
                os.makedirs(os.path.dirname(path), exist_ok=True)
                await self.adapter.screenshot(session_id, path)
            elif action == 'assert':
                html = await self.adapter.get_dom_snapshot(session_id)
                if args.get('selector') and args.get('mode') == 'contains':
                    if args['selector'].replace('text=', '') not in html:
                        return StepResult(id=step.id, ok=False, error='assert contains failed')
            else:
                pass
            return StepResult(id=step.id, ok=True, error=None)
        except Exception as e:
            return StepResult(id=step.id, ok=False, error=str(e))
