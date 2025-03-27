import os
import subprocess
import tempfile
import time
import unittest

import pytest

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(ROOT_DIR, "..", "fixtures")


class TestClientResponse(unittest.TestCase):

    agent = "music_nerd_pro"
    input_file_dir = os.path.join(FIXTURES_PATH, "client")
    input_file = os.path.join(input_file_dir, "beatles_prompt.txt")
    # To inspect the response_file (for debugging prupose), pass "delete=False" argument to prevent temp file deletion
    response_file = tempfile.NamedTemporaryFile(dir=input_file_dir, prefix="tmp_beatles_response_", suffix=".txt")
    response_keyword = "Beatles"

    def setUp(self):
        self.agent_process = subprocess.Popen(["python3", "-m", "neuro_san.client.agent_cli",
                                               "--connection", "direct",
                                               "--agent", TestClientResponse.agent,
                                               "--first_prompt_file", TestClientResponse.input_file,
                                               "--response_output_file", TestClientResponse.response_file.name,
                                               "--one_shot"
                                               ])
        # Wait for the server to start
        time.sleep(15)

    def tearDown(self):
        if self.agent_process:
            self.agent_process.terminate()
            self.agent_process.wait()

    @pytest.mark.integration
    def test_beatles(self):
        try:
            print(f"agent: {TestClientResponse.agent}")
            print(f"input_file: {TestClientResponse.input_file}")
            print(f"response_file: {TestClientResponse.response_file.name}")
            with open(TestClientResponse.response_file.name, "r") as fp:
                response = fp.read()
                self.assertGreater(len(response), 0, "Response file is empty!")
                self.assertIn(TestClientResponse.response_keyword.lower(), response.lower(),
                              f"response_keyword {TestClientResponse.response_keyword} not in response {response}")
        finally:
            TestClientResponse.response_file.close()


if __name__ == "__main__":
    unittest.main()
