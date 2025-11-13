import os
import json
from typing import Dict, Any, List
from datetime import datetime

# Optional LLM
try:
    from langchain import LLMChain, PromptTemplate
    from langchain.llms import OpenAI
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    items = []
    if not os.path.exists(path):
        return items
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def compute_metrics(data_dir: str) -> Dict[str, Any]:
    """Compute basic metrics from agent logs, tasks and failure bank."""
    log_file = os.path.join(data_dir, 'agent.log.jsonl')
    tasks_file = os.path.join(data_dir, 'tasks.jsonl')
    failure_file = os.path.join(data_dir, 'failure_bank.jsonl')

    logs = read_jsonl(log_file)
    tasks = read_jsonl(tasks_file)
    failures = read_jsonl(failure_file)

    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    failed = sum(1 for t in tasks if t.get('status') == 'failed')
    pending = sum(1 for t in tasks if t.get('status') in ('pending','running'))

    # avg duration: use created_at and updated_at if available
    durations = []
    for t in tasks:
        c = t.get('created_at')
        u = t.get('updated_at')
        try:
            if c and u:
                dt = datetime.fromisoformat(u) - datetime.fromisoformat(c)
                durations.append(dt.total_seconds())
        except Exception:
            pass
    avg_duration = sum(durations) / len(durations) if durations else None

    # failure distribution by error text
    err_counts = {}
    for f in failures:
        err = f.get('error') or 'unknown'
        err_counts[err] = err_counts.get(err, 0) + 1

    # recent tasks
    recent = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:20]

    metrics = {
        'total_tasks': total_tasks,
        'completed': completed,
        'failed': failed,
        'pending': pending,
        'avg_duration_seconds': avg_duration,
        'failure_distribution': err_counts,
        'recent_tasks': recent,
        'log_count': len(logs),
        'failure_count': len(failures),
    }
    return metrics


def generate_summary(metrics: Dict[str, Any], openai_api_key: str = None) -> str:
    """Generate a short natural-language summary using an LLM if available, otherwise heuristic."""
    # Heuristic summary
    def heuristic():
        total = metrics.get('total_tasks', 0)
        comp = metrics.get('completed', 0)
        failed = metrics.get('failed', 0)
        avg = metrics.get('avg_duration_seconds')
        top_err = None
        if metrics.get('failure_distribution'):
            top_err = max(metrics['failure_distribution'].items(), key=lambda x: x[1])[0]
        parts = []
        parts.append(f"Total tasks: {total}. Completed: {comp}. Failed: {failed}.")
        if avg:
            parts.append(f"Average task duration: {avg:.1f}s.")
        if top_err:
            parts.append(f"Most common failure: {top_err}.")
        return ' '.join(parts)

    if LANGCHAIN_AVAILABLE and openai_api_key:
        try:
            prompt = (
                "You are an assistant that summarizes QA test run metrics.\n"
                f"Metrics JSON: {json.dumps(metrics)}\n"
                "Produce a 3-4 sentence summary highlighting success rate, trends, and top failure reasons."
            )
            template = PromptTemplate.from_template(prompt)
            llm = OpenAI(openai_api_key=openai_api_key, temperature=0.0)
            chain = LLMChain(llm=llm, prompt=template)
            out = chain.run({})
            return out.strip()
        except Exception:
            return heuristic()
    else:
        return heuristic()
