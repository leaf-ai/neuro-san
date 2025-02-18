
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

from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.message_processing.message_processor import MessageProcessor


class ChatContextMessageProcessor(MessageProcessor):
    """
    Implementation of the MessageProcessor that looks for the chat_context
    in the stream which is used to continue the conversation.
    """

    def __init__(self):
        """
        Constructor
        """
        self.chat_context: Dict[str, Any] = {}

    def get_chat_context(self) -> Dict[str, Any]:
        """
        :return: The chat_context discovered from the agent session interaction
                Empty dictionaries or None values simply start a new conversation.
        """
        return self.chat_context

    def reset(self):
        """
        Resets any previously accumulated state
        """
        self.chat_context = {}

    def process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType):
        """
        Process the message.
        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
        """
        if message_type != ChatMessageType.AGENT_FRAMEWORK:
            # chat_context only ever comes from AGENT_FRAMEWORK Messages
            return

        # Normally the very last message holds the chat_context.
        # Keep accumulating until it comes past, as long as there is something.
        self.chat_context = chat_message_dict.get("chat_context", self.chat_context)
