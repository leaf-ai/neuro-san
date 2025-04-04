
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


class ContextTypeBaseToolFactory:
    """
    Interface for Factory classes creating tool

    Most methods take a config dictionary which consists of the following keys:

        "tool_name"                 The name of the tool.
                                    Raise ValueError if not specified.

        "args"                      A dict containing values of contructor arguments
                                    For a tool or toolkit instantiate via a constructor

        "method"                    A dict containing values of a class method arguements
                                    For a toolkit instantiate via a class method
    """

    def load(self):
        """
        Goes through the process of loading any user extensions and/or configuration
        files
        """
        raise NotImplementedError

    def create_agent_tool(self, tool_name: str, user_args: Dict[str, Any]) -> Any:
        """
        Create a tool instance from the fully-specified tool config.
        :param tool_name: The name of the tool to instantiate.
        :param user_args: Arguments provided by the user, which override the args in config file.
        :return: A tool instance native to the context type.
                Can raise a ValueError if the config's class or tool_name value is
                unknown to this method.
        """
        raise NotImplementedError
