# test_music_nerd_pro.py
# ---------------------------------------------------------
# Parametrized test case that drives CLI interaction test
# ---------------------------------------------------------

import pytest
from utils.mnpt_hocon_loader import extract_test_values
from utils.mnpt_test_runner import run_test

@pytest.mark.timeout(120)
def test_run_connection(connection_name, repeat_index, request):
    """
    Main test entry point for testing music_nerd_pro agent over various connections.
    """
    use_thinking_file = request.config.getoption("--thinking-file")
    
    # NEW: Only pass connection name
    result = extract_test_values(connection_name)
    
    run_test(*result, repeat_index, use_thinking_file)

