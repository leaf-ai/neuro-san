from typing import Any
from typing import Dict
from typing import List

import copy
import json

from leaf_common.config.resolver import Resolver

from neuro_san.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.run_context.interfaces.callable_tool import CallableTool
from neuro_san.run_context.interfaces.run_context import RunContext
from neuro_san.utils.stream_to_logger import StreamToLogger


class MethodTool(CallableTool):
    """
    Interface describing what a CallingTool can access
    when invoking LLM function calls.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, parent_run_context: RunContext,
                 logger: StreamToLogger,
                 factory: AgentToolFactory,
                 arguments: Dict[str, Any],
                 agent_tool_spec: Dict[str, Any],
                 sly_data: Dict[str, Any]):
        """
        Constructor

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param logger: The StreamToLogger that captures messages for user output
        :param factory: The AgentToolFactory used to create tools
        :param arguments: A dictionary of the tool function arguments passed in
        :param agent_tool_spec: The dictionary describing the JSON agent tool
                            to be used by the instance
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
                 This gets passed along as a distinct argument to the referenced python method.
        """
        _ = parent_run_context, logger, factory
        self.agent_tool_spec: Dict[str, Any] = agent_tool_spec
        self.factory: AgentToolFactory = factory
        self.arguments: Dict[str, Any] = arguments

        # Only add sly_data if there is something to add
        if sly_data is not None and len(sly_data.keys()) > 0:

            # Make a copy of the arguments to maintain the external expectation
            # that what is passed in stays unmodified.
            # Note we only do this when we need to.
            self.arguments = copy.copy(arguments)
            self.arguments["sly_data"] = sly_data

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.

        :return: A List of messages produced during this process.
        """
        messages: List[Any] = []

        # Get the python module with the method name.
        # Will need some execption safety in here eventually.
        full_method_ref = self.agent_tool_spec.get("method")
        print(f"Calling method {full_method_ref}")

        # Worth noting that this assumes a static method inside a class for now

        # Break the method down into parts
        method_split = full_method_ref.split(".")
        method_name = method_split[-1]
        class_name = method_split[-2]
        # Remove the method name from the end to get the module name
        module_name = full_method_ref[:-len(f"{class_name}.{method_name}")]
        # Remove any trailing .s
        while module_name.endswith("."):
            module_name = module_name[:-1]

        # Resolve the class and the method
        packages: List[str] = [self.factory.get_agent_tool_path()]
        resolver: Resolver = Resolver(packages)
        python_class = resolver.resolve_class_in_module(class_name, module_name)
        python_method = getattr(python_class, method_name)

        # Call the method
        retval: Any = python_method(self.arguments)

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
