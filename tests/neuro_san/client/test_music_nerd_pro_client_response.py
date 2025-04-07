import os
import subprocess
import tempfile
import unittest

import pytest

from neuro_san.client.util.client_utils import ClientUtils

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(ROOT_DIR, "..", "..", "fixtures")
INPUT_FILE_DIR = os.path.join(FIXTURES_DIR, "music_nerd_pro")


@pytest.mark.integration
class TestMusicNerdProClientResponse(unittest.TestCase):
    """
    This class allows you to pass a prompt specified in a file to an agent network
    and get the response in another file. This helps with integration testing
    """

    agent = "music_nerd_pro"

    def test_beatles(self):
        """
        Query an agent network and assert the response contains the expected value
        """
        input_file = "beatles_prompt.txt"
        response_keyword = "Beatles"

        # To inspect the response_file (for debugging prupose), pass
        # "delete=False" argument to prevent temp file deletion
        with tempfile.NamedTemporaryFile(dir=INPUT_FILE_DIR, prefix="tmp_", suffix=".txt") as response_file:
            input_file = os.path.join(INPUT_FILE_DIR, input_file)

            try:
                result = ClientUtils.run_agent_cli_subprocess(TestMusicNerdProClientResponse.agent, input_file,
                                                              response_file.name)
                if result.returncode == 0:
                    flag, message = ClientUtils.evaluate_response_file(response_file.name, response_keyword)
                    if not flag:
                        self.fail(message)

            except subprocess.CalledProcessError as e:
                print(f"Command failed with exit code {e.returncode}: {e.cmd}")
                print(f"Error output: {e.stderr}")
                self.fail()
