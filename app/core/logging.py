"""Logging configuration: console + rotating file."""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    if root.handlers:
        return
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(fmt)
    root.addHandler(console)
    root.addHandler(file_handler)
