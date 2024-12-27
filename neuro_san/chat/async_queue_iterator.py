
from typing import Any
from typing import AsyncIterator
from typing import Dict

from asyncio.queues import Queue

# Constant for the end key
END_KEY: str = "end"

# Constant for the end message to be put in a Queue when all the messages are done
END_MESSAGE: Dict[str, Any] = {END_KEY: True}


class AsyncQueueIterator(AsyncIterator):

    def __init__(self, queue: Queue):
        self.queue: Queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self) -> Dict[str, Any]:
        message: Dict[str, Any] = await self.queue.get()
        if message.get(END_KEY) is not None:
            raise StopAsyncIteration

        return message
