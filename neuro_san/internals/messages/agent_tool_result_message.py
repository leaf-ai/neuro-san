
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
from typing import Literal
from typing import Union

from langchain_core.messages.ai import AIMessage


class AgentToolResultMessage(AIMessage):
    """
    BaseMessage implementation of a message that came as a result from a tool.
    We use AIMessage class as a basis so that langchain can interpret the content
    correctly.  The extra field that we add here is an origin list to indicate
    where the the tool result came from.
    """

    type: Literal["agent_tool_result"] = "agent_tool_result"

    def __init__(self, content: Union[str, List[Union[str, Dict]]],
                 tool_result_origin: List[Dict[str, Any]],
                 **kwargs: Any) -> None:
        """
        Pass in content as positional arg.

        Args:
            content: The string contents of the message.
            tool_result_origin: The origin describing where the tool result came from
            kwargs: Additional fields to pass to the
        """
        super().__init__(content=content, **kwargs)
        self.tool_result_origin: List[Dict[str, Any]] = tool_result_origin
