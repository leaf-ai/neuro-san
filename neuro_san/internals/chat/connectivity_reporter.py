
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

from leaf_common.parsers.dictionary_extractor import DictionaryExtractor

from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.run_context.utils.external_tool_adapter import ExternalToolAdapter


class ConnectivityReporter:
    """
    A class that knows how to report the connectivity of an entire
    AgentToolRegistry.

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
        Such a node will itself be reported, but with an empty tool list.
    *   External agents are reported but with an empty tool list.
        No effort to discover their internal connectivity is attempted.
        Maybe someday.
    """

    def __init__(self, registry: AgentToolRegistry):
        """
        Constructor

        :param registry: The AgentToolRegistry to use.
        """

        self.registry: AgentToolRegistry = registry

    def report_network_connectivity(self) -> List[Dict[str, Any]]:
        """
        Share the connectivity information of the agent network in question
        :return: A list of connectivity information dictionaries each with the following keys:
            * origin  - The agent network node whose connectivity is being described
            * tools   - A list of tool nodes that are possible to reach from the origin

                        This might include references into external agent networks, perhaps hosted
                        on other servers.  Separate calls to those guys will need to be made
                        in order to gain information about their own connectivity, if this is
                        actually desired by the client.

                        Worth noting that server-side agent descriptions are allowed to
                        withhold connectivity info they deem private, or too much of an
                        implementation detail.  That is, connectivity reported is only
                        as much as the server wants a client to know.
        """
        # Find the name of the front-man as a root node
        front_man: str = self.registry.find_front_man()

        # Do a breadth-first traversal starting with the front-man
        reported_agents: Set[str] = set()
        connectivity: List[Dict[str, Any]] = self.report_node_connectivity(front_man, reported_agents)
        return connectivity

    def report_node_connectivity(self, agent_name: str, reported_agents: Set[str]) -> List[Dict[str, Any]]:
        """
        Share the connectivity information of a single node in the network.
        :param agent_name: The name of the agent spec dictionary to report on
        :param reported_agents: A list of agents that have been reported already.
                Prevents cycles.
        :return: A list of connectivity information dictionaries.
        """

        connectivity_list: List[Dict[str, Any]] = []
        agent_spec: Dict[str, Any] = None

        if not ExternalToolAdapter.is_external_agent(agent_name):

            # This is not an external agent, so get its spec to report on
            agent_spec: Dict[str, Any] = self.registry.get_agent_tool_spec(agent_name)
            if agent_spec is None:
                # The agent referred to by the caller is not actually in the registry.
                # As a hint, don't report anything, not even an empty tool list.
                return connectivity_list

            # Check to see if this node in the graph actually wants its connectivity
            # known to the outside world.
            extractor = DictionaryExtractor(agent_spec)
            allow_connectivity = bool(extractor.get("allow.connectivity", True))
            if not bool(allow_connectivity):

                # We are not allowing connectivity reporting from here on down
                agent_spec = None

        # Compile a tool list of what is referred to by the agent_spec.
        # For many reasons, this list could be empty.
        tool_list: List[str] = self.assemble_tool_list(agent_spec)

        connectivity_dict: Dict[str, Any] = {
            # Report the origin as the agent itself, so any client that receives
            "origin": agent_name,
            # Report the content of the tools list
            "tools": tool_list
        }

        # the message has the correct context about the tools listed in the content.
        reported_agents.add(agent_name)
        connectivity_list.append(connectivity_dict)

        # Recurse for a bread-first search.
        for tool in tool_list:
            # Don't report more than once for the same node to avoid cycles.
            if tool not in reported_agents:
                new_list: List[Dict[str, Any]] = self.report_node_connectivity(tool, reported_agents)
                if len(new_list) > 0:
                    connectivity_list.extend(new_list)

        return connectivity_list

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
