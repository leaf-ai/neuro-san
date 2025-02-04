
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from typing import Any
from typing import Dict

from copy import copy
from time import sleep

from neuro_san.client.abstract_input_processor import AbstractInputProcessor
from neuro_san.interfaces.agent_session import AgentSession


# pylint: disable=too-many-arguments,too-many-positional-arguments
class PollingInputProcessor(AbstractInputProcessor):
    """
    Processes AgentCli input by using the neuro-san polling API.

    Note that the polling API is deprecated.
    If you are looking for a better example, take a look at the StreamingInputProcessor.
    """

    def __init__(self, default_prompt: str,
                 default_input: str,
                 input_timeout_seconds: float,
                 thinking_file: str,
                 session: AgentSession,
                 poll_timeout_seconds: float):
        """
        Constructor
        """
        super().__init__()
        self.default_prompt: str = default_prompt
        self.default_input: str = default_input
        self.poll_timeout_seconds: float = poll_timeout_seconds
        self.input_timeout_seconds: float = input_timeout_seconds
        self.thinking_file: str = thinking_file
        self.session: AgentSession = session

    def process_once(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use polling strategy to communicate with agent.
        :param state: The state dictionary to pass around
        :return: An updated state dictionary
        """
        user_input: str = state.get("user_input")
        sly_data: Dict[str, Any] = state.get("sly_data")

        if user_input is not None and user_input != self.default_input:
            print(f"Sending user_input {user_input}")
            self.send_user_input(user_input, sly_data)
            state["user_input"] = None
        else:
            sleep(self.poll_timeout_seconds)

        state: Dict[str, Any] = self.get_responses(state)
        return state

    def send_user_input(self, user_input: str, sly_data: Dict[str, Any]):
        """
        Sends user input to Agent service
        """
        # Send user input
        if user_input != self.default_input:
            chat_request: Dict[str, Any] = self.formulate_chat_request(user_input, sly_data)

            # Send initial chat request
            chat_response = self.session.chat(chat_request)
            if self.session_id is None:
                self.session_id = chat_response.get("session_id")
                print(f"Using assistant session id {self.session_id}")

    def get_responses(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Polls for chat responses
        """
        last_logs = state.get("last_logs")
        last_chat_response = state.get("last_chat_response")
        prompt = state.get("prompt")
        timeout = state.get("timeout")
        num_input = state.get("num_input")

        # Get logs so we know what the assistant is thinking
        logs_request = {
            "session_id": self.session_id
        }

        logs_response = self.session.logs(logs_request)

        # Get the logs from the response.
        logs = logs_response.get("logs")
        chat_response = logs_response.get("chat_response")

        # Update logs
        if logs is not None and logs != last_logs:
            # Incorrectly flagged as destination of Path Traversal 6
            #   Reason: thinking_file was previously checked with FileOfClass.check_file()
            #           which actually does the path traversal check. CheckMarx does not
            #           recognize pathlib as a valid library with which to resolve these kinds
            #           of issues.  Furthermore, this is a client command line tool that is never
            #           used inside servers which just happens to be part of a library offering.
            with open(self.thinking_file, "a", encoding="utf-8") as thinking:
                # Write out the latest logs
                # Might be more than 1
                for i in range(len(last_logs), len(logs)-1):
                    thinking.write(logs[i])
                    thinking.write("\n")
            last_logs = copy(logs)

        # Update chat response and maybe prompt.
        prompt = ""
        timeout = self.poll_timeout_seconds
        if chat_response is not None:
            print(f"Response: {chat_response}")
            prompt = self.default_prompt
            timeout = self.input_timeout_seconds
            last_chat_response = chat_response
            num_input += 1

        return_state: Dict[str, Any] = {
            "last_logs": last_logs,
            "last_chat_response": last_chat_response,
            "prompt": prompt,
            "timeout": timeout,
            "num_input": num_input
        }
        return return_state
