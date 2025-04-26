# mnpt_runner.py
# ------------------------------------------------------------------------
# CLI-based test runner: drives input/output to the MusicNerdPro agent CLI
# ------------------------------------------------------------------------

import os
import sys
import pexpect
from utils.mnpt_output_parser import extract_agent_response, extract_cost_line
from utils.verifier import verify_keywords_in_response
from utils.thinking_file_builder import build_thinking_file_arg

def run_test(conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2, prompt_final, repeat_index, use_thinking_file):
    """
    Executes a CLI test scenario by interacting with the agent using pexpect.
    
    Args:
        conn (str): Connection type ('direct', 'grpc', 'http')
        prompt_1 (str): First user input
        prompt_2 (str): Second user input
        word_1 (str): Expected keyword in response 1
        word_2 (str): Expected keyword in response 2
        cost_1 (str): Expected cost in response 1
        cost_2 (str): Expected cost in response 2
        prompt_final (str): Termination command (e.g., 'quit')
        repeat_index (int): Current repetition index
        use_thinking_file (bool): Whether to include --thinking_file flag
    """
    print(f"\n▶️ Running test: connection='{conn}', repeat={repeat_index + 1}")

    # NEW: Use shared function
    thinking_file_arg = build_thinking_file_arg(conn, repeat_index, use_thinking_file)

    # Build thinking file argument if needed (only for grpc/http/direct)
    #thinking_file_arg = ""
    #if conn in ("grpc", "http", "direct") and use_thinking_file:
    #    thinking_path = f"/private/tmp/agent_thinking/{conn}_run{repeat_index + 1}"
    #    os.makedirs("/private/tmp/agent_thinking", exist_ok=True)
    #    thinking_file_arg = f" --thinking_file {thinking_path}"
    #    print(f"[thinking_file] → {thinking_path}", flush=True)

    # Build command to launch agent CLI
    command = (
        f"python -m neuro_san.client.agent_cli "
        f"--agent music_nerd_pro "
        f"--connection {conn}"
        f"{thinking_file_arg}"
    )
    print(f"[CMD] {command}", flush=True)

    # Start the agent CLI process
    child = pexpect.spawn(command, encoding="utf-8", echo=False)
    child.logfile = sys.stdout

    # Expected prompt from the CLI agent
    prompt = "enter your response"

    def send_and_parse(prompt_text):
        """Send a prompt, wait for agent reply, extract response and cost."""
        child.sendline(prompt_text)
        child.expect(prompt, timeout=60)
        output = child.before + child.after
        return extract_agent_response(output), extract_cost_line(output)

    # Begin interaction
    child.expect(prompt, timeout=60)
    resp_1, cost_1_out = send_and_parse(prompt_1)
    resp_2, cost_2_out = send_and_parse(prompt_2)

    # Terminate the session
    child.sendline(prompt_final)
    child.expect(pexpect.EOF)

    # Print outputs
    print("\n📤 Extracted Output:")
    print(f"🔹 Response 1: {resp_1}")
    print(f"💰 Cost Line 1: {cost_1_out}")
    print(f"🔹 Response 2: {resp_2}")
    print(f"💰 Cost Line 2: {cost_2_out}")

    def verify(label, actual, expected):
        """Verify if expected keyword/cost is found in output."""
        missing = verify_keywords_in_response(actual, [expected])
        if missing:
            print(f"❌ {label} missing: {', '.join(missing)}")
        return missing

    print("\n🔍 Verifying expected values...")
    failed = any([
        verify("Response 1", resp_1, word_1),
        verify("Cost 1", cost_1_out, cost_1),
        verify("Response 2", resp_2, word_2),
        verify("Cost 2", cost_2_out, cost_2),
    ])

    if failed:
        sys.exit(1)
    else:
        print("✅ Test passed successfully!")

