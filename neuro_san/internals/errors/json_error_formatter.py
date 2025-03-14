
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
from typing import Dict

import json

from neuro_san.internals.interfaces.error_formatter import ErrorFormatter


class JsonErrorFormatter(ErrorFormatter):
    """
    Implementation of ErrorFormatter interface which compiles error information
    into a JSON dictionary.   See parent interface for more details.
    """

    def format(self, agent_name: str, message: str, details: str = None) -> str:
        """
        Format an error message

        :param agent_name: A string describing the name of the agent experiencing
                the error.
        :param message: The specific message describing the error occurrence.
        :param details: An optional string describing further details of how/where the
                error occurred.  Think: traceback.
        :return: String encapsulation and/or filter of the error information
                presented in the arguments.
        """
        error_dict: Dict[str, str] = {
            "error": message,
            "tool": agent_name
        }
        if details is not None:
            error_dict["details"] = f"{details}"

        pretty: str = json.dumps(error_dict, sort_keys=True, indent=4)
        return f"```json\n{pretty}\n```"
