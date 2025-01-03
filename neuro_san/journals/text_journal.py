
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
from typing import List
from typing import Union

from neuro_san.journals.journal import Journal


class TextJournal(Journal):
    """
    Journal implementation for capturing entries as a list of strings
    """

    def __init__(self):
        """
        Constructor
        """
        self.log_content = []

    async def write(self, entry: Union[str, bytes]):
        """
        :param entry: Add a string-ish entry to the logs.
                    Can be either a string or bytes.
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
