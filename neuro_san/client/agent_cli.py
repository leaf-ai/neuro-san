
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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
from time import sleep

import argparse
import json

from timedinput import timedinput

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.session.agent_session import AgentSession
from neuro_san.utils.file_of_class import FileOfClass


class AgentCli:
    """
    Command line tool for communicating with a Agent service
    running in a container.
    """

    def __init__(self):
        """
        Constructor
        """
        self.default_prompt: str = "Please enter your response ('quit' to terminate):\n"
        self.default_input: str = "DEFAULT"
        self.poll_timeout_seconds: float = 5.0
        self.input_timeout_seconds: float = 5000.0
        self.args = None

        self.session: AgentSession = None
        self.session_id: str = None

    def main(self):
        """
        Main entry point for command line user interaction
        """
        self.parse_args()
        self.open_session()

        # Get initial user input
        user_input: str = None
        if self.args.first_prompt_file is not None:
            # Incorrectly flagged as destination of Path Traversal 4
            #   Reason: first_prompt_file was previously checked with FileOfClass.check_file()
            #           which actually does the path traversal check. CheckMarx does not
            #           recognize pathlib as a valid library with which to resolve these kinds
            #           of issues.  Furthermore, this is a client command line tool that is never
            #           used inside servers which just happens to be part of a library offering.
            with open(self.args.first_prompt_file, 'r', encoding="utf-8") as prompt_file:
                user_input = prompt_file.read()

        sly_data: Dict[str, Any] = None
        if self.args.sly_data is not None:
            sly_data = json.loads(self.args.sly_data)
            print(f"sly_data is {sly_data}")

        state: Dict[str, Any] = {
            "last_logs": [],
            "last_chat_response": None,
            "prompt": self.default_prompt,
            "timeout": self.input_timeout_seconds
        }

        print("To see the thinking involved with the agent:\n"
              f"    tail -f {self.args.thinking_file}\n")

        empty: Dict[str, Any] = {}
        response: Dict[str, Any] = self.session.function(empty)
        function: Dict[str, Any] = response.get("function", empty)
        initial_prompt: str = function.get("description")
        print(f"\n{initial_prompt}\n")

        while user_input != "quit":

            prompt = state.get("prompt")
            timeout = state.get("timeout")
            if user_input is None:
                if prompt is not None and len(prompt) > 0:
                    user_input = timedinput(prompt, timeout=timeout,
                                            default=self.default_input)
                else:
                    user_input = None

            if user_input == "quit":
                break

            if user_input is not None and user_input != self.default_input:
                print(f"Sending user_input {user_input}")
                self.send_user_input(user_input, sly_data)
                user_input = None
            else:
                sleep(self.poll_timeout_seconds)

            state = self.get_responses(state)

    def parse_args(self):
        """
        Parse command line arguments into member variables
        """
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument("--local", type=bool, default=True,
                                help="If True (the default), assume we are running against local container")
        arg_parser.add_argument("--host", type=str, default=None,
                                help="hostname setting if not running locally")
        arg_parser.add_argument("--port", type=int, default=AgentSession.DEFAULT_PORT,
                                help="TCP/IP port to run the Agent gRPC service on")
        arg_parser.add_argument("--agent", type=str, default="esp_decision_assistant",
                                help="Name of the agent to talk to on the server")
        arg_parser.add_argument("--thinking_file", type=str, default="/tmp/agent_thinking.txt",
                                help="File that captures agent thinking. "
                                     "This is a separate text stream from the user/assistant chat")
        arg_parser.add_argument("--first_prompt_file", type=str,
                                help="File that captures the first response to the input prompt")
        arg_parser.add_argument("--sly_data", type=str,
                                help="JSON string containing data that is out-of-band to the chat stream, "
                                     "but is still essential to agent function")
        arg_parser.add_argument("--connection", default="direct", type=str,
                                choices=["service", "direct"],
                                help="""
The type of connection to initiate. Choices are to connect to:
    "service"   - an agent service via gRPC. (The default).  Needs host and port.
    "direct"    - a session via library.
All choices require an agent name.
""")

        # Incorrectly flagged as source of Path Traversal 1, 2, 4, 5, 6
        # See destination in file_of_class.py for exception explanation.
        # Incorrectly flagged as source of Trust Boundary Violation 1, 2
        # See destination in agent_session_factory.py for exception explanation.
        self.args = arg_parser.parse_args()

        # Check some arguments to prevent PathTraversal scans lighting up.
        # Since this is a command-line tool not intended to be used inside a
        # Dockerfile service, we don't really care where these files come from.
        # Check anyway to give warm fuzzies to scans.
        self.args.thinking_file = FileOfClass.check_file(self.args.thinking_file, "/")
        self.args.first_prompt_file = FileOfClass.check_file(self.args.first_prompt_file, "/")

    def open_session(self):
        """
        Opens a session based on the parsed command line arguments
        """
        hostname = "localhost"
        if self.args.host is not None or not self.args.local:
            hostname = self.args.host

        # Open a session
        self.session = AgentSessionFactory.create_session(self.args.connection, self.args.agent,
                                                          hostname, self.args.port)

        # Clear out the previous thinking file
        #
        # Incorrectly flagged as destination of Path Traversal 5
        #   Reason: thinking_file was previously checked with FileOfClass.check_file()
        #           which actually does the path traversal check. CheckMarx does not
        #           recognize pathlib as a valid library with which to resolve these kinds
        #           of issues.  Furthermore, this is a client command line tool that is never
        #           used inside servers which just happens to be part of a library offering.
        with open(self.args.thinking_file, "w", encoding="utf-8") as thinking:
            thinking.write("\n")

    def send_user_input(self, user_input: str, sly_data: Dict[str, Any]):
        """
        Sends user input to Agent service
        """
        # Send user input
        if user_input != self.default_input:
            chat_request = {
                "session_id": self.session_id,
                "user_input": user_input
            }

            if sly_data is not None and len(sly_data.keys()) > 0:
                chat_request["sly_data"] = sly_data

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
            with open(self.args.thinking_file, "a", encoding="utf-8") as thinking:
                # Write out the latest logs
                # Might be more than 1
                for i in range(len(last_logs), len(logs)-1):
                    thinking.write(logs[i])
            last_logs = logs

        # Update chat response and maybe prompt.
        prompt = ""
        timeout = self.poll_timeout_seconds
        if chat_response is not None:
            print(f"Response: {chat_response}")
            prompt = self.default_prompt
            timeout = self.input_timeout_seconds
            last_chat_response = chat_response

        return_state: Dict[str, Any] = {
            "last_logs": last_logs,
            "last_chat_response": last_chat_response,
            "prompt": prompt,
            "timeout": timeout
        }
        return return_state


if __name__ == '__main__':
    AgentCli().main()
