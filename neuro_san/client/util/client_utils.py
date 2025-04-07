import subprocess


class ClientUtils:
    """
    Static utility class for calling agent_cli and evaluating results in unit/integration tests
    """

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

    @staticmethod
    def evaluate_response_file(response_file, response_keyword):
        """
        :param response_file: file containing the agent network response to prompt
        :param response_keyword: the keyword we expect to be in the response file
        :return: a tuple, a Boolean and a message. Boolean is True if the keyword is found in the response file
                 Boolean is False is it is not, or if the response file is empty
        """
        with open(response_file, "r", encoding="utf-8") as fp:
            response = fp.read()

            if len(response) == 0:
                return False, "Response file is empty!"

            if response_keyword.lower() not in response.lower():
                return False, f"response_keyword {response_keyword} is not in response:\n{response}"

            return True, f"response_keyword {response_keyword} is in response:\n{response}"
