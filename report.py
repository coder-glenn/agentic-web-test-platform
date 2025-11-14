# report.py

import time
import json
import os
from typing import List, Dict, Any, Optional

from logger_setup import setup_logger

logger = setup_logger("logs/test_agent.log", level=logging.INFO)

class StepRecord:
    def __init__(self, step_description: str):
        self.step_description = step_description
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status: str = "RUNNING"  # RUNNING, PASSED, FAILED
        self.message: Optional[str] = None
        logger.info(f"Step started: {step_description}")

    def mark_passed(self, message: Optional[str] = None):
        self.end_time = time.time()
        self.status = "PASSED"
        self.message = message
        logger.info(f"Step passed: {self.step_description} – message: {message}")

    def mark_failed(self, message: Optional[str] = None):
        self.end_time = time.time()
        self.status = "FAILED"
        self.message = message
        logger.error(f"Step failed: {self.step_description} – message: {message}")

    def duration(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_description": self.step_description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_sec": self.duration(),
            "status": self.status,
            "message": self.message,
        }

class TestReport:
    def __init__(self, test_name: str, environment: str = ""):
        self.test_name = test_name
        self.environment = environment
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.steps: List[StepRecord] = []
        self.overall_status: str = "RUNNING"  # RUNNING, PASSED, FAILED
        logger.info(f"Test report created: {test_name}, environment: {environment}")

    def add_step(self, step: StepRecord):
        self.steps.append(step)
        logger.debug(f"Added step: {step.step_description}")

    def mark_finished(self):
        self.end_time = time.time()
        # overall status: if any step FAILED => FAILED, else PASSED
        self.overall_status = "PASSED"
        for s in self.steps:
            if s.status == "FAILED":
                self.overall_status = "FAILED"
                break
        logger.info(f"Test {self.test_name} finished with status: {self.overall_status} – duration {self.duration():.2f} sec")

    def duration(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "environment": self.environment,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_sec": self.duration(),
            "overall_status": self.overall_status,
            "steps": [s.to_dict() for s in self.steps],
        }

    def save_json(self, path: str):
        logger.info(f"Saving JSON report to {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def save_markdown(self, path: str):
        logger.info(f"Saving Markdown report to {path}")
        lines = []
        lines.append(f"# Test Report: {self.test_name}")
        lines.append(f"- Environment: {self.environment}")
        lines.append(f"- Start time : {time.ctime(self.start_time)}")
        lines.append(f"- End time   : {time.ctime(self.end_time)}")
        lines.append(f"- Duration   : {self.duration():.2f} sec")
        lines.append(f"- Overall status: **{self.overall_status}**")
        lines.append("")
        lines.append("## Steps")
        for idx, s in enumerate(self.steps, start=1):
            lines.append(f"### Step {idx}: {s.step_description}")
            lines.append(f"- Status   : {s.status}")
            lines.append(f"- Duration : {s.duration():.2f} sec")
            if s.message:
                lines.append(f"- Message  : {s.message}")
            lines.append("")
        content = "\n".join(lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def save_html(self, path: str):
        logger.info(f"Saving HTML report to {path}")
        html_lines = []
        html_lines.append(f"<html><head><meta charset='utf-8'><title>Test Report: {self.test_name}</title></head><body>")
        html_lines.append(f"<h1>Test Report: {self.test_name}</h1>")
        html_lines.append(f"<p><strong>Environment:</strong> {self.environment}</p>")
        html_lines.append(f"<p><strong>Start time:</strong> {time.ctime(self.start_time)}</p>")
        html_lines.append(f"<p><strong>End time:</strong> {time.ctime(self.end_time)}</p>")
        html_lines.append(f"<p><strong>Duration:</strong> {self.duration():.2f} sec</p>")
        html_lines.append(f"<p><strong>Overall status:</strong> <span style='font-weight:bold;color:{'green' if self.overall_status=='PASSED' else 'red'}'>{self.overall_status}</span></p>")
        html_lines.append("<h2>Steps</h2>")
        for idx, s in enumerate(self.steps, start=1):
            html_lines.append(f"<h3>Step {idx}: {s.step_description}</h3>")
            html_lines.append(f"<ul>")
            html_lines.append(f"<li><strong>Status:</strong> {s.status}</li>")
            html_lines.append(f"<li><strong>Duration:</strong> {s.duration():.2f} sec</li>")
            if s.message:
                html_lines.append(f"<li><strong>Message:</strong> {s.message}</li>")
            html_lines.append(f"</ul>")
        html_lines.append("</body></html>")
        content = "\n".join(html_lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

