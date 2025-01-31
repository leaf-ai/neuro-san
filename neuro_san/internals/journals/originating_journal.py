
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


class OriginatingJournal(Journal):
    """
    A Journal implementation that has an origin.
    """

    def __init__(self, journal: Journal, origin: List[Dict[str, Any]]):
        """
        Constructor

        :param journal: The Journal that this implementation wraps
        :param origin: The origin that will be applied to all messages.
        """
        self.journal: Journal = journal
        self.origin: List[Dict[str, Any]] = origin

    async def write(self, entry: Union[str, bytes], origin: List[Dict[str, Any]] = None):
        """
        Writes a single string entry into the journal.
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
        self.journal.write(entry, use_origin)

    def get_logs(self) -> List[Any]:
        """
        :return: A list of strings corresponding to journal entries.
        """
        # Pass-through
        return self.journal.get_logs()

    async def write_message(self, message: BaseMessage, origin: List[Dict[str, Any]] = None):
        """
        Writes a BaseMessage entry into the journal
        :param message: The BaseMessage instance to write to the journal
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
        self.journal.write_message(message, use_origin)
