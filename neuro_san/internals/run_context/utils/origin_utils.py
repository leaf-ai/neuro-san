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

from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller


class OriginUtils:
    """
    Static utility class for common code that manipulates origin information.

    A full origin description is a List of Dictionaries indicating the origin of a chat message.
    An origin can be considered a path to the original call to the front-man.
    Origin dictionaries themselves each have the following keys:
        "tool"                  The string name of the tool in the spec
        "instantiation_index"   An integer indicating which incarnation
                                of the tool is being dealt with. Starts at 0.
    """

    NUM_INSTANTIATION_INDEX_DIGITS: int = 2

    @staticmethod
    def add_spec_name_to_origin(origin: List[Dict[str, Any]], tool_caller: ToolCaller) \
            -> List[Dict[str, Any]]:
        """
        Adds the agent name to the origin.
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with. Starts at 0.
        :param tool_caller: The ToolCaller whose agent name is to be added to the list.
        :return: The new origin with the agent name at the end of the list
        """
        if origin is None:
            origin = []

        # Add the name from the spec to the origin, if we have it.
        if tool_caller is not None:
            # Get the agent name
            agent_spec: Dict[str, Any] = tool_caller.get_agent_tool_spec()
            factory: AgentToolFactory = tool_caller.get_factory()
            agent_name: str = factory.get_name_from_spec(agent_spec)

            # Prepare the origin dictionary to append
            origin_dict: Dict[str, Any] = {
                "tool": agent_name,
                "instatiation_index": 0
            }
            origin.append(origin_dict)

        return origin

    @staticmethod
    def get_full_name_from_origin(origin: List[Dict[str, Any]]) -> str:
        """
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with. Starts at 0.
        :return: A single string name given an origin path/list
        """
        if origin is None:
            return None

        # Connect all the elements of the origin by the delimiter "."
        origin_list: List[str] = []
        for origin_dict in origin:

            # Get basic fields from the dict
            instantiation_index: int = origin_dict.get("instantiation_index", 0)
            tool: str = origin_dict.get("tool")
            if tool is None:
                # No information of value will be conveyed with no tool set in the dict.
                raise ValueError("tool name in origin_dict is None")

            # Figure out how we will deal with the index
            index_str: str = ""
            if instantiation_index > 0:
                # zfill() adds leading 0's up to the number of characters provided
                index_str = f"-{str(instantiation_index).zfill(OriginUtils.NUM_INSTANTIATION_INDEX_DIGITS)}"

            # Figure out the single origin string
            origin_str: str = f"{tool}{index_str}"
            origin_list.append(origin_str)

        full_path: str = ".".join(origin_list)

        # Simple replacement of local external agents.
        # DEF - need better recognition of external agent
        full_path = full_path.replace("./", "/")

        return full_path
