
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

from leaf_common.config.dictionary_overlay import DictionaryOverlay

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.run_context.factory.run_context_factory import RunContextFactory
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run import Run
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.interfaces.tool_call import ToolCall
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.internals.run_context.utils.external_agent_parsing import ExternalAgentParsing


class CallingTool(ToolCaller):
    """
    An implementation of the ToolCaller interface which actually does
    the calling of the other tools.

    Worth noting that this is used as a base implementation for:
        * BranchTool - which can both call other tools and be called as a tool
        * FrontMan - which can only call other tools but has other specialized
            logic for interacting with user input, it being the root node of a tool graph.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, parent_run_context: RunContext,
                 journal: Journal,
                 factory: AgentToolFactory,
                 agent_tool_spec: Dict[str, Any],
                 sly_data: Dict[str, Any]):
        """
        Constructor

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param journal: The Journal that captures messages for user output
        :param factory: The factory for Agent Tools.
        :param agent_tool_spec: The dictionary describing the JSON agent tool
                            to be used by the instance
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
        """
        self.journal: Journal = journal
        self.factory: AgentToolFactory = factory
        self.agent_tool_spec: Dict[str, Any] = agent_tool_spec
        self.sly_data: Dict[str, Any] = sly_data

        empty: Dict[str, Any] = {}
        overlayer = DictionaryOverlay()

        # Get the llm config as a combination of defaults from different places in the config
        config: Dict[str, Any] = self.factory.get_config()
        llm_config = config.get("llm_config", empty)
        llm_config = overlayer.overlay(llm_config, self.agent_tool_spec.get("llm_config", empty))
        if len(llm_config.keys()) == 0:
            llm_config = None

        run_context_config: Dict[str, Any] = {
            "context_type": config.get("context_type"),
            "llm_config": llm_config
        }
        self.run_context: RunContext = RunContextFactory.create_run_context(parent_run_context,
                                                                            self,
                                                                            config=run_context_config)

    def get_agent_tool_spec(self) -> Dict[str, Any]:
        """
        :return: the dictionary describing the data-driven agent
        """
        return self.agent_tool_spec

    def get_component_name(self) -> str:
        """
        :return: The string name of the component
        """
        return self.agent_tool_spec.get("name")

    def get_instructions(self) -> str:
        """
        :return: The string prompt for framing the problem in terms of purpose.
        """
        instructions: str = self.agent_tool_spec.get("instructions")
        if instructions is None:
            agent_name: str = self.get_component_name()
            message: str = f"""
The agent named "{agent_name}" has no instructions specified for it.

