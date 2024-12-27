from typing import Any
from typing import List
from typing import Union


class Journal:
    """
    An interface for journaling chat messages.
    """

    def write(self, entry: Union[str, bytes]):
        """
        Writes a single string entry into the journal.
        """
        raise NotImplementedError

    def get_logs(self) -> List[Any]:
        """
        :return: A list of strings corresponding to journal entries.
        """
        raise NotImplementedError
