# tests/e2e/tools/stop_last_server.py

import os
import psutil
import pytest
from tests.e2e.utils import server_state
from tests.e2e.utils.server_manager import stop_server_by_pid


PID_FILE = "/tmp/neuro_san_server.pid"

def stop_last_agent_server():
    """
    Note: run as python <tools name>
    Stops only the most recently started server process recorded in the PID file.

    Verifies:
      ✅ Last PID is valid and running
      ✅ That specific process is terminated
      ✅ Remaining PIDs (if any) are untouched
    """

    # --- Step 1: Load all recorded PIDs
    all_pids = server_state.get_all_server_pids()
    assert all_pids, "❌ No server PIDs found. Is the server running?"

    # --- Step 2: Target the last one (most recent)
    last_pid = all_pids[-1]
    print(f"🛑 Preparing to stop last server with PID: {last_pid}")

    # --- Step 3: Confirm it's running before stopping
    proc = psutil.Process(last_pid)
    assert proc.is_running(), f"❌ Process {last_pid} is not running."

    # --- Step 4: Stop that specific server
    stop_server_by_pid(last_pid)

    # --- Step 5: Confirm it's gone
    with pytest.raises(psutil.NoSuchProcess):
        psutil.Process(last_pid)
    print(f"✅ Server PID {last_pid} successfully terminated.")

    # --- Step 6: Confirm PID file still exists and contains other PIDs (if applicable)
    remaining = [pid for pid in all_pids if pid != last_pid]
    current = server_state.get_all_server_pids()

    if not remaining and os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        print(f"🧹 PID file cleaned up: {PID_FILE}")
    elif not remaining:
        print(f"🧹 No remaining PIDs. PID file was already cleaned up.")
    else:
        assert current == remaining, f"❌ PID file mismatch. Expected {remaining}, got {current}"
        print(f"ℹ️ Remaining PIDs still active: {current}")

# CLI entrypoint
if __name__ == "__main__":
    stop_last_agent_server()