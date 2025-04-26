# ------------------------------------------------------------------------
# mnpt_hocon_loader.py
# ------------------------------------------------------------------------
# Utility functions for loading test prompt/response values from HOCON files.
# Separates test data loading from agent configuration loading.
# ------------------------------------------------------------------------

import os
from pyhocon import ConfigFactory

# ------------------------------------------------------------------------
# Path to the TEST DATA HOCON file
# - This file contains input prompts and expected agent outputs.
# - NOTE: Only test cases, no agent config.
# ------------------------------------------------------------------------

TEST_DATA_HOCON_PATH = os.path.join(
    os.path.dirname(__file__),        # This utils/ folder
    "../test_cases_data/mnpt_data.hocon"  # Relative path to test_cases/
)

# ------------------------------------------------------------------------
# Load the test data once at import time
# ------------------------------------------------------------------------
test_data = ConfigFactory.parse_file(os.path.abspath(TEST_DATA_HOCON_PATH))

# ------------------------------------------------------------------------
# Function: extract_test_values
# Description:
#   - Loads the prompts and expected answer keywords/costs
#   - Validates the connection name if needed
#   - Returns extracted values for CLI interaction testing
# ------------------------------------------------------------------------

def extract_test_values(connection_name):
    """
    Loads test prompts and expected outputs for a given connection
    from the test data HOCON file.

    Args:
        connection_name (str): The type of connection to validate (e.g., "grpc", "http")

    Returns:
        tuple: (connection_name, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2, input_done)
    """

    # If you want to validate connection types, you can add here
    # Example connection list: ["direct", "grpc", "http"]

    # Pull the list of test prompts and expected outputs
    test_entries = test_data.get("test")

    # Extract the first test input
    input_1 = next(item["input_1"] for item in test_entries if "input_1" in item)
    prompt_1 = input_1.get("user_text")
    word_1 = input_1.get("answer.word")
    cost_1 = input_1.get("answer.cost")

    # Extract the second test input
    input_2 = next(item["input_2"] for item in test_entries if "input_2" in item)
    prompt_2 = input_2.get("user_text")
    word_2 = input_2.get("answer.word")
    cost_2 = input_2.get("answer.cost")

    # Extract the input for termination (e.g., "quit")
    input_done = next((item.get("input_done") for item in test_entries if "input_done" in item), None)

    # Return all values required for the test runner
    return connection_name, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2, input_done