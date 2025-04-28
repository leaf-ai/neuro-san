# test_music_nerd_pro.py
# ---------------------------------------------------------
# Parametrized E2E test case that drives CLI interaction tests
# ---------------------------------------------------------

import pytest
from utils.mnpt_hocon_loader import extract_test_values
from utils.mnpt_test_runner import run_test


@pytest.mark.e2e
@pytest.mark.timeout(120)
def test_run_connection(connection_name, repeat_index, request):
    """
    End-to-end test for the music_nerd_pro agent across different connections.

    This test:
    - Dynamically parametrizes across multiple connections (e.g., direct, grpc, http).
    - Supports repeated test runs via `repeat_index`.
    - Optionally uses a 'thinking file' if the --thinking-file pytest option is passed.
    """

    # Retrieve custom CLI option for thinking file usage
    use_thinking_file = request.config.getoption("--thinking-file")

    # Extract required test values for the given connection
    result = extract_test_values(connection_name)

    # Defensive check (optional but good practice)
    assert result is not None, f"Failed to extract test values for connection: {connection_name}"

    # Execute the CLI-based test
    run_test(*result, repeat_index, use_thinking_file)
