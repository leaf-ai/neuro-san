# conftest.py

# ------------------------------------------------------------------------
# Pytest configuration for shared CLI options, dynamic test generation,
# session-wide logging setup, and agent server lifecycle management.
# ------------------------------------------------------------------------

import pytest
import os
import logging
from pyhocon import ConfigFactory
from pathlib import Path
from utils.logging_config import setup_logging, DEFAULT_LOG_PATH
setup_logging()  # Make sure logger is initialized


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

THINKING_FILE_PATH = "/private/tmp/agent_thinking"
LOG_PATH = DEFAULT_LOG_PATH  # shared with logging_config
NAME_CONFIG_HOCON = "share_agent_config"

# ------------------------------------------------------------------------------
# One-time Log Cleanup + Logging Setup
# ------------------------------------------------------------------------------

try:
    # Truncate the log file for a clean start (don't delete it)
    open(LOG_PATH, "w").close()

    print(f"[setup] Truncated log file: {LOG_PATH}")
except Exception as e:
    print(f"[setup] WARNING: Could not prepare log file: {e}")


# Initialize shared logging (both file and console)
setup_logging(log_path=LOG_PATH)
logging.info("✅ Logging system initialized by conftest.py")

# ------------------------------------------------------------------------------
# Load Static Agent Configuration (HOCON)
# ------------------------------------------------------------------------------

CONFIG_HOCON_PATH = os.path.join(os.path.dirname(__file__), "configs", NAME_CONFIG_HOCON + ".hocon")

config = ConfigFactory.parse_file(CONFIG_HOCON_PATH)

# ------------------------------------------------------------------------------
# Pytest Hooks
# ------------------------------------------------------------------------------


def pytest_ignore_collect(collection_path: Path, config):
    """
    Prevents pytest from collecting a specific test file during discovery.

    This is used to ignore test_agent_cli_music_nerd_pro.py during normal pytest runs,
    because:
    - It depends on a pre-started server (via start_server_manual.py)
    - It is intended to be run only as part of tools/smoke_test_runner.py
    - This helps avoid accidental test failures or unwanted execution

    Note: Uses pathlib.Path as required by pytest 9+ (fix for PytestRemovedIn9Warning).
    """
    return "test_agent_cli_music_nerd_pro.py" in str(collection_path)


def pytest_configure(config):
    """
    Pytest hook: called once at the start of the test session.
    This function logs useful context about the test configuration.

    - Logs the repeat count from `--repeat` CLI option (default = 1)
    - Detects if pytest-xdist is enabled (i.e., running in parallel)
    """
    # Fetch repeat count from command-line option or default to 1
    repeat = config.getoption("repeat", default=1)

    # Check if we are in a worker process (i.e., xdist parallel run)
    is_parallel = hasattr(config, "workerinput")

    # Emit a log entry showing test mode
    logging.info(f"🧪 Test mode: repeat={repeat}, parallel={is_parallel}")
    logging.info("Custom Environment Info")
    logging.info(f"thinking-file path      : {THINKING_FILE_PATH}")


def pytest_addoption(parser):
    """
    Defines CLI options:
    --connection: Limit tests to a specific connection (e.g., direct/grpc/http)
    --repeat: Repeat each test multiple times
    --thinking-file: Enables optional thinking_file logging
    """
    group = parser.getgroup("custom options")
    group.addoption("--connection", action="store", default=None,
                    help="Specify a connection to test: direct, grpc, or http.")
    group.addoption("--repeat", action="store", type=int, default=1,
                    help="Number of times to repeat each test.")
    group.addoption("--thinking-file", action="store_true", default=False,
                    help="Enable thinking_file output per test run.")


def pytest_generate_tests(metafunc):
    # 🛑 Skip parametrization if running the orchestrator module
    if metafunc.module.__name__.endswith("test_e2e_mnp"):
        return

    if "connection_name" in metafunc.fixturenames:
        all_connections = load_connections()
        selected = metafunc.config.getoption("connection")
        repeat = metafunc.config.getoption("repeat")

        if selected:
            if selected not in all_connections:
                raise ValueError(f"Connection '{selected}' not in config: {all_connections}")
            all_connections = [selected]

        test_params = [
            pytest.param(conn, i, id=f"{conn}_run{i+1}")
            for conn in all_connections
            for i in range(repeat)
        ]

        metafunc.parametrize("connection_name, repeat_index", test_params)


def load_connections():
    """
    Returns the list of connections from the test config.
    """
    return config.get("connection")
