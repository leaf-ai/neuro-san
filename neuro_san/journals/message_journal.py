
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

from neuro_san.interfaces.async_hopper import AsyncHopper
from neuro_san.journals.journal import Journal
from neuro_san.messages.legacy_logs_message import LegacyLogsMessage


class MessageJournal(Journal):
    """
    Journal implementation for capturing entries as a list of strings
    """

    def __init__(self, hopper: AsyncHopper):
        """
        Constructor

        :param hopper: A handle to an AsyncHopper implementation, onto which
                       any message will be put().
        """
        self.hopper = hopper

    async def write(self, message: Union[str, bytes]):
        """
        :param message: Add a message to the logs.
                    Can be either a string or bytes.
        """
        # Decoding bytes to string if necessary
        if isinstance(message, bytes):
            message = message.decode('utf-8')

        legacy = LegacyLogsMessage(content=message)
        await self.hopper.put(legacy)

    def get_logs(self) -> List[str]:
        """
        :return: A list of strings corresponding to log entries written with write()
        """
        return None
