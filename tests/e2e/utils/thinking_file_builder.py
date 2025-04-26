# utils/thinking_file_builder.py
# ---------------------------------------------------------
# Thinking File Builder
# ---------------------------------------------------------
# Utility to dynamically generate the optional --thinking_file
# argument used by the agent CLI testing.
# Handles correct directory creation and naming based on
# connection type and repeat index.
# ---------------------------------------------------------

import os

# Root directory where all thinking_file outputs are stored
THINKING_FILE_DIR = "/private/tmp/agent_thinking"


def build_thinking_file_arg(conn: str, repeat_index: int, use_thinking_file: bool) -> str:
    """
    Builds the --thinking_file CLI argument if applicable.

    Rules:
    - Only apply --thinking_file if the connection type is 'grpc', 'http', or 'direct'.
    - If --thinking-file flag is not set (user didn't pass it), no thinking_file will be attached.
    - Ensures the /private/tmp/agent_thinking folder exists before use.
    - Each thinking_file is uniquely named using connection + repeat index.

    Args:
        conn (str): Connection type, e.g., 'grpc', 'http', or 'direct'.
        repeat_index (int): Zero-based repeat index (e.g., 0 for first run).
        use_thinking_file (bool): Whether user requested thinking_file via CLI.

    Returns:
        str: A formatted CLI-ready string for --thinking_file argument.
             Example: " --thinking_file /private/tmp/agent_thinking/grpc_run1"
             If not applicable, returns an empty string "".
    """

    # If user didn't enable thinking_file, skip entirely
    if not use_thinking_file:
        return ""

    # Only certain connection types require thinking_file
    if conn not in ("grpc", "http", "direct"):
        return ""

    # Ensure the thinking file output directory exists
    os.makedirs(THINKING_FILE_DIR, exist_ok=True)

    # Create a unique path for this thinking file
    thinking_path = f"{THINKING_FILE_DIR}/{conn}_run{repeat_index + 1}"

    # Print the thinking path to stdout for debug visibility
    print(f"[thinking_file] → {thinking_path}", flush=True)

    # Return the CLI-ready argument string
    return f" --thinking_file {thinking_path}"