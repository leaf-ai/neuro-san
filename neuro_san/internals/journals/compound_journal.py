
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


class CompoundJournal(Journal):
    """
    A Journal implementation that can service multiple other Journal instances
    """

    def __init__(self, journals: List[Journal] = None):
        """
        Constructor

        :param journals: A List of Journal instances to simultaneously service
        """
        self.journals: List[Journal] = journals
        if self.journals is None:
            self.journals = []

    async def write(self, entry: Union[str, bytes], origin: List[Dict[str, Any]]):
        """
        Writes a single string entry into each journal.
        :param entry: The logs entry to write
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with. Starts at 0.
        """
        for journal in self.journals:
            await journal.write(entry, origin)

    def get_logs(self) -> List[Any]:
        """
        :return: A list of strings corresponding to journal entries
                 from the first Journal instance in the list that will return something..
        """
        logs: List[Any] = None
        for journal in self.journals:
            logs = journal.get_logs()
            if logs is not None:
                break
        return logs

    def add_journal(self, journal: Journal):
        """
        Adds a journal to the list
        :param journal: A Journal instance to service
        """
        self.journals.append(journal)

    async def write_message(self, message: BaseMessage, origin: List[Dict[str, Any]]):
        """
        Writes a BaseMessage entry into the journal
        :param message: The BaseMessage instance to write to the journal
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with. Starts at 0.
        """
        for journal in self.journals:
            await journal.write_message(message, origin)
