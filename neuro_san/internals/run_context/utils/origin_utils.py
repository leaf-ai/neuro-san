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

from neuro_san.internals.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.interfaces.tool_caller import ToolCaller


class OriginUtils:
    """
    Static utility class for common code that manipulates origin information.
    """

    @staticmethod
    def add_spec_name_to_origin(origin: List[str], tool_caller: ToolCaller) -> List[str]:
        """
        Adds the agent name to the origin.
        :param origin: A list of strings determining an origin of a chat message
        :param tool_caller: The ToolCaller whose agent name is to be added to the list.
        :return: The new origin with the agent name at the end of the list
        """
        if origin is None:
            origin = []

        # Add the name from the spec to the origin, if we have it.
        if tool_caller is not None:
            agent_spec: Dict[str, Any] = tool_caller.get_agent_tool_spec()
            factory: AgentToolFactory = tool_caller.get_factory()
            agent_name: str = factory.get_name_from_spec(agent_spec)
            origin.append(agent_name)

        return origin

    @staticmethod
    def get_full_name_from_origin(origin: List[str]) -> str:
        """
        :param origin: A list of strings determining an origin of a chat message
        :return: A single string name given an origin path/list
        """
        # Connect all the elements of the origin by the delimiter "."
        name: str = ".".join(origin)
        # Simple replacement of local external agents.
        # DEF - need better recognition of external agent
        name = name.replace("./", "/")
        return name
