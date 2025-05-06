import os

# Path to the PID file where server PIDs are stored (one per line)
PID_FILE = "/tmp/neuro_san_server.pid"


def get_all_server_pids():
    """
    Reads the PID file and returns a list of all recorded PIDs.
    Each line in the file is expected to be a valid integer PID.

    Returns:
        List[int]: All valid PIDs in the file.
        []: Empty list if file is missing or has no valid entries.
    """
    if not os.path.exists(PID_FILE):
        return []

    with open(PID_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]


def get_last_server_pid():
    """
    Returns the most recently recorded (last) PID from the PID file.

    This is useful when only the latest server process matters
    (e.g., stopping the last started service).

    Returns:
        int: The last PID in the file.
        None: If the file doesn't exist or is empty.
    """
    pids = get_all_server_pids()
    return pids[-1] if pids else None
