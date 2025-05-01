import subprocess
import time
from contextlib import contextmanager


def start_server():
    """
    Start the agent server as a subprocess.

    Returns:
        subprocess.Popen: The running process object.
    """
    print("[INFO] Starting agent server: neuro_san.service.agent_main_loop")

    # Start the service as a background subprocess
    proc = subprocess.Popen(
        ["python", "-m", "neuro_san.service.agent_main_loop", "--port", "30011"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Optional: wait briefly for the server to initialize (adjust if needed)
    time.sleep(5)

    return proc


def stop_server(proc):
    """
    Stop a running agent server subprocess.

    Args:
        proc (subprocess.Popen): The process to terminate.
    """
    if proc:
        print("[INFO] Terminating agent server process")
        proc.terminate()
        proc.wait()
        print("[INFO] Server process stopped")


@contextmanager
def agent_server():
    """
    Context manager for running the agent server service in the background.

    This is the preferred way to manage the server lifecycle in tests.
    Automatically handles startup and cleanup of the process.

    Usage:
        with agent_server():
            # run CLI or client code that depends on the server
    """
    proc = start_server()
    try:
        yield proc  # Yield control back to the test logic
    finally:
        stop_server(proc)
