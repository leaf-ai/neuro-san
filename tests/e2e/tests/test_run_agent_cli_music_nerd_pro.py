# test_run_agent_cli_music_nerd_pro.py

# -------------------------------------------------------------------------
# ⚠️ IMPORTANT:
# - This test requires the agent server to be manually started **before** running.
# - It will NOT start or stop the server on its own.
# - This file is excluded from default test discovery by `pytest_ignore_collect()` in conftest.py.
# - This test is executed as part of `tools/smoke_test_runner.py` (not a standalone smoke test).
# -------------------------------------------------------------------------

import pytest
import logging
from tests.e2e.utils.music_nerd_pro_hocon_loader import extract_test_values
from tests.e2e.utils.music_nerd_pro_runner import runner
from tests.e2e.utils.logging_config import setup_logging

# Initialize consistent logging across CLI tools and tests
setup_logging()


@pytest.mark.e2e
@pytest.mark.timeout(120)  # Ensure no single run hangs too long
def test_run_cli_smoke(connection_name, repeat_index, request):
    """
    Full E2E CLI agent test for the music_nerd_pro agent.

    Features:
    - Parametrized across connection types (e.g., direct, grpc, http)
    - Can be repeated N times using --repeat
    - Optionally logs intermediate agent "thinking" to disk using --thinking-file

    Example Invocation (used inside smoke_test_runner.py):
        pytest tests/e2e/tests/test_run_agent_cli_music_nerd_pro.py \
            --connection grpc --repeat 2 --thinking-file -n 1
    """

    # Log current run context (repeat, parallel mode)
    repeat = request.config.getoption('repeat')
    is_parallel = hasattr(request.config, 'workerinput')
    logging.info(f"🧪 Test mode: repeat={repeat}, parallel={is_parallel}")

    # Whether to emit 'thinking file' logs
    use_thinking_file = request.config.getoption("--thinking-file")

    # Extract input values for the specific connection type
    result = extract_test_values(connection_name)
    assert result is not None, f"❌ Could not load test data for connection '{connection_name}'"

    # Run the test for this connection and repeat index
    runner(*result, repeat_index, use_thinking_file)
