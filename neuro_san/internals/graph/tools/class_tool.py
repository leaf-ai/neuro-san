
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

import json

from leaf_common.config.resolver import Resolver

from neuro_san.interfaces.coded_tool import CodedTool
from neuro_san.internals.graph.tools.branch_tool import BranchTool
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run_context import RunContext


class ClassTool(CallableTool):
    """
    CallableTool which can invoke a CodedTool by its class name.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, parent_run_context: RunContext,
                 journal: Journal,
                 factory: AgentToolFactory,
                 arguments: Dict[str, Any],
                 agent_tool_spec: Dict[str, Any],
                 sly_data: Dict[str, Any],
                 config: Dict[str, Any] = None):
        """
        Constructor

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param journal: The Journal that captures messages for user output
        :param factory: The AgentToolFactory used to create tools
        :param arguments: A dictionary of the tool function arguments passed in
        :param agent_tool_spec: The dictionary describing the JSON agent tool
                            to be used by the instance
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
                 This gets passed along as a distinct argument to the referenced python class's
                 invoke() method.
        :param config: An optional config dictionary to pass to the CodedTool
        """
        self.parent_run_context: RunContext = parent_run_context
        self.journal: Journal = journal
        self.factory: AgentToolFactory = factory
        self.arguments: Dict[str, Any] = arguments
        self.agent_tool_spec: Dict[str, Any] = agent_tool_spec
        self.sly_data: Dict[str, Any] = sly_data
        self.config: Dict[str, str] = {}
        if config is not None:
            self.config = config

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.

        :return: A List of messages produced during this process.
        """
        messages: List[Any] = []

        # Get the python module with the class name containing a CodedTool reference.
        # Will need some exception safety in here eventually.
        full_class_ref = self.agent_tool_spec.get("class")
        print(f"Calling class {full_class_ref}")

        class_split = full_class_ref.split(".")
        class_name = class_split[-1]
        # Remove the class name from the end to get the module name
        module_name = full_class_ref[:-len(class_name)]
        # Remove any trailing .s
        while module_name.endswith("."):
            module_name = module_name[:-1]

        # Resolve the class and the method
        packages: List[str] = [self.factory.get_agent_tool_path()]
        resolver: Resolver = Resolver(packages)

        python_class = resolver.resolve_class_in_module(class_name, module_name)

        # Instantiate the CodedTool
        coded_tool: CodedTool = None
        if issubclass(python_class, BranchTool):
            coded_tool = python_class(self.parent_run_context, self.journal, self.factory,
                                      self.arguments, self.agent_tool_spec, self.sly_data)
        else:
            # Go with the no-args constructor as per the run-of-the-mill contract
            coded_tool = python_class()

        if isinstance(coded_tool, CodedTool):
            retval: Any = await coded_tool.async_invoke(self.arguments, self.sly_data, self.config)
        else:
            retval = f"Error: {full_class_ref} is not a CodedTool"

        # Change the result into a message
        retval_str: str = f"{retval}"
        message: Dict[str, Any] = {
            "role": "assistant",
            "content": retval_str
        }
        messages.append(message)
        messages_str: str = json.dumps(messages)

        return messages_str

    async def delete_resources(self, parent_run_context: RunContext):
        """
        Cleans up after any allocated resources on their server side.
        :param parent_run_context: The RunContext which contains the scope
                    of operation of this CallableNode
        """
        # Nothing to delete
        return
