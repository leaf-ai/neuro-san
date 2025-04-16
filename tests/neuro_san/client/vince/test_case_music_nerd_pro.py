import re
import pexpect
import sys
import os
import time
import json
import argparse

# ------------------------------------------------------------------------
# Function: Parse config file and extract values for test execution
# - Reads the connection types and prompts from a configuration file
# ------------------------------------------------------------------------

def extract_test_values(config_file, index=0):
    with open(config_file, 'r') as f:
        content = f.read()

    # Extract the connection list, e.g., [grpc, http, direct]
    conn_match = re.search(r'connection\s*=\s*\[([^\]]+)\]', content)
    if not conn_match:
        raise ValueError("connection list not found")

    # Convert to list and trim whitespace
    conn_list = [x.strip() for x in conn_match.group(1).split(',') if x.strip()]

    # Validate provided index
    if index >= len(conn_list):
        raise IndexError(f"Requested connection index {index}, but only {len(conn_list)} defined.")

    conn = conn_list[index]

    # Extract input_1.user_text string using regex
    input1_match = re.search(r'input_1\s*=\s*\{[^}]*user_text\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input1_match:
        raise ValueError("input_1.user_text not found")
    prompt_1 = input1_match.group(1)

    # Extract input_2.user_text string using regex
    input2_match = re.search(r'input_2\s*=\s*\{[^}]*user_text\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input2_match:
        raise ValueError("input_2.user_text not found")
    prompt_2 = input2_match.group(1)

    # Extract answer.word from input_1
    input1_word_match = re.search(r'input_1\s*=\s*\{[^}]*answer\s*=\s*\{[^}]*word\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input1_word_match:
        raise ValueError("input_1.answer.word not found")
    word_1 = input1_word_match.group(1)

    # Extract answer.word from input_2
    input2_word_match = re.search(r'input_2\s*=\s*\{[^}]*answer\s*=\s*\{[^}]*word\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input2_word_match:
        raise ValueError("input_2.answer.word not found")
    word_2 = input2_word_match.group(1)

    # Extract answer.cost from input_1
    input1_cost_match = re.search(r'input_1\s*=\s*\{[^}]*answer\s*=\s*\{[^}]*cost\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input1_cost_match:
        raise ValueError("input_1.answer.cost not found")
    cost_1 = input1_cost_match.group(1)

    # Extract answer.cost from input_2
    input2_cost_match = re.search(r'input_2\s*=\s*\{[^}]*answer\s*=\s*\{[^}]*cost\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not input2_cost_match:
        raise ValueError("input_2.answer.cost not found")
    cost_2 = input2_cost_match.group(1)

    return conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2


# ------------------------------------------------------------------------
# Function: Extract agent response text from CLI output
# - Removes cost/prompt footers and isolates the actual response
# ------------------------------------------------------------------------

def extract_agent_response(output: str, start_marker="Response from MusicNerdPro:"):
    pattern = (
        rf"{re.escape(start_marker)}"                     # Match start marker
        rf"(.*?)"                                         # Non-greedy capture
        rf"(?:\n+(?:"
        rf"Here'?s the running cost.*|"                   # Stop if cost line begins
        rf"The running cost.*|"
        rf"The current running cost.*|"
        rf"Please enter your response.*"
        rf"))"
    )

    match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        print("[WARN] Could not find agent response in output.")
        return None

# ------------------------------------------------------------------------
# Function: Extract cost information from output
# - Handles both plain text and JSON formats
# ------------------------------------------------------------------------

def extract_cost_line(output: str):
    # Pattern 1: Match natural language cost statement
    pattern = r"(Here('?s| is)|The|Your|Current).*?running cost.*?\$\d+\.\d{2}\.?"
    match = re.search(pattern, output, re.IGNORECASE)
    if match:
        return match.group(0).strip()

    # Pattern 2: Look for JSON containing "running_cost" key
    json_blocks = re.findall(r"\{.*?\}", output, re.DOTALL)
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            if "running_cost" in parsed:
                return f"running_cost: {parsed['running_cost']}"
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

    return None

# ------------------------------------------------------------------------
# Function: Verify that required keywords are found in the response
# - Returns a list of keywords that are missing
# ------------------------------------------------------------------------

def verify_keywords_in_response(response: str, keywords: list[str]) -> list[str]:
    if not response:
        return keywords  # No response means all keywords are missing

    missing = []
    response_lower = response.lower()
    for keyword in keywords:
        if keyword.lower() not in response_lower:
            missing.append(keyword)
    return missing

# ------------------------------------------------------------------------
# Function: Run test by simulating input/output to agent CLI using pexpect
# ------------------------------------------------------------------------

def run_test(conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2):
    print("\n=== Got From Config File ===")
    print(f"Connection = {conn}")
    print(f"Prompt 1 = {prompt_1}")
    print(f"Prompt 2 = {prompt_2}")
    print(f"Word 1 = {word_1}")
    print(f"Word 2 = {word_2}")
    print(f"Cost 1 = {cost_1}")
    print(f"Cost 2 = {cost_2}")
    print("==============================")

    # Construct and spawn the command to run the CLI agent
    command = f"python -m neuro_san.client.agent_cli --agent music_nerd_pro --connection {conn}"
    child = pexpect.spawn(command, encoding='utf-8', echo=False)

    # Show CLI interaction in real time
    child.logfile = sys.stdout

    # Expected prompt string from the CLI
    prompt = "enter your response"

    # Step 1: Send the first prompt
    child.expect(prompt)
    child.sendline(prompt_1)

    # Step 2: Capture and parse the output
    child.expect(prompt, timeout=60)
    output = child.before + child.after
    response_text_1 = extract_agent_response(output)
    cost_line_1 = extract_cost_line(output)

    # Step 3: Send the second prompt
    child.sendline(prompt_2)

    # Step 4: Capture and parse the output again
    child.expect(prompt, timeout=60)
    output = child.before + child.after
    response_text_2 = extract_agent_response(output)
    cost_line_2 = extract_cost_line(output)

    # Step 5: Gracefully exit the CLI
    child.sendline("quit")
    child.expect(pexpect.EOF)

    # Output the captured results
    print("\n=== FULL OUTPUT ===")
    print("🎯 Extracted Agent Response_1:\n", response_text_1 or "[No match]")
    print("💰 Extracted Cost Line_1:\n", cost_line_1 or "[No match]")
    print("\n🎯 Extracted Agent Response_2:\n", response_text_2 or "[No match]")
    print("💰 Extracted Cost Line_2:\n", cost_line_2 or "[No match]")

    # --------------------------------------------------------------------
    # Keyword verification for assertions
    # --------------------------------------------------------------------
    print("\n=== Match All Response Outputs ===")
    required_keywords_1 = [word_1]
    required_keywords_2 = [word_2]
    required_costs_1 = [cost_1]
    required_costs_2 = [cost_2]

    missing_1w = verify_keywords_in_response(response_text_1, required_keywords_1)
    missing_1c = verify_keywords_in_response(cost_line_1, required_costs_1)
    missing_2w = verify_keywords_in_response(response_text_2, required_keywords_2)
    missing_2c = verify_keywords_in_response(cost_line_2, required_costs_2)

    if missing_1w or missing_1c or missing_2w or missing_2c:
        print("❌ Missing in one or both responses:")
        if missing_1w:
            print(f" - Response 1 missing words: {', '.join(missing_1w)}")
        if missing_1c:
            print(f" - Response 1 missing costs: {', '.join(missing_1c)}")
        if missing_2w:
            print(f" - Response 2 missing words: {', '.join(missing_2w)}")
        if missing_2c:
            print(f" - Response 2 missing costs: {', '.join(missing_2c)}")
        sys.exit("❌ Test failed.")
    else:
        print("✅ All required keywords found in both responses.")

# ------------------------------------------------------------------------
# Main entry point: parse CLI args and run tests accordingly
# ------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run test cases for music_nerd_pro agent.")
    parser.add_argument("--connection", type=int, help="Index of the connection to test (0, 1, 2). If not provided, test all.")
    args = parser.parse_args()

    config_path = os.path.expanduser("~/TheTest/scripts/test_cases_music_nerd_pro.conf")

    try:
        if args.connection is not None:
            # Run test for a specific connection index
            conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2 = extract_test_values(config_path, index=args.connection)
            run_test(conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2)
        else:
            # Run test for all defined connection types
            with open(config_path, "r") as f:
                content = f.read()
            conn_match = re.search(r'connection\s*=\s*\[([^\]]+)\]', content)
            if not conn_match:
                raise ValueError("connection list not found")
            conn_list = [x.strip() for x in conn_match.group(1).split(',') if x.strip()]

            # Loop through and run test for each connection
            for i, conn_val in enumerate(conn_list):
                print(f"\n=== Running test for connection index {i} ({conn_val}) ===")
                conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2 = extract_test_values(config_path, index=i)
                run_test(conn, prompt_1, prompt_2, word_1, word_2, cost_1, cost_2)

    except IndexError as e:
        print(f"[ERROR] {e}")
    except Exception as e:
        print(f"[FAIL] {e}")

