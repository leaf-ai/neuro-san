
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

from neuro_san.client.abstract_input_processor import AbstractInputProcessor
from neuro_san.client.thinking_file_message_processor import ThinkingFileMessageProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.messages.origination import Origination
from neuro_san.message_processing.basic_message_processor import BasicMessageProcessor


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
        self.session: AgentSession = session
        self.processor = BasicMessageProcessor()
        self.processor.add_processor(ThinkingFileMessageProcessor(thinking_file, thinking_dir))

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
        self.processor.reset()

        return_state: Dict[str, Any] = copy(state)
        chat_responses: Generator[Dict[str, Any], None, None] = self.session.streaming_chat(chat_request)
        for chat_response in chat_responses:

            response: Dict[str, Any] = chat_response.get("response", empty)

            self.processor.process_message(response)

            # Update the state if there is something to update it with
            chat_context = self.processor.get_chat_context()
            last_chat_response = self.processor.get_answer()
            origin_str = Origination.get_full_name_from_origin(self.processor.get_answer_origin())

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
