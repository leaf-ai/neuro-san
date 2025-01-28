
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

from unittest import TestCase

from neuro_san.internals.chat.connectivity_reporter import ConnectivityReporter
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.internals.utils.file_of_class import FileOfClass


class TestConnectivityReporter(TestCase):
    """
    Unit tests for ConnectivityReporter class.
    """

    def test_assumptions(self):
        """
        Can we construct?
        """
        agent_tool_registry: AgentToolRegistry = None
        reporter = ConnectivityReporter(agent_tool_registry)
        self.assertIsNotNone(reporter)

    def get_sample_registry(self, hocon_file: str) -> AgentToolRegistry:
        """
        :param hocon_file: A hocon file reference within this repo
        """
        file_of_class = FileOfClass(__file__, "../../neuro_san/registries")
        file_reference = file_of_class.get_file_in_basis(hocon_file)
        restorer = AgentToolRegistryRestorer()
        agent_tool_registry: AgentToolRegistry = restorer.restore(file_reference=file_reference)
        return agent_tool_registry

    def test_hello_world(self):
        """
        Tests the connectivity of the hello world hocon
        """
        agent_tool_registry: AgentToolRegistry = self.get_sample_registry("hello_world.hocon")
        reporter = ConnectivityReporter(agent_tool_registry)

        messages: List[Dict[str, Any]] = reporter.report_network_connectivity()
        self.assertEqual(len(messages), 2)

        # First guy is the front-man and he only has a single tool
        connectivity: Dict[str, Any] = messages[0]
        self.assertIsNotNone(connectivity)

        tools: List[str] = connectivity.get("tools")
        self.assertIsNotNone(tools)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0], "synonymizer")

        # Next guy is the synonymizer and has no tools
        connectivity: Dict[str, Any] = messages[1]
        self.assertIsNotNone(connectivity)

        tools: List[str] = connectivity.get("tools")
        self.assertIsNotNone(tools)
        self.assertEqual(len(tools), 0)