Every agent must have instructions providing the natural-language
context with which it will proces input, essentially telling it what to do.
"""
            raise ValueError(message)
        return instructions

    def get_factory(self) -> AgentToolFactory:
        """
        :return: The factory containing all the tool specs
        """
        return self.factory

    def get_origin(self) -> List[Dict[str, Any]]:
        """
        :return: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with. Starts at 0.
        """
        return self.run_context.get_origin()

    async def create_resources(self, component_name: str = None,
                               specific_instructions: str = None):
        """
        Creates resources that will be used throughout the lifetime of the component.
        :param component_name: Optional string for labelling the component.
                        Defaults to the agent name if not set.
        :param specific_instructions: Optional string for setting
                        more fine-grained instructions. Defaults to agent instructions.
        """
        name = component_name
        if name is None:
            name = self.get_component_name()

        instructions = specific_instructions
        if instructions is None:
            instructions = self.get_instructions()

        tool_names: List[str] = self.get_callable_tool_names(self.agent_tool_spec)
        await self.run_context.create_resources(name, instructions, tool_names=tool_names)

    @staticmethod
    def get_callable_tool_names(agent_tool_spec: Dict[str, Any]) -> List[str]:
        """
        :return: The names of the callable tools this instance will call
                 Can return None if the instance will not call any tools.
        """
        tool_list: List[str] = agent_tool_spec.get("tools")
        if tool_list is None or len(tool_list) == 0:
            # We really don't have any callable tools
            return None

        return tool_list

    def get_callable_tool_dict(self) -> Dict[str, str]:
        """
        :return: A dictionary of name -> name, where the keys are what the tool has been
                called in the framework (e.g. langchain) and the value is what the tool
                has been called in the agent_spec itself.  This is often a reflexive
                mapping, except in the case of external tools where a safer name is
                needed for internal framework reference.
        """
        tool_dict: Dict[str, str] = {}

        tool_list: List[str] = self.get_callable_tool_names(self.agent_tool_spec)
        if tool_list is None:
            return tool_dict

        for tool in tool_list:
            safe_name: str = ExternalAgentParsing.get_safe_agent_name(tool)
            tool_dict[safe_name] = tool

        return tool_dict

    async def make_tool_function_calls(self, component_run: Run) -> Run:
        """
        Calls all of the callable_components' functions

        :param component_run: The Run which the component is operating under
        :return: A potentially updated Run for the component
        """
        # DEF: Still a mystery as to how to get langchain implementation
        #      to tell us the tool calls it *needs* to make vs the tool calls
        #      it *could* make.
        component_tool_calls: List[ToolCall] = component_run.get_tool_calls()
        tool_outputs: List[Dict[str, Any]] = []  # Initialize an empty list to store tool outputs

        # Call each of the the listed tools and collect the results
        # of their function(s).
        for component_tool_call in component_tool_calls:

            tool_output: Dict[str, Any] = await self.make_one_tool_function_call(component_tool_call)

            # Add the tool output for the current component_tool_call to the list
            tool_outputs.append(tool_output)

        # Submit all tool outputs at once after the loop has gathered all
        # outputs of all CallableTool' functions.
        component_run = await self.run_context.submit_tool_outputs(component_run, tool_outputs)

        return component_run

    async def make_one_tool_function_call(self, component_tool_call: ToolCall) -> Dict[str, Any]:
        """
        Calls a single callable_component's function

        :param component_tool_call: A ToolCall instance to get the function
                            arguments from
        :return: A dictionary with keys:
                "tool_call_id" a string id representing the call to the tool itself
                "output" a JSON string representing the output of the tool's function
        """
        # Get the function args as a dictionary
        tool_name: str = component_tool_call.get_function_name()
        print(f"Calling {tool_name}")

        tool_arguments: Dict[str, Any] = component_tool_call.get_function_arguments()

        # Create a new instance of a JSON-speced tool using the supplied callable_tool_name.
        # At this point tool_name might be an internal reference to an external tool,
        # so we need to check a mapping.
        callable_tool_dict: Dict[str, str] = self.get_callable_tool_dict()
        use_tool_name: str = callable_tool_dict.get(tool_name)
        if use_tool_name is None:
            raise ValueError(f"{tool_name} is not in tools {list(callable_tool_dict.keys())}")

        # Note: This is not a BaseTool. This is our own construct within graph
        #       that we can build().
        callable_component: CallableTool = \
            self.factory.create_agent_tool(self.run_context, self.journal,
                                           use_tool_name, self.sly_data, tool_arguments)
        callable_component_response: List[Any] = await callable_component.build()

        output: str = json.dumps(callable_component_response)

        # Prepare the tool output
        tool_output: Dict[str, Any] = {
            "tool_call_id": component_tool_call.get_id(),
            "output": output
        }

        # Clean up after this CallableTool.
        # Note that the run_context passed here is used as a comparison to be sure
        # that the CallableTool's cleanup does not accidentally clean up
        # any resources that should still remain open for this
        # CallingTool's purposes.
        await callable_component.delete_resources(self.run_context)

        return tool_output

    async def delete_resources(self, parent_run_context: RunContext):
        """
        Cleans up after any allocated resources on their server side.
        :param parent_run_context: The RunContext which contains the scope
                    of operation of this CallableTool
        """
        if self.run_context is not None:
            await self.run_context.delete_resources(parent_run_context)
            self.run_context = None
