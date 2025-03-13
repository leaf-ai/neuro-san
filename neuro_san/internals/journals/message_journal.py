
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

from neuro_san.internals.interfaces.async_hopper import AsyncHopper
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.legacy_logs_message import LegacyLogsMessage
from neuro_san.internals.messages.message_utils import convert_to_chat_message


class MessageJournal(Journal):
    """
    Journal implementation for putting entries into a Hopper
    for storage for later processing.
    """

    def __init__(self, hopper: AsyncHopper):
        """
        Constructor

        :param hopper: A handle to an AsyncHopper implementation, onto which
                       any message will be put().
        """
        self.hopper: AsyncHopper = hopper

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

        legacy = LegacyLogsMessage(content=entry)
        await self.write_message(legacy, origin)

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
        message_dict: Dict[str, Any] = convert_to_chat_message(message, origin)

        # Queue Producer from this:
        #   https://stackoverflow.com/questions/74130544/asyncio-yielding-results-from-multiple-futures-as-they-arrive
        await self.hopper.put(message_dict)
