
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


class ConnectivityReporter:
    """
    A class that knows how to report the connectivity of an entire
    AgentToolRegistry to a particular Journal
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
        # Get the list of agent names from the registry
        agent_names: List[str] = self.registry.get_agent_names()

        # Find out what the front man is called.
        front_man_spec: Dict[str, Any] = self.front_man.get_agent_tool_spec()
        front_man_name: str = self.registry.get_name_from_spec(front_man_spec)

        # Be sure the front man goes first in the list.
        # Remove it from the set, then insert at the beginning of the remaining list.
        agent_name_set: Set[str] = set(agent_names)
        agent_name_set.discard(front_man_name)
        agent_names = list(agent_name_set)
        agent_names.insert(0, front_man_name)

        # Report connectivity for each node in the graph
        for agent_name in agent_names:
            agent_spec: Dict[str, Any] = self.registry.get_agent_tool_spec(agent_name)
            await self.report_node_connectivity(agent_spec)

    async def report_node_connectivity(self, agent_spec: Dict[str, Any]):
        """
        Share the connectivity information of a single node in the network.
        :param agent_spec: The agent spec dictionary to report on
        """
        extractor = DictionaryExtractor(agent_spec)

        # Check to see if this node in the graph actually wants its connectivity
        # known to the outside world.
        allow_connectivity = bool(extractor.get("allow.connectivity", True))
        if not allow_connectivity:
            # Nothing to see here, please move along
            return

        # Keep a set of the combined sources of tools, so connectivity only gets
        # listed once.
        tool_set: Set[str] = set()

        # First check the tools of the run-of-the-mill agent spec
        empty_list: List[str] = []
        tools: List[str] = agent_spec.get("tools", empty_list)
        tool_set.update(tools)

        # Next check a special case convention where a coded tool takes a dictionary of
        # key/value pairs mapping function -> tool name.
        empty_dict: Dict[str, Any] = {}
        args_tools = extractor.get("args.tools", empty_dict)
        if isinstance(args_tools, Dict):
            args_tools = args_tools.values()
        if isinstance(args_tools, List):
            tool_set.update(args_tools)

        # Make a list from the set of tools
        tool_list: List[str] = list(tool_set)

        # Recall that an empty list evaluates to False
        if not bool(tool_list):
            # Nothing to see here, please move along
            return

        # Report the content of the tools list as a dictionary in JSON.
        tools_dict: Dict[str, Any] = {
            "tools": tool_list
        }
        content: str = json.dumps(tools_dict)
        message = AgentFrameworkMessage(content=content)

        # Report the origin as the agent itself, so any client that receives
        # the message has the correct context about the tools listed in the content.
        agent_name: str = self.registry.get_name_from_spec(agent_spec)
        await self.journal.write_message(message, origin=agent_name)
