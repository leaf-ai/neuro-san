
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

import os
import shutil

import argparse
import json

from timedinput import timedinput

from grpc import RpcError
from grpc import StatusCode

from neuro_san.client.abstract_input_processor import AbstractInputProcessor
from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.client.polling_input_processor import PollingInputProcessor
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.utils.file_of_class import FileOfClass


# pylint: disable=too-many-instance-attributes
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
        self.thinking_dir: str = None

    # pylint: disable=too-many-branches
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

        print("To see the thinking involved with the agent:\n")
        if not self.args.thinking_dir:
            print(f"    tail -f {self.args.thinking_file}\n")
        else:
            print(f"    See any one of the files in {self.thinking_dir} for agent network chat details.\n")

        state: Dict[str, Any] = {
            "last_logs": [],
            "last_chat_response": None,
            "prompt": self.default_prompt,
            "timeout": self.input_timeout_seconds,
            "num_input": 0,
            "user_input": user_input,
            "sly_data": sly_data,
        }

        input_processor: AbstractInputProcessor = None
        if self.args.stream:
            input_processor = StreamingInputProcessor(self.default_prompt,
                                                      self.default_input,
                                                      self.input_timeout_seconds,
                                                      self.args.thinking_file,
                                                      self.session,
                                                      self.thinking_dir)
        else:
            # Note: Polling is deprecated
            input_processor = PollingInputProcessor(self.default_prompt,
                                                    self.default_input,
                                                    self.input_timeout_seconds,
                                                    self.args.thinking_file,
                                                    self.session,
                                                    self.poll_timeout_seconds)

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
            state = input_processor.process_once(state)

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
        # What agent are we talking to?
        arg_parser.add_argument("--agent", type=str, default="esp_decision_assistant",
                                help="Name of the agent to talk to")

        # How are we connecting (if by service/sockets)?
        arg_parser.add_argument("--local", type=bool, default=True,
                                help="If True (the default), assume we are running against local container")
        arg_parser.add_argument("--host", type=str, default=None,
                                help="hostname setting if not running locally")
        arg_parser.add_argument("--port", type=int, default=AgentSession.DEFAULT_PORT,
                                help="TCP/IP port to run the Agent gRPC service on")

        # How are we capturing output?
        arg_parser.add_argument("--thinking_file", type=str, default="/tmp/agent_thinking.txt",
                                help="File that captures agent thinking. "
                                     "This is a separate text stream from the user/assistant chat")
        arg_parser.add_argument("--thinking_dir", default=False, action="store_true",
                                help="Use the basis of the thinking_file as a directory to capture "
                                     "internal agent chatter in separate files. "
                                     "This is a separate text stream from the user/assistant chat. "
                                     "Only available when streaming (the default).")

        # How can we get input to the chat client without typing it in?
        arg_parser.add_argument("--first_prompt_file", type=str,
                                help="File that captures the first response to the input prompt")
        arg_parser.add_argument("--sly_data", type=str,
                                help="JSON string containing data that is out-of-band to the chat stream, "
                                     "but is still essential to agent function")

        # How do we receive messages?
        arg_parser.add_argument("--stream", default=True, action="store_true",
                                help="Use streaming chat instead of polling")
        arg_parser.add_argument("--poll", dest="stream", action="store_false",
                                help="Use polling chat instead of streaming")

        # How do we set up our session connection?
        arg_parser.add_argument("--connection", default="direct", type=str,
                                choices=["service", "direct", "http"],
                                help="""
The type of connection to initiate. Choices are to connect to:
    "service"   - an agent service via gRPC. (The default).  Needs host and port.
    "http"      - an agent service via http. Needs host and port.
    "direct"    - a session via library.
All choices require an agent name.
""")
        arg_parser.add_argument("--service", dest="connection", action="store_const", const="service",
                                help="Use a service connection")
        arg_parser.add_argument("--direct", dest="connection", action="store_const", const="direct",
                                help="Use a direct/library call for the chat")

        # How do we handle calls to external agents?
        arg_parser.add_argument("--local_externals_direct", default=False, action="store_true",
                                help="""
Have external tools that can be found in the local agent manifest use a
direct connection instead of requiring a service to be stood up.
                                """)
        arg_parser.add_argument("--local_externals_service", dest="local_externals_direct", action="store_false",
                                help="""
Have external tools that can be found in the local agent manifest use a service connection
                                """)

        # How do we handle the number of rounds of input?
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
                                              hostname, self.args.port, self.args.local_externals_direct)

        # Clear out the previous thinking file/dir contents
        #
        # Incorrectly flagged as destination of Path Traversal 5
        #   Reason: thinking_file was previously checked with FileOfClass.check_file()
        #           which actually does the path traversal check. CheckMarx does not
        #           recognize pathlib as a valid library with which to resolve these kinds
        #           of issues.  Furthermore, this is a client command line tool that is never
        #           used inside servers which just happens to be part of a library offering.
        if not self.args.thinking_dir:
            with open(self.args.thinking_file, "w", encoding="utf-8") as thinking:
                thinking.write("\n")
        else:
            # Use the stem of the the thinking file (i.e. no ".txt" extention) as the
            # basis for the thinking directory
            self.thinking_dir, extension = os.path.splitext(self.args.thinking_file)
            _ = extension

            # Remove any contents that might be there already.
            # Writing over will existing dir will just confuse output.
            if os.path.exists(self.thinking_dir):
                shutil.rmtree(self.thinking_dir)
            # Create the directory anew
            os.makedirs(self.thinking_dir)

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


if __name__ == '__main__':
    AgentCli().main()
