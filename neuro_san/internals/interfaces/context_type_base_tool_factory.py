
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
    Interface for factory classes that create tools or toolkits.

    Most methods accept a configuration dictionary, where each key is a tool name, and each value is
    a dictionary containing the corresponding tool's setup information. The configuration dictionary
    supports the following keys for each tool:

        - "class":   The class of the tool or toolkit.
                    This key is required. A ValueError will be raised if not provided.

        - "args":    A dictionary of constructor arguments used to instantiate the tool or toolkit
                    directly via its constructor.

        - "method":  A dictionary of arguments used when instantiating the toolkit via a class method.
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
