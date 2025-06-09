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

from neuro_san.internals.interfaces.front_man import FrontMan


class AgentRegistry:
    """
    Interface that describes how the session-level of the system interacts with
    a registry of agents.
    """

    def create_front_man(self, sly_data: Dict[str, Any], parent_run_context: object = None) -> FrontMan:
        """
        Find and create the FrontMan for chat

        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
        :param parent_run_context: A RunContext instance
        """
        raise NotImplementedError

    def find_front_man(self) -> str:
        """
        :return: A single tool name to use as the root of the chat agent.
                 This guy will be user facing.  If there are none or > 1,
                 an exception will be raised.
        """
        raise NotImplementedError

    def get_agent_tool_spec(self, name: str) -> Dict[str, Any]:
        """
        :param name: The name of the agent tool to get out of the registry
        :return: The dictionary representing the spec registered agent
        """
        raise NotImplementedError
