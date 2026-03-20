"""
logger.py
---------
Colored console logging for the job application crew.
"""

import logging
import colorlog
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "../../logs/crew.log")


def get_logger(name: str = "JobCrew") -> logging.Logger:
    """Get a nicely formatted, colored logger."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Console handler (colored)
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(name)s] %(levelname)s%(reset)s: %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        ))
        logger.addHandler(console_handler)

        # File handler (plain text)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        ))
        logger.addHandler(file_handler)

    return logger
