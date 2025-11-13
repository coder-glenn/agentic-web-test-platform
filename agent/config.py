import os

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    EXECUTOR_URL = os.getenv("EXECUTOR_URL", "http://executor:3000/exec")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "false").lower() == "true"
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    TASK_STATE_FILE = os.path.join(DATA_DIR, "tasks.jsonl")
    LOG_FILE = os.path.join(DATA_DIR, "agent.log.jsonl")
    MAX_PARALLEL_TASKS = int(os.getenv("MAX_PARALLEL_TASKS", "3"))
    RETRY_COUNT = int(os.getenv("RETRY_COUNT", "2"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "3.0"))

# ensure data dir exists
os.makedirs(Config.DATA_DIR, exist_ok=True)
