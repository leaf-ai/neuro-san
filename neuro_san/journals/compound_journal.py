from typing import Any
from typing import List
from typing import Union

from neuro_san.journals.journal import Journal


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

    async def write(self, entry: Union[str, bytes]):
        """
        Writes a single string entry into each journal.
        """
        for journal in self.journals:
            await journal.write(entry)

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
