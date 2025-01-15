
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
from typing import List
from typing import Union

from langchain_core.messages.base import BaseMessage


class Journal:
    """
    An interface for journaling chat messages.
    """

    async def write(self, entry: Union[str, bytes]):
        """
        Writes a single string entry into the journal.
        """
        raise NotImplementedError

    def get_logs(self) -> List[Any]:
        """
        :return: A list of strings corresponding to journal entries.
        """
        raise NotImplementedError

    async def write_message(self, message: BaseMessage):
        """
        Writes a BaseMessage entry into the journal
        :param message: The BaseMessage instance to write to the journal
        """
        raise NotImplementedError
