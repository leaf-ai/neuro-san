
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


class TextJournal(Journal):
    """
    Journal implementation for capturing entries as a list of strings
    """

    def __init__(self, logs: List[Any] = None):
        """
        Constructor
        """
        self.log_content = logs
        if logs is None:
            self.log_content = []

    async def write(self, entry: Union[str, bytes], origin: List[Dict[str, Any]]):
        """
        :param entry: Add a string-ish entry to the logs.
                    Can be either a string or bytes.
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        # Decoding bytes to string if necessary
        if isinstance(entry, bytes):
            entry = entry.decode('utf-8')
        self.log_content.append(entry)

    def get_logs(self) -> List[str]:
        """
        :return: A list of strings corresponding to log entries written with write()
        """
        return self.log_content

    async def write_message(self, message: BaseMessage, origin: List[Dict[str, Any]]):
        """
        Writes a BaseMessage entry into the journal
        :param message: The BaseMessage instance to write to the journal
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        # Do nothing
        _ = message, origin

    def set_logs(self, logs: List[Any]):
        """
        :param logs: A list of strings corresponding to journal entries.
        """
        self.log_content = logs
