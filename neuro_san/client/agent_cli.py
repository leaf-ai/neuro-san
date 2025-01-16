
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
from typing import Generator

from copy import copy
from time import sleep

import argparse
import json

from timedinput import timedinput

from grpc import RpcError
from grpc import StatusCode

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.internals.utils.file_of_class import FileOfClass
from neuro_san.session.agent_session import AgentSession


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

        empty: Dict[str, Any] = {}
        try:
            response: Dict[str, Any] = self.session.function(empty)
        except RpcError as exception:
            # pylint: disable=no-member
            if exception.code() is StatusCode.UNIMPLEMENTED:
                message = f"""
The agent "{self.args.agent}" is not implemented on the server.

Some suggestions:
1. Did you misspell the agent name on the command line?
2. Is there a key for the agent name in the server manifest.hocon file?
3. Is the value for the agent name key in the server manifest.hocon file set to true?
4. Servers will skip manifest entries that have errors. They will also print out which
   agents they are actually serving.  Check your server output for each of these.
"""
                raise ValueError(message) from exception

            # If not an RpcException, then I dunno what it is.
            raise

        function: Dict[str, Any] = response.get("function", empty)
        initial_prompt: str = function.get("description")
        print(f"\n{initial_prompt}\n")

        print("To see the thinking involved with the agent:\n"
              f"    tail -f {self.args.thinking_file}\n")

        state: Dict[str, Any] = {
            "last_logs": [],
            "last_chat_response": None,
            "prompt": self.default_prompt,
            "timeout": self.input_timeout_seconds,
            "num_input": 0,
            "user_input": user_input,
            "sly_data": sly_data,
        }

        while not self.is_done(state):

            prompt = state.get("prompt")
            timeout = state.get("timeout")
            user_input = state.get("user_input")
            if user_input is None:
                if prompt is not None and len(prompt) > 0:
                    user_input = timedinput(prompt, timeout=timeout,
                                            default=self.default_input)
                else:
                    user_input = None

            if user_input == "quit":
                break

            state["user_input"] = user_input
            if self.args.stream:
                state = self.stream_once(state)
            else:
                state = self.poll_once(state)

    def parse_args(self):
        """
        Parse command line arguments into member variables
        """

        arg_parser = argparse.ArgumentParser()

        self.add_args(arg_parser)

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

    def add_args(self, arg_parser: argparse.ArgumentParser):
        """
        Adds arguments.  Allows subclasses a chance to add their own.
        :param arg_parser: The argparse.ArgumentParser to add.
        """
        arg_parser.add_argument("--local", type=bool, default=True,
                                help="If True (the default), assume we are running against local container")
        arg_parser.add_argument("--host", type=str, default=None,
                                help="hostname setting if not running locally")
        arg_parser.add_argument("--port", type=int, default=AgentSession.DEFAULT_PORT,
                                help="TCP/IP port to run the Agent gRPC service on")
        arg_parser.add_argument("--agent", type=str, default="esp_decision_assistant",
                                help="Name of the agent to talk to")
        arg_parser.add_argument("--thinking_file", type=str, default="/tmp/agent_thinking.txt",
                                help="File that captures agent thinking. "
                                     "This is a separate text stream from the user/assistant chat")
        arg_parser.add_argument("--first_prompt_file", type=str,
                                help="File that captures the first response to the input prompt")
        arg_parser.add_argument("--sly_data", type=str,
                                help="JSON string containing data that is out-of-band to the chat stream, "
                                     "but is still essential to agent function")
        arg_parser.add_argument("--stream", default=True, action="store_true",
                                help="Use streaming chat instead of polling")
        arg_parser.add_argument("--poll", dest="stream", action="store_false",
                                help="Use polling chat instead of streaming")
        arg_parser.add_argument("--connection", default="direct", type=str,
                                choices=["service", "direct"],
                                help="""
The type of connection to initiate. Choices are to connect to:
    "service"   - an agent service via gRPC. (The default).  Needs host and port.
    "direct"    - a session via library.
All choices require an agent name.
""")
        arg_parser.add_argument("--service", dest="connection", action="store_const", const="service",
                                help="Use a service connection")
        arg_parser.add_argument("--direct", dest="connection", action="store_const", const="direct",
                                help="Use a direct/library call for the chat")
        arg_parser.add_argument("--max_input", type=int, default=1000000,
                                help="Maximum rounds of input to go before exiting")
        arg_parser.add_argument("--one_shot", dest="max_input", action="store_const", const=1,
                                help="Send one round of input, then exit")

    def open_session(self):
        """
        Opens a session based on the parsed command line arguments
        """
        hostname = "localhost"
        if self.args.host is not None or not self.args.local:
            hostname = self.args.host

        # Open a session with the factory
        factory: AgentSessionFactory = self.get_agent_session_factory()
        self.session = factory.create_session(self.args.connection, self.args.agent,
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

    def get_agent_session_factory(self) -> AgentSessionFactory:
        """
        This allows subclasses to add different kinds of connections.

        :return: An AgentSessionFactory instance that will allow creation of the
                 session with the agent network.
        """
        return AgentSessionFactory()

    def is_done(self, state: Dict[str, Any]) -> bool:
        """
        :param state: The state dictionary
        :return: True if the values in the state are considered to be sufficient
                for terminating further conversation. False otherwise.
        """

        if state.get("user_input") == "quit":
            return True

        if state.get("num_input") >= self.args.max_input:
            return True

        return False

    def poll_once(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use polling strategy to communicate with agent.
        :param user_input: The initial (string) user input to the loop.
        :param sly_data: The initial dictionary of private sly_data to send.
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
            with open(self.args.thinking_file, "a", encoding="utf-8") as thinking:
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

    # pylint: disable=too-many-locals
    def stream_once(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use polling strategy to communicate with agent.
        :param user_input: The initial (string) user input to the loop.
        :param sly_data: The initial dictionary of private sly_data to send.
        """
        user_input: str = state.get("user_input")
        last_logs = state.get("last_logs")
        last_chat_response = state.get("last_chat_response")
        num_input = state.get("num_input")

        if user_input is None or user_input == self.default_input:
            return state

        print(f"Sending user_input {user_input}")
        sly_data: Dict[str, Any] = state.get("sly_data")
        chat_request: Dict[str, Any] = self.formulate_chat_request(user_input, sly_data)

        return_state: Dict[str, Any] = {}
        empty = {}
        chat_responses: Generator[Dict[str, Any], None, None] = self.session.streaming_chat(chat_request)
        for chat_response in chat_responses:

            session_id: str = chat_response.get("session_id")
            response: Dict[str, Any] = chat_response.get("response", empty)

            if session_id is not None:
                self.session_id = session_id

            # Convert the message type in the response to the enum we want to work with
            response_type: str = response.get("type")
            message_type: ChatMessageType = ChatMessageType.from_response_type(response_type)

            text: str = response.get("text")

            # Update chat response and maybe prompt.
            if text is not None:
                if message_type == ChatMessageType.LEGACY_LOGS:
                    with open(self.args.thinking_file, "a", encoding="utf-8") as thinking:
                        thinking.write(text)
                        thinking.write("\n")
                elif message_type == ChatMessageType.AGENT_FRAMEWORK:
                    # Skip over the connectivity messages
                    if response.get("origin") is None:
                        print(f"{text}")
                else:
                    print(f"Response: {text}")
                    last_chat_response = text

            return_state = {
                "last_logs": last_logs,
                "last_chat_response": last_chat_response,
                "prompt": self.default_prompt,
                "timeout": self.input_timeout_seconds,
                "num_input": num_input + 1
            }

        return return_state

    def formulate_chat_request(self, user_input: str, sly_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Formulates a single chat request given the user_input
        :param user_input: The string to send
        :param sly_data: The sly_data dictionary to send
        :return: A dictionary representing the chat request to send
        """
        chat_request = {
            "session_id": self.session_id,
            "user_message": {
                "type": ChatMessageType.HUMAN,
                "text": user_input
            }
        }

        if sly_data is not None and len(sly_data.keys()) > 0:
            chat_request["sly_data"] = sly_data

        return chat_request


if __name__ == '__main__':
    AgentCli().main()
