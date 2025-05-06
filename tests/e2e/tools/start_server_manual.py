# tests/e2e/tools/start_server_manual.py

import psutil
from tests.e2e.utils import server_manager, server_state


def start_server_and_sets_pid():
    """
    Note: run as python <tools name>
    Test that the server starts and the global SERVER_PROC is assigned.
    Also verifies that the process is alive using psutil.
    """

    # Start the server using the test connection type
    conn = "grpc"  # or "http" or whatever is valid in your config
    proc = server_manager.start_server(conn)

    # Store the reference globally for access in other tests
    server_state.SERVER_PROC = proc

    # Verify server process object
    pids = server_state.get_all_server_pids()
    assert pids, "❌ No PIDs found in PID file."
    pid = pids[-1]  # use the latest one

    print(f"🧪 Server PIDs: {pids}")
    print(f"🧪 Server started with PID: {pid}")

    # Check that the process is alive
    ps_proc = psutil.Process(pid)
    assert ps_proc.is_running(), "❌ Server process is not running."
    assert ps_proc.status() != psutil.STATUS_ZOMBIE, "❌ Server process is a zombie."

    print(f"✅ Server is running (status: {ps_proc.status()})")


# CLI entrypoint
if __name__ == "__main__":
    start_server_and_sets_pid()
