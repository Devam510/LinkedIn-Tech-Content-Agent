"""
utils/logger.py — Centralised Loguru logger for the LinkedIn agent.
Import `log` from this module in every other module.
"""
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Console: clean, human-readable
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> — {message}",
    colorize=True,
)

# File: full detail, rotating weekly, kept 4 weeks
logger.add(
    "logs/agent.log",
    level="DEBUG",
    rotation="1 week",
    retention="4 weeks",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
)

log = logger
