from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str | Path | None = None) -> logging.Logger:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger("obfuscation_tax")
    logger.setLevel(lvl)
    # avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(lvl)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        if log_file:
            p = Path(log_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(p)
            fh.setLevel(lvl)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
    return logger


def get_logger(name: str = "obfuscation_tax") -> logging.Logger:
    return logging.getLogger(name)
