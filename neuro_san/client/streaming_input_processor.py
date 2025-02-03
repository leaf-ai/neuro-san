
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
from typing import List

import os

from neuro_san.client.abstract_input_processor import AbstractInputProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.internals.messages.origination import Origination


# pylint: disable=too-many-arguments,too-many-positional-arguments
class StreamingInputProcessor(AbstractInputProcessor):
    """
    Processes AgentCli input by using the neuro-san streaming API.
    """

    def __init__(self, default_prompt: str,
                 default_input: str,
                 input_timeout_seconds: float,
                 thinking_file: str,
                 session: AgentSession,
                 thinking_dir: str):
        """
        Constructor
        """
        super().__init__()
        self.default_prompt: str = default_prompt
        self.default_input: str = default_input
        self.input_timeout_seconds: float = input_timeout_seconds
        self.thinking_file: str = thinking_file
        self.thinking_dir: str = thinking_dir
        self.session: AgentSession = session

    # pylint: disable=too-many-locals
    def process_once(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use polling strategy to communicate with agent.
        :param state: The state dictionary to pass around
        :return: An updated state dictionary
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
            origin: List[str] = response.get("origin")
            origin_str: str = Origination.get_full_name_from_origin(origin)

            # Update chat response and maybe prompt.
            if text is not None:
                if message_type == ChatMessageType.LEGACY_LOGS:
                    self.write_text(text, origin_str)
                else:
                    print(f"Response from {origin_str}:")
                    print(f"{text}")
                    last_chat_response = text

            return_state = {
                "last_logs": last_logs,
                "last_chat_response": last_chat_response,
                "prompt": self.default_prompt,
                "timeout": self.input_timeout_seconds,
                "num_input": num_input + 1
            }

        return return_state

    def write_text(self, text: str, origin_str: str):
        """
        Writes a line of text attributable to the origin, however we are doing that.
        :param text: The text of the message
        :param origin_str: The string representing the origin of the message
        """

        filename: str = self.thinking_file
        if self.thinking_dir:
            filename = os.path.join(self.thinking_dir, origin_str)

        how_to_open_file: str = "a"
        if not os.path.exists(filename):
            how_to_open_file = "w"

        with open(filename, how_to_open_file, encoding="utf-8") as thinking:
            if not self.thinking_dir:
                thinking.write(f"[{origin_str}]:\n")
            thinking.write(text)
            thinking.write("\n")
