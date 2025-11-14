# logger_setup.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_file: str = "logs/test_agent.log", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger("test_agent_logger")
    logger.setLevel(level)
    if not logger.handlers:
        fh = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)-8s %(message)s [in %(filename)s:%(lineno)d]")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger
