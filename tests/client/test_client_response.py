import os
import subprocess
import tempfile
import time
import unittest

import pytest

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(ROOT_DIR, "..", "fixtures")
INPUT_FILE_DIR = os.path.join(FIXTURES_DIR, "client")


class TestMusicNerdProClient(unittest.TestCase):
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
        # pylint: disable=consider-using-with
        agent_cli_subprocess = subprocess.Popen(["python3", "-m", "neuro_san.client.agent_cli",
                                                 "--connection", "direct",
                                                 "--agent", agent,
                                                 "--first_prompt_file", input_file,
                                                 "--response_output_file", response_file,
                                                 "--one_shot"
                                                 ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # Wait for the server to start
        time.sleep(40)

        return agent_cli_subprocess

    @staticmethod
    def destruct_agent_cli_subprocess(agent_process):
        """
        :param agent_process: a Popen object representing the running process to be destructed
        :return: None
        """
        if agent_process:
            agent_process.terminate()
            agent_process.wait()

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
    def test_beatles(self):
        """
        Query an agent network and assert the response contains the expected value
        """
        # To inspect the response_file (for debugging prupose), pass
        # "delete=False" argument to prevent temp file deletion
        with tempfile.NamedTemporaryFile(dir=INPUT_FILE_DIR, prefix="tmp_", suffix=".txt") as response_file:
            input_file = os.path.join(INPUT_FILE_DIR, "beatles_prompt.txt")
            response_keyword = "Beatles"
            agent_process = None

            with open(input_file, "r", encoding="utf-8") as fp:
                input = fp.read()
                print(f"input: {input}")

            try:
                agent_process = TestMusicNerdProClient.get_agent_cli_subprocess(TestMusicNerdProClient.agent,
                                                                                input_file, response_file.name)
                """
                for _ in range(100):
                    line = agent_process.stdout.readline()
                    if not line:
                        continue
                    print(f"aline: {line.rstrip()}", flush=True)
                """
                poll = agent_process.poll()
                if poll is None:
                    print(f"agent_process {agent_process} is alive")

                time.sleep(40)

                print(f"response_file.name: {response_file.name}")
                print(f"response_file.name size: {os.stat(response_file.name).st_size}")

                poll = agent_process.poll()
                if poll is None:
                    print(f"agent_process {agent_process} is alive")

                self.assert_response(response_file, response_keyword)
            finally:
                TestMusicNerdProClient.destruct_agent_cli_subprocess(agent_process)


if __name__ == "__main__":
    unittest.main()
