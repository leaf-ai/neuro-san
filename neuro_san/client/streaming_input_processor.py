
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
from copy import copy

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

    def __init__(self,
                 default_input: str,
                 thinking_file: str,
                 session: AgentSession,
                 thinking_dir: str):
        """
        Constructor
        """
        super().__init__()
        self.default_input: str = default_input
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
        empty: Dict[str, Any] = {}
        user_input: str = state.get("user_input")
        last_chat_response = state.get("last_chat_response")
        num_input = state.get("num_input")
        chat_context = state.get("chat_context", empty)
        origin_str: str = ""

        if user_input is None or user_input == self.default_input:
            return state

        print(f"Sending user_input {user_input}")
        sly_data: Dict[str, Any] = state.get("sly_data")
        # Note that by design, a client does not have to interpret the
        # chat_context at all. It merely needs to pass it along to continue
        # the conversation.
        chat_request: Dict[str, Any] = self.formulate_chat_request(user_input, sly_data, chat_context)

        return_state: Dict[str, Any] = copy(state)
        chat_responses: Generator[Dict[str, Any], None, None] = self.session.streaming_chat(chat_request)
        for chat_response in chat_responses:

            session_id: str = chat_response.get("session_id")
            response: Dict[str, Any] = chat_response.get("response", empty)

            if session_id is not None:
                self.session_id = session_id

            # Convert the message type in the response to the enum we want to work with
            response_type: str = response.get("type")
            message_type: ChatMessageType = ChatMessageType.from_response_type(response_type)

            if message_type == ChatMessageType.AGENT_FRAMEWORK:
                # Update the chat context if there is something to update it with
                chat_context = response.get("chat_context", chat_context)

            # Process any text in the message
            origin: List[str] = response.get("origin")
            text: str = response.get("text")
            if text is not None:
                if message_type != ChatMessageType.LEGACY_LOGS:
                    # Now that we are sending messages from deep within the infrastructure,
                    # write those.  The LEGACY_LOGS messages should be redundant with these.
                    test_origin_str: str = Origination.get_full_name_from_origin(origin)
                    if test_origin_str is not None:
                        origin_str = test_origin_str
                    self.write_response(response, origin_str)
                if origin is not None and len(origin) == 1 and message_type == ChatMessageType.AI:
                    # The last message from the front man (origin len 1) that is an
                    # AI message is effectively "the answer".  This is what
                    # we want to communicate back to the user in an up-front fashion.
                    last_chat_response = text

        update = {
            "chat_context": chat_context,
            "num_input": num_input + 1,
            "last_chat_response": last_chat_response,
            "user_input": None,
            "sly_data": None,
        }
        return_state.update(update)

        print(f"\nResponse from {origin_str}:")
        print(f"{last_chat_response}")
        return return_state

    def write_response(self, response: Dict[str, Any], origin_str: str):
        """
        Writes a line of text attributable to the origin, however we are doing that.
        :param response: The message to write
        :param origin_str: The string representing the origin of the message
        """

        response_type: str = response.get("type")
        message_type: ChatMessageType = ChatMessageType.from_response_type(response_type)
        message_type_str: str = ChatMessageType.to_string(message_type)

        text: str = response.get("text")

        filename: str = self.thinking_file
        if self.thinking_dir:
            if origin_str is None:
                return
            filename = os.path.join(self.thinking_dir, origin_str)

        how_to_open_file: str = "a"
        if not os.path.exists(filename):
            how_to_open_file = "w"

        with open(filename, how_to_open_file, encoding="utf-8") as thinking:
            use_origin: str = ""
            tool_result_origin: List[Dict[str, Any]] = response.get("tool_result_origin")
            if tool_result_origin is not None:
                last_origin_only: List[Dict[str, Any]] = [tool_result_origin[-1]]
                origin_str = Origination.get_full_name_from_origin(last_origin_only)
                use_origin = f" from {origin_str}"
            if not self.thinking_dir:
                use_origin += f" from {origin_str}"
            thinking.write(f"\n[{message_type_str}{use_origin}]:\n")
            thinking.write(text)
            thinking.write("\n")
