
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

from neuro_san.internals.interfaces.async_hopper import AsyncHopper
from neuro_san.internals.journals.compound_journal import CompoundJournal
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.journals.message_journal import MessageJournal
from neuro_san.internals.journals.text_journal import TextJournal


class CompatibilityJournal(CompoundJournal):
    """
    A concreate CompoundJournal implementation that services
    Journal instances needed for servicing streaming and polling chat.
    """

    def __init__(self, hopper: AsyncHopper):
        """
        Constructor
        """
        journals: List[Journal] = [
            TextJournal(),
            MessageJournal(hopper)
        ]
        super().__init__(journals=journals)
