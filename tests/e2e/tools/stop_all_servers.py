# tests/e2e/tools/stop_all_servers.py

import os
import psutil
import pytest
from tests.e2e.utils.server_state import get_all_server_pids
from tests.e2e.utils.server_manager import stop_all_servers
from tests.e2e.utils.server_manager import ensure_process_stopped

PID_FILE = "/tmp/neuro_san_server.pid"


@pytest.mark.order(-1)
def stop_all_agent_servers():
    """
    Note: run as python <tools name>
    Test case that stops all agent server processes listed in the PID file.

    Verifies:
      ✅ Each PID exists and maps to a running process
      ✅ After stop_all_servers(), the processes are no longer alive
      ✅ The PID file is deleted after shutdown
    """

    # --- Step 1: Load all known PIDs from the shared PID file
    pids = get_all_server_pids()
    assert pids, "❌ No server PIDs recorded — is the server running?"

    # --- Step 2: Verify each PID corresponds to a live server process
    for pid in pids:
        proc = psutil.Process(pid)
        assert proc.is_running(), f"❌ Server process with PID {pid} is not running."
        print(f"🛑 Preparing to stop server with PID {pid}...")

    # --- Step 3: Call the shared stop function to clean up all servers
    stop_all_servers()

    # --- Step 4: Validate each PID is no longer running (process no longer exists)
    for pid in pids:
        success = ensure_process_stopped(pid)
        if success:
            print(f"✅ Confirmed: server process {pid} is terminated.")
        else:
            pytest.fail(f"❌ Failed to stop server PID {pid}.")

    # --- Step 5: Double-check that PID file is removed (optional cleanup)
    assert not os.path.exists(PID_FILE), f"❌ PID file still exists: {PID_FILE}"
    print(f"🧹 PID file successfully removed: {PID_FILE}")


# CLI entrypoint
if __name__ == "__main__":
    stop_all_agent_servers()
