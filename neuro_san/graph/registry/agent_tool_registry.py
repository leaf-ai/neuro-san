
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

import os

from pathlib import Path

from leaf_common.parsers.field_extractor import FieldExtractor

from neuro_san.graph.tools.branch_tool import BranchTool
from neuro_san.graph.tools.class_tool import ClassTool
from neuro_san.graph.tools.external_tool import ExternalTool
from neuro_san.graph.tools.front_man import FrontMan
from neuro_san.graph.tools.method_tool import MethodTool
from neuro_san.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.run_context.interfaces.callable_tool import CallableTool
from neuro_san.run_context.interfaces.run_context import RunContext
from neuro_san.run_context.utils.external_tool_adapter import ExternalToolAdapter
from neuro_san.utils.stream_to_logger import StreamToLogger
from neuro_san.utils.file_of_class import FileOfClass


class AgentToolRegistry(AgentToolFactory):
    """
    A place where agent tools are registered.
    """

    def __init__(self, config: Dict[str, Any], name: str, agent_tool_path: str = None):
        """
        Constructor

        :param agent_specs: A list of agents to pre-register
        :param name: The name of the registry
        :param agent_tool_path: Optional path to specify where source gets resolved.
                    If None, the value comes from the env var AGENT_TOOL_PATH.
                    If that is not set, if defaults to a path relative to this file.
        """
        self.config = config
        self.name = name
        self.agent_spec_map: Dict[str, Dict[str, Any]] = {}

        self.agent_tool_path = self.determine_agent_tool_path(agent_tool_path)

        agent_specs = self.config.get("tools")
        if agent_specs is not None:
            for agent_spec in agent_specs:
                self.register(agent_spec)

    def determine_agent_tool_path(self, agent_tool_path: str) -> str:
        """
        Policy for determining where tool source should be looked for
        when resolving references to coded tools.

        :return: the agent tool path to use for source resolution.
        """
        # Try the env var first if nothing to start with
        if agent_tool_path is None:
            agent_tool_path = os.environ.get("AGENT_TOOL_PATH")

        # Try reach-around directory if still nothing to start with
        if agent_tool_path is None:
            file_of_class = FileOfClass(__file__, "../../coded_tools")
            agent_tool_path = file_of_class.get_basis()

        # If we are dealing with file paths, convert that to something resolvable
        if agent_tool_path.find(os.sep) >= 0:

            # Find the best of many resolution paths in the PYTHONPATH
            best_path = ""
            pythonpath_split = os.environ.get("PYTHONPATH").split(":")
            for one_path in pythonpath_split:
                resolved_path: str = str(Path(one_path).resolve())
                if agent_tool_path.startswith(resolved_path) and \
                        len(resolved_path) > len(best_path):
                    best_path = resolved_path

            # Find the path beneath the python path
            resolve_path = agent_tool_path.split(best_path)[1]

            # Replace separators with python delimiters for later resolution
            agent_tool_path = resolve_path.replace(os.sep, ".")

            # Remove any leading .s
            while agent_tool_path.startswith("."):
                agent_tool_path = agent_tool_path[1:]

        # Be sure the name of the agent (stem of the hocon file) is the
        # last piece to narrow down the path resolution further.
        if not agent_tool_path.endswith(self.name):
            agent_tool_path = f"{agent_tool_path}.{self.name}"

        return agent_tool_path

    def get_config(self) -> Dict[str, Any]:
        """
        :return: The config dictionary passed into the constructor
        """
        return self.config

    def get_agent_tool_path(self) -> str:
        """
        :return: The path under which tools for this registry should be looked for.
        """
        return self.agent_tool_path

    def register(self, agent_spec: Dict[str, Any]):
        """
        :param agent_spec: A single agent to register
        """
        if agent_spec is None:
            return

        extractor = FieldExtractor()
        name = extractor.get_field(agent_spec, "function.name")
        if name is None:
            name = agent_spec.get("name")

        self.agent_spec_map[name] = agent_spec

    def get_agent_tool_spec(self, name: str) -> Dict[str, Any]:
        """
        :param name: The name of the agent tool to get out of the registry
        :return: The dictionary representing the spec registered agent
        """
        if name is None:
            return None

        return self.agent_spec_map.get(name)

    # pylint: disable=too-many-arguments
    def create_agent_tool(self, parent_run_context: RunContext,
                          logger: StreamToLogger,
                          name: str,
                          sly_data: Dict[str, Any],
                          arguments: Dict[str, Any] = None) -> CallableTool:
        """
        :param name: The name of the agent to get out of the registry
        :return: The CallableTool referred to by the name.
        """
        agent_tool: CallableTool = None

        agent_tool_spec: Dict[str, Any] = self.get_agent_tool_spec(name)
        if agent_tool_spec is None:

            if not ExternalToolAdapter.is_external_agent(name):
                raise ValueError(f"No agent_tool_spec for {name}")

            agent_tool = ExternalTool(parent_run_context, logger, name, arguments, sly_data)
            return agent_tool

        if agent_tool_spec.get("function") is not None:
            # If we have a function in the spec, the agent has arguments
            # it wants to be called with.
            if agent_tool_spec.get("class") is not None:
                # Agent specifically requested a python class to be run.
                agent_tool = ClassTool(parent_run_context, logger, self, arguments, agent_tool_spec, sly_data)
            elif agent_tool_spec.get("method") is not None:
                # Agent specifically requested a python method to be run.
                # NOTE: this usage is deprecaded in favor of ClassTools so as to
                # discourage tool implementations with Static Cling.
                agent_tool = MethodTool(parent_run_context, logger, self, arguments, agent_tool_spec, sly_data)
            else:
                agent_tool = BranchTool(parent_run_context, logger, self, arguments, agent_tool_spec, sly_data)
        else:
            # Get the tool to call from the spec.
            agent_tool = FrontMan(parent_run_context, logger, self, agent_tool_spec, sly_data)

        return agent_tool

    def create_front_man(self, logger: StreamToLogger, sly_data: Dict[str, Any]) -> FrontMan:
        """
        Find and create the FrontMan for chat
        """
        front_man_name: str = self.find_front_man()

        agent_tool_spec: Dict[str, Any] = self.get_agent_tool_spec(front_man_name)
        front_man = FrontMan(None, logger, self, agent_tool_spec, sly_data)
        return front_man

    def find_front_man(self) -> str:
        """
        :return: A single tool name to use as the root of the chat agent.
                 This guy will be user facing.  If there are none or > 1,
                 an exception will be raised.
        """
        front_men: List[str] = []

        # The primary way to identify a front-man is that its function has no parameters.
        for name, agent_spec in self.agent_spec_map.items():
            function: Dict[str, Any] = agent_spec.get("function")
            if function.get("parameters") is None:
                front_men.append(name)

        if len(front_men) == 0:
            raise ValueError("No front man for chat found. "
                             "One entry's function must not have any parameters defined to be the front man")

        if len(front_men) > 1:
            raise ValueError(f"Found > 1 front man for chat. Possibilities: {front_men}")

        front_man = front_men[0]
        return front_man
