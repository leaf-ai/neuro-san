
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

from neuro_san.internals.graph.tools.abstract_class_tool import AbstractClassTool
from neuro_san.internals.interfaces.context_type_toolbox_factory import ContextTypeToolboxFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext


class ToolboxTool(AbstractClassTool):
    """
    A ClassTool that resolves the full class reference from a predefined coded tool in the toolbox.

    Note that this class does not apply to Langchain's base tools.
    """

    def get_full_class_ref(self) -> str:
        """
        Returns the full class reference path from a predefined toolbox.

        This implementation looks up the tool by name in a toolbox, using the
        "toolbox" field in `agent_tool_spec`, then determine the class of that
        coded tool.

        :return: A dot-separated string representing the full class path.
        """
        tool_name: str = self.agent_tool_spec.get("toolbox")
        invocation_context: InvocationContext = self.run_context.get_invocation_context()
        toolbox_factory: ContextTypeToolboxFactory = invocation_context.get_toolbox_factory()
        return toolbox_factory.get_shared_coded_tool_class(tool_name)
