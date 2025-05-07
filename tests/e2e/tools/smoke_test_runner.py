# tools/smoke_test_runner.py

import subprocess

print("\n# 1. Start server")
subprocess.run(["python", "tests/e2e/tools/start_server_manual.py"], check=True)

print("\n# 2. Run tests")
subprocess.run([
    "pytest",
    "tests/e2e/tests/test_run_agent_cli_music_nerd_pro.py",
    "--capture=no",
    "--thinking-file",
    "--repeat", "1",
    "-n", "auto"
], check=True)

print("\n# 3. Stop all servers")
subprocess.run(["python", "tests/e2e/tools/stop_all_servers.py"], check=True)
