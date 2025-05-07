# 🧪 End-to-End Testing Suite for `music_nerd_pro`

This directory contains the full end-to-end (E2E) test infrastructure for the `music_nerd_pro` agent, including configuration, reusable utilities, test cases, and server lifecycle control tools.

---

## 📁 Directory Structure

```text
tests/e2e/
├── README.md                      # ✅ You're here
├── configs/
│   └── config.hocon               # HOCON config defining all agent connections
├── conftest.py                    # Shared pytest setup, CLI options, parametrization, server startup
├── requirements.txt               # Pip requirements for test environment
├── test_cases_data/
│   └── mnpt_data.hocon            # Input data and expectations for test runner
├── tests/
│   └── test_run_agent_cli_music_nerd_pro.py  # Main test case driver (used by orchestrators)
├── tools/
│   ├── smoke_test_runner.py       # Orchestrator: start → test → stop
│   ├── start_server_manual.py     # Manual: starts server and stores PID
│   ├── stop_all_servers.py        # Manual: stops all running agent servers from PID file
│   └── stop_last_server.py        # Manual: stops only the most recently started server
└── utils/
    ├── logging_config.py          # Shared logging setup (file + console)
    ├── music_nerd_pro_hocon_loader.py  # Extracts structured test data from HOCON config
    ├── music_nerd_pro_output_parser.py # Parses CLI outputs for verification
    ├── music_nerd_pro_runner.py   # Executes the CLI test logic
    ├── server_manager.py          # Manages agent server lifecycle (start, stop, PID tracking)
    ├── server_state.py            # In-memory + file-based PID state tracking
    ├── thinking_file_builder.py   # Generates `thinking_file` argument path
    └── verifier.py                # Assertion helper for output validation
```

---

## 🚦 How to Run E2E Tests

### 🔁 Option 1: Manual Mode

```bash
# 1. Start agent server manually
python tests/e2e/tools/start_server_manual.py

# 2. Run E2E CLI tests
pytest tests/e2e/tests/test_run_agent_cli_music_nerd_pro.py \
  --capture=no --connection grpc --thinking-file --repeat 1 -n auto

# 3. Stop all running agent servers
python tests/e2e/tools/stop_all_servers.py
```

---

### ⚡ Option 2: Orchestrated Smoke Test

Run everything in one go:

```bash
python -m tests.e2e.tools.smoke_test_runner
```

---

## ✅ Test CLI Options

| Option           | Description                                      |
|------------------|--------------------------------------------------|
| `--connection`   | One of: `direct`, `grpc`, `http`                 |
| `--repeat`       | Number of repetitions per connection             |
| `--thinking-file`| Enables logging of agent `thinking_file` output  |
| `-n`             | This is Pytest to launch the runner in parallel  |

---

## 📦 Test Environment Setup

```bash
pip install -r tests/e2e/requirements.txt
```

You must also have the `neuro_san` package accessible via `PYTHONPATH`.

---

## 🧠 Notes

- PID tracking is handled via `/tmp/neuro_san_server.pid`.
- Multiple PIDs are supported and cleaned up automatically.
- The test file `test_run_agent_cli_music_nerd_pro.py` is ignored during normal discovery unless triggered explicitly.
- Logging is unified under `/tmp/e2e_server.log`.

---

## 🛠️ Authors & Maintenance

Maintained by QA & Platform Engineering.
Contact: `@vincent.nguyen`
