
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
from typing import Set

import json

from leaf_common.parsers.dictionary_extractor import DictionaryExtractor

from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.tools.front_man import FrontMan
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.agent_framework_message import AgentFrameworkMessage
from neuro_san.internals.run_context.utils.external_tool_adapter import ExternalToolAdapter


class ConnectivityReporter:
    """
    A class that knows how to report the connectivity of an entire
    AgentToolRegistry to a particular Journal.

    Connectivity information comes as a series of AgentFramework
    messages, each of whose origin field reflects the name of the
    node and the content of the message is a JSON structure
    containing the list of tools that the node is connected to.

    *   The FrontMan is always sent first.
    *   Subsequent tool reporting proceeds in a breadth-first search, as per the
        ordering of the tools laid out in each agent spec.
    *   Cycles in the graph are mentioned in the tool reporting, but any node
        is only ever reported once.
    *   Hocon files can elect to hide the connectivity information from this reporting
        from any level on downstream by adding this block:
            "allow": {
                "connectivity": False
            }
        ...so if a network does not want connectivity reported at all, then this is only
        required in the front man's spec.
    *   External agent's connectivity is not reported. Maybe someday.
    """

    def __init__(self, registry: AgentToolRegistry,
                 front_man: FrontMan,
                 journal: Journal):
        """
        Constructor

        :param registry: The AgentToolRegistry to use.
        :param front_man: The pre-determined front man agent.
        :param journal: The Journal that captures messages for user output
        """

        self.registry: AgentToolRegistry = registry
        self.front_man: FrontMan = front_man
        self.journal: Journal = journal

    async def report_network_connectivity(self):
        """
        Share the connectivity information of the agent network in question
        """

        # Do a breadth-first traversal starting with the front-man
        front_man_spec: Dict[str, Any] = self.front_man.get_agent_tool_spec()
        front_man_name: str = self.registry.get_name_from_spec(front_man_spec)

        reported_agents: Set[str] = set()
        await self.report_node_connectivity(front_man_name, reported_agents)

    async def report_node_connectivity(self, agent_name: str, reported_agents: Set[str]):
        """
        Share the connectivity information of a single node in the network.
        :param agent_name: The name of the agent spec dictionary to report on
        :param reported_agents: A list of agents that have been reported already.
                Prevents cycles.
        """

        agent_spec: Dict[str, Any] = None

        if not ExternalToolAdapter.is_external_agent(agent_name):

            # This is not an external agent, so get its spec to report on
            agent_spec: Dict[str, Any] = self.registry.get_agent_tool_spec(agent_name)
            extractor = DictionaryExtractor(agent_spec)

            # Check to see if this node in the graph actually wants its connectivity
            # known to the outside world.
            allow_connectivity = bool(extractor.get("allow.connectivity", True))
            if not bool(allow_connectivity):

                # We are not allowing connectivity reporting from here on down
                agent_spec = None

        # Compile a tool list of what is referred to by the agent_spec.
        # For many reasons, this list could be empty.
        tool_list: List[str] = self.assemble_tool_list(agent_spec)

        # Report the content of the tools list as a dictionary in JSON.
        tools_dict: Dict[str, Any] = {
            "tools": tool_list
        }
        content: str = f"```json\n{json.dumps(tools_dict)}```"
        message = AgentFrameworkMessage(content=content)

        # Report the origin as the agent itself, so any client that receives
        # the message has the correct context about the tools listed in the content.
        await self.journal.write_message(message, origin=agent_name)
        reported_agents.add(agent_name)

        # Recurse for a bread-first search.
        for tool in tool_list:
            # Don't report more than once for the same node to avoid cycles.
            if tool not in reported_agents:
                await self.report_node_connectivity(tool, reported_agents)

    @staticmethod
    def assemble_tool_list(agent_spec: Dict[str, Any]) -> List[str]:
        """
        :param agent_spec: The agent spec to assemble a tool list from.
        :return: A list of tool names referred to by the agent spec.
        """

        # Keep a list of the tools to respect the ordering they were specified.
        tool_list: List[str] = []

        if agent_spec is None:
            # Nothing to report
            return tool_list

        extractor = DictionaryExtractor(agent_spec)

        # Keep a set of the combined sources of tools,
        # so connectivity only gets reported once.
        tool_set: Set[str] = set()

        # First check the tools of the run-of-the-mill agent spec
        empty_list: List[str] = []
        spec_tools: List[str] = extractor.get("tools", empty_list)

        # Add to our list in order, but without repeats
        for tool in spec_tools:
            if tool not in tool_set:
                tool_set.add(tool)
                tool_list.append(tool)

        # Next check a special case convention where a coded tool takes a dictionary of
        # key/value pairs mapping function -> tool name.
        empty_dict: Dict[str, Any] = {}
        args_tools = extractor.get("args.tools", empty_dict)

        if isinstance(args_tools, Dict):
            args_tools = args_tools.values()

        if isinstance(args_tools, List):
            # Add to our list in order, but without repeats
            for tool in args_tools:
                if tool not in tool_set:
                    tool_set.add(tool)
                    tool_list.append(tool)

        return tool_list
