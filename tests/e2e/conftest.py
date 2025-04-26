# conftest.py
# ------------------------------------------------------------------------
# Pytest configuration for MusicNerdPro tests.
# Provides custom CLI flags, dynamic test generation, and environment setup.
# ------------------------------------------------------------------------

import pytest
import os
from pyhocon import ConfigFactory

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Directory where agent CLI thinking files will be written (optional feature)
THINKING_FILE_PATH = "/private/tmp/agent_thinking"

# Static agent config (HOCON) loaded once for all tests
CONFIG_HOCON_PATH = os.path.join(os.path.dirname(__file__), "configs", "config.hocon")
config = ConfigFactory.parse_file(CONFIG_HOCON_PATH)

# ------------------------------------------------------------------------------
# Hooks
# ------------------------------------------------------------------------------

def pytest_configure(config):
    """
    Prints custom environment info when pytest starts.
    Helps verify environment settings.
    """
    print("\nCustom Environment Info")
    print(f"thinking-file path      : {THINKING_FILE_PATH}")

def pytest_addoption(parser):
    """
    Adds custom command-line options for pytest to control the test suite:
    --connection    -> Filter tests by specific connection method (direct/grpc/http)
    --repeat        -> Repeat the same test multiple times (for stability/reliability)
    --thinking-file -> Enable writing out agent thinking_file logs during test
    """
    group = parser.getgroup("custom options")
    group.addoption(
        "--connection",
        action="store",
        default=None,
        help="Specify a connection name to test (e.g., direct, grpc, http). If omitted, all will be tested."
    )
    group.addoption(
        "--repeat",
        action="store",
        type=int,
        default=1,
        help="Number of times to repeat each test (for stress or reliability testing)."
    )
    group.addoption(
        "--thinking-file",
        action="store_true",
        default=False,
        help="If enabled, agent will write a thinking_file log per test case (grpc/http/direct)."
    )

def pytest_generate_tests(metafunc):
    """
    Dynamically parameterizes the tests based on the connection(s) and repetition requested.

    Example:
    --connection grpc --repeat 3
    → Runs 3 tests against 'grpc' connection.

    --repeat 2 (with no connection)
    → Runs 2 tests for each connection (direct, grpc, http).

    This auto-expands into (connection_name, repeat_index) fixture pairs.
    """
    if "connection_name" in metafunc.fixturenames:
        all_connections = load_connections()
        selected_connection = metafunc.config.getoption("connection")
        repeat = metafunc.config.getoption("repeat")

        # Filter if a specific connection is selected
        if selected_connection:
            if selected_connection not in all_connections:
                raise ValueError(f"Connection '{selected_connection}' not found in config: {all_connections}")
            all_connections = [selected_connection]

        # Generate combinations of (connection_name, repeat_index)
        test_params = [
            pytest.param(conn, i, id=f"{conn}_run{i+1}")
            for conn in all_connections
            for i in range(repeat)
        ]

        # Parametrize the test function
        metafunc.parametrize("connection_name, repeat_index", test_params)

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------

def load_connections():
    """
    Loads the list of supported connection names from the static config file.
    """
    return config.get("connection")

