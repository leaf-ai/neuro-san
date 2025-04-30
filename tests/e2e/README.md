# 🧪 End-to-End Agent Testing Framework

This project provides an extensible, reusable **pytest**-based test system to validate AI agent behavior through real CLI interactions.

It supports:
- Running **multiple connections** (`grpc`, `http`, `direct`)
- **Parallel execution** with **pytest-xdist**
- Optional **thinking file capture** for agent internals
- Config-driven prompts using **HOCON** files

---

## 📦 Project Structure

```bash
e2e/
├── README.md                     # This documentation
├── configs/                      # Static agent configuration
│   └── config.hocon
├── conftest.py                   # Pytest customizations (CLI args, test discovery)
├── pytest.ini                    # Pytest settings
├── requirements.txt              # Python dependencies
├── test_cases_data/              # Test data for each agent
│   └── mnpt_data.hocon
├── tests/                        # Test case source files
│   └── test_music_nerd_pro.py
└── utils/                        # Helper modules for parsing, test orchestration, and CLI interaction
  ├── mnpt_hocon_loader.py        # Loads test input data from HOCON config files (connection, prompts, expectations)
  ├── mnpt_output_parser.py       # Parses agent CLI output (response and cost lines) using regex/JSON extraction
  ├── mnpt_test_runner.py         # Main runner that drives CLI interaction using pexpect and verifies output
  ├── server_manager.py           # Starts and stops the backend agent service (used for grpc/http test runs)
  ├── thinking_file_builder.py    # Builds --thinking-file arguments dynamically for repeated test runs
  └── verifier.py                 # Contains logic to validate whether agent responses contain expected keywords/costs
```

---

## 🚀 Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Basic Test Command

Run a test (default: **all connections**):

```bash
pytest tests/ --verbose
```

Run for specific connection only:

```bash
pytest tests/ --connection grpc --verbose
```

Run and enable thinking file output:

```bash
pytest tests/ --thinking-file --verbose
```

Enable parallel test execution:

```bash
pytest tests/ --connection grpc --repeat 5 --thinking-file -n auto --verbose
```

> 💡 When using `-n auto`, each repeat runs across multiple CPU cores.

---

## ⚙️ CLI Options

| Option            | Description |
|:------------------|:------------|
| `--connection`     | Run tests only for a specific connection (e.g., `grpc`, `http`, `direct`). |
| `--repeat`         | Repeat each test multiple times. |
| `--thinking-file`  | Save the agent's internal "thinking" to a temp directory during the test. |

---

# 🧠 Agent: MusicNerdPro Test (test_music_nerd_pro.py)

This suite tests the `music_nerd_pro` agent over all connection types.

### Test Logic

- Load prompt/expected outputs from **HOCON** config files
- Spawn a CLI agent process
- Send user questions
- Verify that:
  - Correct keyword appears in the response
  - Correct cost value is returned

### Related Files

| File | Purpose |
|:-----|:--------|
| `tests/test_music_nerd_pro.py` | Main test case (pytest function) |
| `test_cases_data/mnpt_data.hocon` | Prompt/expected answer definitions |
| `configs/config.hocon` | Static agent config (connections list) |
| `utils/*.py` | Reusable helpers for all agent tests |

---

# 📝 Notes

- **Thinking files** are stored under `/private/tmp/agent_thinking/`
- If `-n auto` is used, **worker-specific** folders are created (e.g., `run_gw0_1`).
- **PEXPECT** is used to fully simulate CLI typing behavior.
- Future agents can be easily added following the same pattern as MusicNerdPro!