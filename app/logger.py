import logging
import sys
from datetime import datetime


def setup_logger():
    logger = logging.getLogger("pincode_api")
    logger.setLevel(logging.INFO)

    # avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    # ─── Console Handler ──────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # ─── File Handler ─────────────────────────────────────
    log_filename = f"logs/app.log"
    import os

    os.makedirs("logs", exist_ok=True)

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # ─── Format ───────────────────────────────────────────
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# single instance used across entire app
logger = setup_logger()
