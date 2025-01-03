from typing import List

from neuro_san.interfaces.async_hopper import AsyncHopper
from neuro_san.journals.compound_journal import CompoundJournal
from neuro_san.journals.journal import Journal
from neuro_san.journals.message_journal import MessageJournal
from neuro_san.journals.text_journal import TextJournal


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
