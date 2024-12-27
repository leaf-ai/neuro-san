form typing import Any


class AsyncHopper:
    """
    An interface whose clients store things for later use.
    """

    async put(self, item: Any):
        """
        :param item: The item to put in the hopper.
        """
        raise NotImplementedError
