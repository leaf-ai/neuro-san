
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


class ChatMessageConverter:
    """
    Helper class to prepare chat response messages
    for external clients consumption.
    """

    @classmethod
    def convert(cls, response_dict: Dict[str, Any]):
        """
        Convert chat response message to a format expected by external clients:
        :param response_dict: chat response message to be sent out
        """
        # Ensure that we return ChatMessageType as a string in output json
        message_dict: Dict[str, Any] = response_dict.get('response', None)
        if message_dict is not None:
            ChatMessageConverter.convert_message(message_dict)

    @classmethod
    def convert_message(cls, message_dict: Dict[str, Any]):
        """
        Convert chat message to a format expected by external clients:
        :param message_dict: chat message to process
        """
        # Ensure that we return ChatMessageType as a string in output json
        response_type = message_dict.get('type', None)
        if response_type is not None:
            message_dict['type'] =\
                ChatMessageType.from_response_type(response_type).name
        chat_context: Dict[str, Any] = message_dict.get('chat_context', None)
        if chat_context is not None:
            for chat_history in chat_context.get("chat_histories", []):
                for chat_message in chat_history.get("messages", []):
                    ChatMessageConverter.convert_message(chat_message)
