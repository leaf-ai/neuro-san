
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
from typing import Type

from neuro_san.internals.filters.maximal_message_filter import MaximalMessageFilter
from neuro_san.internals.filters.message_filter import MessageFilter
from neuro_san.internals.filters.minimal_message_filter import MinimalMessageFilter

TYPE_TO_MESSAGE_FILTER_CLASS: Dict[Any, Type[MessageFilter]] = {
    0:  MinimalMessageFilter,
    1:  MinimalMessageFilter,
    2:  MaximalMessageFilter,

    "UNKNOWN":  MinimalMessageFilter,
    "MINIMAL":  MinimalMessageFilter,
    "MAXIMAL":  MaximalMessageFilter,
}


class MessageFilterFactory:
    """
    Class for creating MessageFilters
    """

    @staticmethod
    def create_message_filter(chat_filter: Dict[str, Any]) -> MessageFilter:
        """
        :param chat_filter: The ChatFilter dictionary to process.
        :return: A MessageFilter that corresponds to the contents
        """

        # For now the default is MAXIMAL simply to emulate current behavior.
        # After the ChatFilter API gets released this will eventually change to "MINIMAL".
        default: str = "MINIMAL"
        chat_filter_type: Any = default

        # Get what was in the request
        if chat_filter is not None:
            chat_filter_type = chat_filter.get("chat_filter_type", chat_filter_type)

        # Change strings so they are suitable for lookup
        if isinstance(chat_filter_type, str):
            chat_filter_type = chat_filter_type.upper()

        chat_filter_class: MessageFilter = TYPE_TO_MESSAGE_FILTER_CLASS.get(chat_filter_type)
        if chat_filter_class is None:
            chat_filter_class = TYPE_TO_MESSAGE_FILTER_CLASS.get(default)

        # Instantiate the class and return
        message_filter: MessageFilter = chat_filter_class()
        return message_filter
