from typing import Any


# pylint: disable=too-few-public-methods
class AsyncHopper:
    """
    An interface whose clients store things for later use.
    """

    async def put(self, item: Any):
        """
        :param item: The item to put in the hopper.
        """
        raise NotImplementedError
