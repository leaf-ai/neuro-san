
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
from typing import Union

from langchain_core.messages.base import BaseMessage

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.message_utils import is_relevant_to_chat_history


class OriginatingJournal(Journal):
    """
    A Journal implementation that has an origin.
    """

    def __init__(self, wrapped_journal: Journal,
                 origin: List[Dict[str, Any]],
                 chat_history: List[BaseMessage] = None):
        """
        Constructor

        :param wrapped_journal: The Journal that this implementation wraps
        :param origin: The origin that will be applied to all messages.
        :param chat_history: The chat history list instance to store write_message() results in.
                            Can be None (the default).
        """
        self.wrapped_journal: Journal = wrapped_journal
        self.origin: List[Dict[str, Any]] = origin
        self.chat_history: List[BaseMessage] = chat_history

    async def write(self, entry: Union[str, bytes], origin: List[Dict[str, Any]] = None):
        """
        Writes a single string entry into the wrapped_journal.
        :param entry: The logs entry to write
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
                For this particular implementation we expect this to be None
        """
        use_origin: List[Dict[str, Any]] = self.origin
        if origin is not None:
            use_origin = origin
        await self.wrapped_journal.write(entry, use_origin)

    def get_logs(self) -> List[Any]:
        """
        :return: A list of strings corresponding to wrapped_journal entries.
        """
        # Pass-through
        return self.wrapped_journal.get_logs()

    async def write_message(self, message: BaseMessage, origin: List[Dict[str, Any]] = None):
        """
        Writes a BaseMessage entry into the wrapped_journal
        and appends to the chat history.

        :param message: The BaseMessage instance to write to the wrapped_journal
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
                For this particular implementation we expect this to be None
        """
        use_origin: List[Dict[str, Any]] = self.origin
        if origin is not None:
            use_origin = origin

        if self.chat_history is not None and is_relevant_to_chat_history((message):
            self.chat_history.append(message)
        await self.wrapped_journal.write_message(message, use_origin)

    def get_chat_history(self) -> List[BaseMessage]:
        """
        :return: The chat history list of base messages associated with the instance.
        """
        return self.chat_history
