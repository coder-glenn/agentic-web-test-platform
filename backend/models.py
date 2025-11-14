from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Step(BaseModel):
    id: str
    action: str
    args: Dict[str, Any] = {}
    retry: int = 1
    timeout: Optional[int] = None

class TestIR(BaseModel):
    id: str
    title: Optional[str]
    meta: Dict[str, Any] = {}
    steps: List[Step]

class StepResult(BaseModel):
    id: str
    ok: bool
    error: Optional[str]
    details: Dict[str, Any] = {}

class TestResult(BaseModel):
    id: str
    results: List[StepResult]
    ok: bool
    artifacts: Dict[str, str] = {}
