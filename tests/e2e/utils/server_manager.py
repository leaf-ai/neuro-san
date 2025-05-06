# utils/server_manager.py

import subprocess
import sys
import os
import logging
from tests.e2e.utils.server_state import get_all_server_pids
from tests.e2e.utils.logging_config import setup_logging
import psutil

# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------
PID_FILE = "/tmp/neuro_san_server.pid"

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
setup_logging()
logging.info("✅ [SERVER_MANAGER] Logging initialized.")

# --------------------------------------------------------------------
# Start the server
# --------------------------------------------------------------------
def start_server(conn: str):
    """
    Start the agent server as a detached background subprocess.
    Writes PID to a file and updates shared state.
    """
    logging.info(f"🚀 [SERVER] Starting agent service for connection='{conn}'...")

    kwargs = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "close_fds": True
    }

    if os.name == "posix":
        kwargs["start_new_session"] = True
    elif os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(["python", "-m", "neuro_san.service.agent_main_loop"], **kwargs)

    # Save process handle in shared state
    get_all_server_pids.SERVER_PROC = proc
    logging.info(f"✅ [SERVER] Agent started in detached mode. PID={proc.pid}")

    # After starting the subprocess
    logging.info(f"✅ [SERVER] Agent started in detached mode. PID={proc.pid}")
    with open(PID_FILE, "a") as f:
        f.write(f"{proc.pid}\n")
    return proc

# --------------------------------------------------------------------
# Stop all server
# --------------------------------------------------------------------
def stop_all_servers():
    """
    Stop all PIDs listed in the PID file. Clean up the file.
    """

    pids = get_all_server_pids()
    if not pids:
        logging.warning("[SERVER] 🚫 No PIDs to stop.")
        return

    for pid in pids:
        try:
            proc = psutil.Process(pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                logging.info(f"[SERVER] 🛑 Terminating server with PID {pid}...")
                proc.terminate()
                proc.wait(timeout=10)
                logging.info(f"[SERVER] ✅ PID {pid} terminated.")
        except Exception as e:
            logging.warning(f"[SERVER] ⚠️ Failed to stop PID {pid}: {e}")

    # Cleanup
    try:
        os.remove(PID_FILE)
        logging.info(f"[SERVER] 🧹 Removed PID file: {PID_FILE}")
    except Exception as e:
        logging.warning(f"[SERVER] ⚠️ Failed to delete PID file: {e}")

def stop_server_by_pid(pid: int):
    try:
        proc = psutil.Process(pid)
        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
            proc.terminate()
            proc.wait(timeout=10)
            logging.info(f"[SERVER] ✅ Server with PID {pid} terminated.")

        # Remove from PID file
        _remove_pid_from_file(pid)

    except psutil.NoSuchProcess:
        logging.warning(f"[SERVER] ⚠️ PID {pid} does not exist.")
    except Exception as e:
        logging.error(f"[SERVER] ❌ Failed to stop PID {pid}: {e}")


def _remove_pid_from_file(pid: int):
    if not os.path.exists(PID_FILE):
        return
    try:
        with open(PID_FILE, "r") as f:
            pids = [line.strip() for line in f if line.strip() != str(pid)]
        with open(PID_FILE, "w") as f:
            f.write("\n".join(pids) + "\n" if pids else "")
        logging.info(f"[SERVER] 🧹 Removed PID {pid} from file.")
    except Exception as e:
        logging.warning(f"[SERVER] ⚠️ Could not remove PID {pid} from file: {e}")
