
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

from copy import copy

from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.message_processing.message_processor import MessageProcessor


class ChatHistoryMessageProcessor(MessageProcessor):
    """
    MessageProcessor implementation for processing a single message
    in a chat history.
    """

    def __init__(self):
        """
        Constructor
        """
        self.message_history: List[Dict[str, Any]] = []
        self.saw_first_system: bool = False

    def get_message_history(self) -> List[Dict[str, Any]]:
        """
        :return: The filtered message history
        """
        return self.message_history

    def process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType):
        """
        Process the message.
        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
        """
        if message_type not in (ChatMessageType.HUMAN, ChatMessageType.SYSTEM, ChatMessageType.AI):
            # Don't send any messages over the wire that won't be re-ingestable.
            return

        transformed_message_dict: Dict[str, Any] = chat_message_dict
        if not self.saw_first_system and message_type is ChatMessageType.SYSTEM:
            transformed_message_dict = self.redact_instructions(chat_message_dict)
            self.saw_first_system = True
        else:
            transformed_message_dict = self.transform_message(chat_message_dict)

        self.message_history.append(transformed_message_dict)

    def redact_instructions(self, chat_message_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redacts the text instructions of the given system message.
        These will get replaced by the agent's instructions anyway to preserve
        server-side intent.
        """
        redacted: Dict[str, Any] = copy(chat_message_dict)
        redacted["text"] = "<redacted>"
        return redacted

    def transform_message(self, chat_message_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a message such that it can be re-ingested by the system nicely.
        """
        transformed: Dict[str, Any] = copy(chat_message_dict)
        text: str = transformed.get("text")

        # Braces are a problem for chat history being read back into the system
        # if they are not properly escaped.

        # First replace any escaped braces with normal braces
        text = text.replace(r"\{", "{")
        text = text.replace(r"\}", "}")

        # Now replace normal braces with escaped braces.
        # Idea is to catch everything pre-escaped or not
        text = text.replace("{", r"\{")
        text = text.replace("}", r"\}")

        transformed["text"] = text
        return transformed
