
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
from neuro_san.internals.errors.json_error_formatter import JsonErrorFormatter
from neuro_san.internals.errors.string_error_formatter import StringErrorFormatter
from neuro_san.internals.interfaces.error_formatter import ErrorFormatter


class ErrorFormatterFactory:
    """
    Factory class to create an appropriate ErrorFormatter
    """

    @staticmethod
    def create_formatter(name: str = "string") -> ErrorFormatter:
        """
        Creates an ErrorFormatter given the name.

        :param name: The name of the error formatter to use
        :return: An ErrorFormatter instance.
        """

        # Default
        formatter: ErrorFormatter = StringErrorFormatter()
        if name is None:
            return formatter

        if name.lower() == "json":
            formatter = JsonErrorFormatter()

        # When the need arises, we could conceivably add class name lookup
        # for error formatters here, not unlike the way we do for coded tools.

        return formatter
