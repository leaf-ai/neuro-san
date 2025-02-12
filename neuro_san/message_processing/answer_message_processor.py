
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
from typing import List

from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.message_processing.message_processor import MessageProcessor


class AnswerMessageProcessor(MessageProcessor):
    """
    Implementation of the MessageProcessor that looks for "the answer"
    of the chat session.
    """

    def __init__(self):
        """
        Constructor
        """
        self.answer: str = None
        self.answer_origin: List[Dict[str, Any]] = None

    def get_answer(self) -> str:
        """
        :return: The final answer from the agent session interaction
        """
        return self.answer

    def get_answer_origin(self) -> List[Dict[str, Any]]:
        """
        :return: The origin of the final answer from the agent session interaction
        """
        return self.answer_origin

    def reset(self):
        """
        Resets any previously accumulated state
        """
        self.answer = None
        self.answer_origin = None

    def process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType):
        """
        Process the message.
        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
        """
        if message_type != ChatMessageType.AI:
            # Final answers are only ever AI Messages
            return

        origin: List[Dict[str, Any]] = chat_message_dict.get("origin")
        if origin is None or len(origin) != 1:
            # Final answers only come from the FrontMan,
            # whose origin length is the only one of length 1.
            return

        text = chat_message_dict.get("text")
        if text is None:
            # Final answers need to be text (for now).
            # There might be more options in the future.
            return

        # Record what we got.
        # We might get another as we go along, but the last message in the stream
        # meeting the criteria above is our final answer.
        self.answer = text
        self.answer_origin = origin
