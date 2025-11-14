# report.py
import time
import json
from typing import List, Dict, Any, Optional
from logger_setup import setup_logger

logger = setup_logger()

class StepRecord:
    def __init__(self, step_description: str):
        self.step_description = step_description
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status: str = "RUNNING"
        self.message: Optional[str] = None
        logger.info(f"[REPORT] Step started: {step_description}")

    def mark_passed(self, message: Optional[str] = None):
        self.end_time = time.time()
        self.status = "PASSED"
        self.message = message
        logger.info(f"[REPORT] Step passed: {self.step_description} – {message}")

    def mark_failed(self, message: Optional[str] = None):
        self.end_time = time.time()
        self.status = "FAILED"
        self.message = message
        logger.error(f"[REPORT] Step failed: {self.step_description} – {message}")

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
        self.overall_status: str = "RUNNING"
        logger.info(f"[REPORT] Created report for: {test_name}")

    def add_step(self, step: StepRecord):
        self.steps.append(step)
        logger.debug(f"[REPORT] Added step: {step.step_description}")

    def mark_finished(self):
        self.end_time = time.time()
        self.overall_status = "PASSED"
        for s in self.steps:
            if s.status == "FAILED":
                self.overall_status = "FAILED"
                break
        logger.info(f"[REPORT] Finished: {self.test_name} status={self.overall_status}, duration={self.duration():.2f}s")

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
        logger.info(f"[REPORT] Saving JSON -> {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def save_markdown(self, path: str):
        logger.info(f"[REPORT] Saving Markdown -> {path}")
        lines = [
            f"# Test Report: {self.test_name}",
            f"- Environment: {self.environment}",
            f"- Start time : {time.ctime(self.start_time)}",
            f"- End time   : {time.ctime(self.end_time) if self.end_time else 'N/A'}",
            f"- Duration   : {self.duration():.2f} sec",
            f"- Overall status: **{self.overall_status}**",
            "",
            "## Steps",
        ]
        for idx, s in enumerate(self.steps, start=1):
            lines += [
                f"### Step {idx}: {s.step_description}",
                f"- Status   : {s.status}",
                f"- Duration : {s.duration():.2f} sec",
            ]
            if s.message:
                lines.append(f"- Message  : {s.message}")
            lines.append("")
        content = "\n".join(lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def save_html(self, path: str):
        logger.info(f"[REPORT] Saving HTML -> {path}")
        html_lines = [
            "<html><head><meta charset='utf-8'><title>Test Report</title></head><body>",
            f"<h1>Test Report: {self.test_name}</h1>",
            f"<p><strong>Environment:</strong> {self.environment}</p>",
            f"<p><strong>Start time:</strong> {time.ctime(self.start_time)}</p>",
            f"<p><strong>End time:</strong> {time.ctime(self.end_time) if self.end_time else 'N/A'}</p>",
            f"<p><strong>Duration:</strong> {self.duration():.2f} sec</p>",
            f"<p><strong>Overall status:</strong> <strong style='color:{'green' if self.overall_status=='PASSED' else 'red'}'>{self.overall_status}</strong></p>",
            "<h2>Steps</h2>",
        ]
        for idx, s in enumerate(self.steps, start=1):
            html_lines += [
                f"<h3>Step {idx}: {s.step_description}</h3>",
                "<ul>",
                f"<li><strong>Status:</strong> {s.status}</li>",
                f"<li><strong>Duration:</strong> {s.duration():.2f} sec</li>",
            ]
            if s.message:
                html_lines.append(f"<li><strong>Message:</strong> {s.message}</li>")
            html_lines.append("</ul>")
        html_lines.append("</body></html>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))
