
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

import os

from pathlib import Path

from leaf_common.config.dictionary_overlay import DictionaryOverlay
from leaf_common.parsers.field_extractor import FieldExtractor

from neuro_san.internals.graph.registry.sly_data_redactor import SlyDataRedactor
from neuro_san.internals.graph.tools.branch_tool import BranchTool
from neuro_san.internals.graph.tools.class_tool import ClassTool
from neuro_san.internals.graph.tools.external_tool import ExternalTool
from neuro_san.internals.graph.tools.front_man import FrontMan
from neuro_san.internals.graph.tools.method_tool import MethodTool
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.utils.external_tool_adapter import ExternalToolAdapter
from neuro_san.internals.utils.file_of_class import FileOfClass


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
        self.first_agent: str = None

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
            file_of_class = FileOfClass(__file__, "../../../coded_tools")
            agent_tool_path = file_of_class.get_basis()

        # If we are dealing with file paths, convert that to something resolvable
        if agent_tool_path.find(os.sep) >= 0:

            # Find the best of many resolution paths in the PYTHONPATH
            resolved_tool_path: str = str(Path(agent_tool_path).resolve())
            best_path = ""
            pythonpath_split = os.environ.get("PYTHONPATH").split(":")
            for one_path in pythonpath_split:
                resolved_path: str = str(Path(one_path).resolve())
                if resolved_tool_path.startswith(resolved_path) and \
                        len(resolved_path) > len(best_path):
                    best_path = resolved_path

            if len(best_path) == 0:
                raise ValueError(f"No reasonable agent tool path found in PYTHONPATH for {agent_tool_path}")

            # Find the path beneath the python path
            path_split = resolved_tool_path.split(best_path)
            resolve_path = path_split[1]

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

        name: str = self.get_name_from_spec(agent_spec)
        if self.first_agent is None:
            self.first_agent = name

        self.agent_spec_map[name] = agent_spec

    def get_name_from_spec(self, agent_spec: Dict[str, Any]) -> str:
        """
        :param agent_spec: A single agent to register
        :return: The agent name as per the spec
        """
        extractor = FieldExtractor()
        name = extractor.get_field(agent_spec, "function.name")
        if name is None:
            name = agent_spec.get("name")

        return name

    def get_agent_tool_spec(self, name: str) -> Dict[str, Any]:
        """
        :param name: The name of the agent tool to get out of the registry
        :return: The dictionary representing the spec registered agent
        """
        if name is None:
            return None

        return self.agent_spec_map.get(name)

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def create_agent_tool(self, parent_run_context: RunContext,
                          journal: Journal,
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

            # For external tools, we want to redact the sly data based on
            # the calling/parent's agent specs.
            redacted_sly_data: Dict[str, Any] = self.redact_sly_data(parent_run_context, sly_data)

            agent_tool = ExternalTool(parent_run_context, journal, name, arguments, redacted_sly_data)
            return agent_tool

        # Merge the arguments coming in from the LLM with those that were specified
        # in the hocon file for the agent.
        use_args: Dict[str, Any] = self.merge_args(arguments, agent_tool_spec)

        if agent_tool_spec.get("function") is not None:
            # If we have a function in the spec, the agent has arguments
            # it wants to be called with.
            if agent_tool_spec.get("class") is not None:
                # Agent specifically requested a python class to be run.
                agent_tool = ClassTool(parent_run_context, journal, self, use_args, agent_tool_spec, sly_data)
            elif agent_tool_spec.get("method") is not None:
                # Agent specifically requested a python method to be run.
                # NOTE: this usage is deprecaded in favor of ClassTools so as to
                # discourage tool implementations with Static Cling.
                agent_tool = MethodTool(parent_run_context, journal, self, use_args, agent_tool_spec, sly_data)
            else:
                agent_tool = BranchTool(parent_run_context, journal, self, use_args, agent_tool_spec, sly_data)
        else:
            # Get the tool to call from the spec.
            agent_tool = FrontMan(parent_run_context, journal, self, agent_tool_spec, sly_data)

        return agent_tool

    def create_front_man(self, journal: Journal, sly_data: Dict[str, Any]) -> FrontMan:
        """
        Find and create the FrontMan for chat
        """
        front_man_name: str = self.find_front_man()

        agent_tool_spec: Dict[str, Any] = self.get_agent_tool_spec(front_man_name)
        front_man = FrontMan(None, journal, self, agent_tool_spec, sly_data)
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
            # The next way to find a front man is to see which agent was registered first
            front_men.append(self.first_agent)

        if len(front_men) == 0:
            raise ValueError("No front man for chat found. "
                             "One entry's function must not have any parameters defined to be the front man")

        if len(front_men) > 1:
            raise ValueError(f"Found > 1 front man for chat. Possibilities: {front_men}")

        front_man = front_men[0]
        return front_man

    def merge_args(self, llm_args: Dict[str, Any], agent_tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges the args specified by the llm with "hard-coded" args specified in the agent spec.
        Hard-coded args win over llm-specified args if both are defined.
        If you want the llm args to win out over the hard-coded args, use a default for
        the function spec instead of the hard-coded args.

        :param llm_args: argument dictionary that the LLM wants
        :param agent_tool_spec: The dictionary representing the spec registered agent
        """
        config_args: Dict[str, Any] = agent_tool_spec.get("args")
        if config_args is None:
            # Nothing to override
            return llm_args

        overlay = DictionaryOverlay()
        merged_args: Dict[str, Any] = overlay.overlay(llm_args, config_args)
        return merged_args

    def redact_sly_data(self, parent_run_context: RunContext, sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact the sly_data based on the agent spec associated with the parent run context

        :param parent_run_context: The parent run context of the tool to be created.
        :param sly_data: The internal representation of the sly_data to be redacted
        :return: A new sly_data dictionary, redacted as per the parent spec
        """
        parent_spec: Dict[str, Any] = None
        if parent_run_context is not None:
            parent_spec = parent_run_context.get_agent_tool_spec()

        redactor = SlyDataRedactor(parent_spec)
        redacted: Dict[str, Any] = redactor.filter_config(sly_data)
        return redacted
