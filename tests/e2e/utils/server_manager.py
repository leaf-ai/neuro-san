import subprocess
import os
import sys
import time
import logging
from contextlib import contextmanager

LOG_PATH = os.path.abspath("/tmp/e2e_server.log")  # <- safe, visible location

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)


def start_server():
    """
    Start the agent server as a subprocess.

    Returns:
        subprocess.Popen: The running process object.
    """
    logging.info("🚀 [SERVER] Starting agent service...")
    """
    #print("[INFO] Starting agent server: neuro_san.service.agent_main_loop")

    # Start the service as a background subprocess
    """
    proc = subprocess.Popen(
        ["python", "-m", "neuro_san.service.agent_main_loop"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Optional: wait briefly for the server to initialize (adjust if needed)
    time.sleep(2)
    logging.info("✅ [SERVER] Agent service started.")
    return proc


def stop_server(proc):
    """
    Stop a running agent server subprocess.

    Args:
        proc (subprocess.Popen): The process to terminate.
    """
    if proc:
        # print("[INFO] Terminating agent server process")
        logging.info("🛑 [SERVER] Stopping agent service...")
        proc.terminate()
        proc.wait()
        logging.info("✅ [SERVER] Agent service stopped.")
        logging.shutdown()  # ✅ Flush all logging buffers
        sys.stdout.flush()  # ✅ Ensure everything gets written


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
