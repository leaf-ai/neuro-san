# utils/logging_config.py

import logging
import os

# ------------------------------------------------------------------------
# Shared Logging Setup for E2E Tests and CLI Runners
# ------------------------------------------------------------------------

# Default path to the shared log file
DEFAULT_LOG_PATH = os.path.abspath("/tmp/e2e_server.log")


def setup_logging(log_path=DEFAULT_LOG_PATH):
    """
    Initializes the logging system used across tests and CLI tools.

    Args:
        log_path (str): Path to the log file (optional override).

    Behavior:
    - Logs messages to both the specified file and the console.
    - Applies a consistent format across all outputs.
    - Safe to call multiple times — will only initialize once.

    Usage:
        setup_logging()                           # use default path
        setup_logging(log_path="/tmp/custom.log") # use custom path
    """
    logger = logging.getLogger()

    # 🔧 Clear any existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
