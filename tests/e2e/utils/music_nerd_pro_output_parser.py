# output_parser.py
# ---------------------------------------------------------
# Parses CLI agent output to extract response or cost info
# ---------------------------------------------------------

import re
import json


def extract_agent_response(output: str, start_marker="Response from MusicNerdPro:"):
    """
    Extracts agent's response text based on a start marker.
    Strips out trailing cost information or CLI prompts.
    """
    pattern = (
        rf"{re.escape(start_marker)}(.*?)"
        rf"(?:\n+(?:Here'?s the running cost.*|The running cost.*|"
        rf"The current running cost.*|Please enter your response.*))"
    )
    match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_cost_line(output: str):
    """
    Finds and returns cost-related information from agent output.
    Tries different styles: labeled, sentence, or JSON block.
    Return None on nothing
    """
    label = re.search(r"Running Cost:\s*\$\d+\.\d{2}", output)
    if label:
        return label.group(0)

    sentence = re.search(r"(Here('?s| is)?|The|Your).*?running cost.*?\$\d+\.\d{2}", output, re.IGNORECASE)
    if sentence:
        return sentence.group(0)

    for block in re.findall(r"\{.*?\}", output, re.DOTALL):
        try:
            parsed = json.loads(block.replace("'", '"'))
            if "running_cost" in parsed:
                return f"running_cost: {parsed['running_cost']}"
        except Exception:
            continue

    return None
