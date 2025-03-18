
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

from neuro_san.internals.filters.message_filter import MessageFilter
from neuro_san.internals.messages.chat_message_type import ChatMessageType


class CompoundMessageFilter(MessageFilter):
    """
    A MessageFilter implementation that can service multiple other MessageFilter instances
    """

    def __init__(self, filters: List[MessageFilter] = None):
        """
        Constructor

        :param filters: A List of MessageFilter instances to simultaneously service
        """
        self.filters: List[MessageFilter] = filters
        if self.filters is None:
            self.filters = []

    def allow_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType) -> bool:
        """
        Determine whether to allow the message through.
        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
        :return: True if the message should be allowed through to the client. False otherwise.
        """
        # If any one filter says to let a message through, then let it through.
        for one_filter in self.filters:
            if one_filter.allow_message(chat_message_dict, message_type):
                return True

        # Nobody wanted it.
        return False

    def add_message_filter(self, message_filter: MessageFilter):
        """
        Adds a message_filter to the list
        :param message_filter: A MessageFilter instance to service
        """
        self.filters.append(message_filter)
