
from typing import Any
from typing import AsyncIterator
from typing import Dict

from asyncio.queues import Queue

# Constant for the end key
END_KEY: str = "end"

# Constant for the end message to be put in a Queue when all the messages are done
END_MESSAGE: Dict[str, Any] = {END_KEY: True}


class AsyncQueueIterator(AsyncIterator[Dict[str, Any]]):
    """
    AsyncIterator instance to asynchronously iterate over/consume the contents of
    a Queue as they come in.
    """

    def __init__(self, queue: Queue):
        """
        Constructor

        :param queue: The queue we will be iterating over.
        """
        self.queue: Queue = queue

    def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Self-identify as an AsyncIterator when called upon by
        the Python async framework.
        """
        return self

    async def __anext__(self) -> Dict[str, Any]:
        """
        Per the convention, we look for an END_MESSAGE dictionary on the queue
        that indicates its time to stop the iteration.
        :return: Blocks waiting to return the next dictionary message on the queue.
                Will throw StopAsyncIteration when an end queue message is detected.
        """
        message: Dict[str, Any] = await self.queue.get()
        if message.get(END_KEY) is not None:
            raise StopAsyncIteration

        return message
