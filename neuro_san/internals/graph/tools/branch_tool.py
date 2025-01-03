
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
import uuid

from leaf_common.parsers.field_extractor import FieldExtractor

from neuro_san.internals.graph.tools.calling_tool import CallingTool
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.message_utils import generate_response
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run import Run
from neuro_san.internals.run_context.interfaces.run_context import RunContext


class BranchTool(CallingTool, CallableTool):
    """
    A CallingTool subclass which can also be a CallableTool.
    Thus, instances are able to be branch nodes in the tool call graph.
    Leaf nodes in the call graph are also these guys, they just happen to
    not call anyone else.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, parent_run_context: RunContext,
                 journal: Journal,
                 factory: AgentToolFactory,
                 arguments: Dict[str, Any],
                 agent_tool_spec: Dict[str, Any],
                 sly_data: Dict[str, Any]):
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
        """
        super().__init__(parent_run_context, journal, factory, agent_tool_spec, sly_data)
        self.arguments: Dict[str, Any] = arguments

    def get_decision_name(self) -> str:
        """
        :return: The string name of the decision the user is trying to make
        """
        decision_name = self.arguments.get("name")
        if decision_name is None:
            decision_name = str(uuid.uuid4())
        return decision_name

    def get_specific_instructions(self) -> str:
        """
        :return: The string prompt for framing the problem in terms of expertise,
                 context, actions and outcomes.
        """
        # Get the properties of the function
        extractor: FieldExtractor = FieldExtractor()
        empty: Dict[str, Any] = {}

        agent_spec = self.get_agent_tool_spec()

        # Properties describe the function arguments
        properties: Dict[str, Any] = extractor.get_field(agent_spec, "function.parameters.properties", empty)

        # Attributions describe how we tell the tool what the values of its function arguments are
        attributions: Dict[str, str] = extractor.get_field(agent_spec, "attributions", empty)

        # Start to build the specific instructions, with one sentence for each property
        # listed (exception for name and description).
        specific_instructions: str = ""
        for one_property, attributes in properties.items():

            if one_property in ("name", "description"):
                # Skip, as this does not need to be in the specific intructions
                continue

            args_value: Any = self.arguments.get(one_property)
            if args_value is None:
                # If we do not have an argument value for the property,
                # do not add anything to the specific instructions
                continue

            args_value_str: str = self._get_args_value_as_string(args_value,
                                                                 attributes.get("type"))

            # Determine which attribution to use.
            # First we look in the agent spec to see if there is something
            # specific to use given the property/arg name.
            attribution: str = attributions.get(one_property)
            if attribution is None:

                # No specific attribution text, so we make up a boilerplate
                # one where it give the property/arg name <is/are> and the value.

                # Figure out the attribution verb for singular vs plural
                assignment_verb: str = "is"
                if attributes.get("type") == "array":
                    assignment_verb = "are"

                attribution = f"The {one_property} {assignment_verb}"

            # Put together the assignment statement
            assignment: str = f"{attribution} {args_value_str}.\n"

            # Add the assignment statement to the overall specific instructions.
            specific_instructions = specific_instructions + assignment

        return specific_instructions

    @staticmethod
    def _get_args_value_as_string(args_value: Any, value_type: str = None) -> str:
        """
        Get the string value of the value provided in the arguments
        """
        args_value_str: str = None

        if value_type == "dict" or isinstance(args_value, Dict):
            args_value_str = json.dumps(args_value)
            # Strip the begin/end braces as gpt-4o doesn't like them.
            # This means that anything within the json-y braces for a dictionary
            # value gets interpreted as "this is an input value that has
            # to come from the code" when that is not the case at all.
            # Unclear why this is an issue with gpt-4o and not gpt-4-turbo.
            args_value_str = args_value_str[1:-1]
        elif value_type == "array" or isinstance(args_value, List):
            str_values = []
            for item in args_value:
                item_str: str = BranchTool._get_args_value_as_string(item)
                str_values.append(item_str)
            args_value_str = ", ".join(str_values)
        elif value_type == "string":
            args_value_str = f'"{args_value}"'
            # Per https://github.com/langchain-ai/langchain/issues/1660
            # We need to use double curly braces in order to pass values
            # that actually have curly braces in them so they will not
            # be mistaken for string placeholders for input.
            args_value_str = args_value_str.replace("{", "{{")
            args_value_str = args_value_str.replace("}", "}}")
        else:
            args_value_str = str(args_value)

        return args_value_str

    def get_takes_awhile(self) -> bool:
        """
        :return: True if the component's function takes a decent bit of time.
                Default is False.
        """
        takes_awhile = self.get_callable_tool_names(self.agent_tool_spec) is not None
        return takes_awhile

    def get_command(self) -> str:
        """
        :return: A string describing the objective of the component.
        """
        agent_spec = self.get_agent_tool_spec()
        return agent_spec.get("command")

    async def integrate_callable_response(self, run: Run, messages: List[Any]) -> List[Any]:
        """
        :param run: The Run for the prescriptor (if any)
        :param messages: A current list of messages for the component.
        :return: An updated list of messages after this operation is done.
                This default implementation is just a pass-through of the messages argument.
        """
        new_messages: List[Any] = messages

        callable_tool_name = self.get_callable_tool_names(self.agent_tool_spec)
        if callable_tool_name is None:
            # If there is no callable_tool_name, then there is no action from the
            # callable class to integrate
            return new_messages

        while run.requires_action():
            # The tool we just called requires more information
            new_run = await self.make_tool_function_calls(run)
            new_run = await self.run_context.wait_on_run(new_run, self.journal)
            new_messages = await self.run_context.get_response()

        return new_messages

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.
        :return: A List of messages produced during this process.
        """

        specific_instructions = self.get_specific_instructions()
        instructions = self.get_instructions()
        instructions = instructions + specific_instructions

        decision_name = self.get_decision_name()
        component_name = self.get_component_name()
        assistant_name = f"{decision_name}_{component_name}"
        await self.journal.write(f"setting up {component_name} assistant...")

        await self.create_resources(assistant_name, instructions)

        upper_component = component_name.upper()
        await self.journal.write(f"{upper_component} CALLED>>> {specific_instructions}")
        if self.get_takes_awhile():
            await self.journal.write("This may take awhile...")

        command = self.get_command()
        run: Run = await self.run_context.submit_message(command)
        run = await self.run_context.wait_on_run(run, self.journal)

        messages = await self.run_context.get_response()

        messages = await self.integrate_callable_response(run, messages)

        response = generate_response(messages)
        await self.journal.write(f"{upper_component} RETURNED>>> {response}")
        return response
