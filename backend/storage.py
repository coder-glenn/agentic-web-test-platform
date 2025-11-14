import os, json
from .models import TestResult
class Storage:
    def __init__(self, base='data'):
        self.base = base
        os.makedirs(self.base, exist_ok=True)
    async def save_result(self, result: TestResult):
        path = os.path.join(self.base, f'{result.id}.json')
        with open(path, 'w', encoding='utf8') as f:
            json.dump(result.dict(), f, ensure_ascii=False, indent=2)
    async def load_result(self, id: str) -> TestResult:
        path = os.path.join(self.base, f'{id}.json')
        with open(path, 'r', encoding='utf8') as f:
            data = json.load(f)
        return TestResult(**data)
