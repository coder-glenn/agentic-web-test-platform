# logger_setup.py

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    设置并返回一个 logger，用于整个测试平台记录日志。
    日志将输出至指定文件，并做轮转，以防文件过大。
    """
    # 创建 logs 目录（如果不存在）
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("test_agent_logger")
    logger.setLevel(level)

    # 如果已有 handler，避免重复
    if not logger.handlers:
        # 文件 handler，轮转：10 MB 大小，保留 5 个备份
        fh = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf‑8")
        fh.setLevel(level)

        # 控制台 handler（可选：也输出控制台）
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # 日志格式
        formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)-8s %(message)s [in %(filename)s:%(lineno)d]"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
