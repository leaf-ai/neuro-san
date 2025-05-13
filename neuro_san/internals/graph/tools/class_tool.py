
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


class ClassTool(AbstractClassTool):
    """
    A ClassTool that retrieves the full class reference directly from the tool specification
    in agent network hocon.
    """

    def get_full_class_ref(self) -> str:
        """
        Returns the full class reference path directly from the tool specification.

        This implementation expects the fully qualified class name to be provided
        in the "class" field of the `agent_tool_spec` dictionary.

        :return: A dot-separated string representing the full class path.
        """
        return self.agent_tool_spec.get("class")
