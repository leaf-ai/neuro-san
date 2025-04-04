import os
import subprocess
import tempfile
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

    music_nerd_pro_agent = "music_nerd_pro"

    @staticmethod
    def run_agent_cli_subprocess(agent, input_file, response_file):
        """
        :param agent: the name of the agent network to query
        :param input_file: file containing the prompt for the agent network
        :param response_file: file that accepts the response from the agent newtork

        :return: a CompletedProcess object, which contains the return code and the output
        """
        # pylint: disable=consider-using-with
        result = subprocess.run(["python3", "-m", "neuro_san.client.agent_cli",
                                 "--connection", "direct",
                                 "--agent", agent,
                                 "--first_prompt_file", input_file,
                                 "--response_output_file", response_file,
                                 "--one_shot"
                                 ], capture_output=True, text=True, check=True, timeout=30)
        return result

    def assert_response(self, response_file, response_keyword):
        """
        :param response_file: file containing the agent network response to prompt
        :param response_keyword: the keyword we expect to be in the response file
        :return: None
        """
        with open(response_file.name, "r", encoding="utf-8") as fp:
            response = fp.read()
            self.assertGreater(len(response), 0, "Response file is empty!")
            self.assertIn(response_keyword.lower(), response.lower(),
                          f"response_keyword {response_keyword} not in response {response}")

    @pytest.mark.integration
    def test_music_nerd_pro_beatles(self):
        """
        Query an agent network and assert the response contains the expected value
        """
        agent = "music_nerd_pro"
        input_file = "beatles_prompt.txt"

        # To inspect the response_file (for debugging prupose), pass
        # "delete=False" argument to prevent temp file deletion
        with tempfile.NamedTemporaryFile(dir=INPUT_FILE_DIR, prefix="tmp_", suffix=".txt") as response_file:
            input_file = os.path.join(INPUT_FILE_DIR, input_file)
            response_keyword = "Beatles"

            try:
                result = TestClientResponse.run_agent_cli_subprocess(agent, input_file, response_file.name)
                if result.returncode == 0:
                    self.assert_response(response_file, response_keyword)

            except subprocess.CalledProcessError as e:
                print(f"Command failed with exit code {e.returncode}: {e.cmd}")
                print(f"Error output: {e.stderr}")
                self.fail()


if __name__ == "__main__":
    unittest.main()
