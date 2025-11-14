import os
from .models import TestIR, Step
# For prototype, we implement a simple rule-based planner if LLM is not configured.
try:
    from langchain.llms import OpenAI
except Exception:
    OpenAI = None

PROMPT_TEMPLATE = '''
把下面的自然语言需求拆成可执行的测试步骤（IR），用 YAML 或 JSON 的 steps 列表表达。
需求: {nl}
每步要包含: id, action (goto/click/type/wait/assert/screenshot/eval), args
'''

class Planner:
    def __init__(self, llm=None):
        self.llm = llm
    def plan(self, nl_request: str) -> TestIR:
        # If an LLM is configured, try to call it. Otherwise create a simple example IR.
        if self.llm:
            prompt = PROMPT_TEMPLATE.format(nl=nl_request)
            try:
                resp = self.llm(prompt)
                import yaml
                parsed = yaml.safe_load(resp)
                return TestIR(**parsed)
            except Exception:
                pass
        # fallback simple IR for demo
        ir = TestIR(
            id='ir_' + str(abs(hash(nl_request)) % (10**8)),
            title=nl_request,
            meta={'browser': 'chromium'},
            steps=[
                Step(id='s1', action='goto', args={'url': 'https://playwright.dev/'}),
                Step(id='s2', action='click', args={'selector': 'text=Docs'}),
                Step(id='s3', action='screenshot', args={'path': 'artifacts/{}/after_docs.png'.format('ir_demo')}),
            ]
        )
        return ir
