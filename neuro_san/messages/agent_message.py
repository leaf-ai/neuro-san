from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Union

from langchain_core.messages.base import BaseMessage


class AgentMessage(BaseMessage):
    """
    BaseMessage implementation of a message from an agent
    """

    type: Literal["agent"] = "agent"

    def __init__(self, content: Union[str, List[Union[str, Dict]]], **kwargs: Any) -> None:
        """
        Pass in content as positional arg.

        Args:
            content: The string contents of the message.
            kwargs: Additional fields to pass to the
        """
        super().__init__(content=content, **kwargs)
