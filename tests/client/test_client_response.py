import os
import subprocess
import tempfile
import time
import unittest

import pytest

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(ROOT_DIR, "..", "fixtures")
INPUT_FILE_DIR = os.path.join(FIXTURES_DIR, "client")


class TestClientResponse(unittest.TestCase):
    """
    This class allows you to pass a prompt specified in a file to an agent network
    and get the response in another file. This helps with integration testing
    """

    agent = "music_nerd_pro"

    @staticmethod
    def get_agent_cli_subprocess(agent, input_file, response_file):
        """
        :param agent: the name of the agent network to query
        :param input_file: file containing the prompt for the agent network
        :param response_file: file that accepts the response from the agent newtork

        :return: a Popen object representing the running process
        """
        agent_cli_subprocess = subprocess.Popen(["python3", "-m", "neuro_san.client.agent_cli",
                                                 "--connection", "direct",
                                                 "--agent", agent,
                                                 "--first_prompt_file", input_file,
                                                 "--response_output_file", response_file,
                                                 "--one_shot"
                                                 ])
        # Wait for the server to start
        time.sleep(15)

        return agent_cli_subprocess

    def tearDown(self):
        if self.agent_process:
            self.agent_process.terminate()
            self.agent_process.wait()

    @pytest.mark.integration
    def test_beatles(self):
        """
        Query an agent network and assert the response contains the expected value
        """
        input_file = os.path.join(INPUT_FILE_DIR, "beatles_prompt.txt")
        # To inspect the response_file (for debugging prupose), pass
        # "delete=False" argument to prevent temp file deletion
        response_file = tempfile.NamedTemporaryFile(dir=INPUT_FILE_DIR, prefix="tmp_", suffix=".txt")
        response_keyword = "Beatles"

        self.agent_process = TestClientResponse.get_agent_cli_subprocess(TestClientResponse.agent,
                                                                         input_file,
                                                                         response_file.name)
        try:
            print(f"agent: {TestClientResponse.agent}")
            print(f"input_file: {input_file}")
            print(f"response_file: {response_file.name}")
            with open(response_file.name, "r", encoding="utf-8") as fp:
                response = fp.read()
                self.assertGreater(len(response), 0, "Response file is empty!")
                self.assertIn(response_keyword.lower(), response.lower(),
                              f"response_keyword {response_keyword} not in response {response}")
        finally:
            response_file.close()


if __name__ == "__main__":
    unittest.main()
