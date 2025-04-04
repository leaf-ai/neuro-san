
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

from neuro_san.internals.interfaces.context_type_base_tool_factory import ContextTypeBaseToolFactory
from neuro_san.internals.run_context.langchain.base_tool_factory import BaseToolFactory


class MasterBaseToolFactory:
    """
    Creates the correct kind of ContextTypeBaseToolFactory
    """

    @staticmethod
    def create_base_tool_factory(config: Dict[str, Any] = None) -> ContextTypeBaseToolFactory:
        """
        Creates an appropriate ContextTypeBaseToolFactory

        :param config: The config dictionary which may or may not contain
                       keys for the context_type and default base_tool_config
        :return: A ContextTypeBaseToolFactory appropriate for the context_type in the config.
        """

        base_tool_factory: ContextTypeBaseToolFactory = None
        context_type: str = MasterBaseToolFactory.get_context_type(config)

        if context_type.startswith("openai"):
            base_tool_factory = None
        elif context_type.startswith("langchain"):
            base_tool_factory = BaseToolFactory()
        else:
            # Default case
            base_tool_factory = BaseToolFactory()

        return base_tool_factory

    @staticmethod
    def get_context_type(config: Dict[str, Any]) -> str:
        """
        :param config: The config dictionary which may or may not contain
                       keys for the context_type and default base_tool_config
        :return: The context type for the config
        """
        empty: Dict[str, Any] = {}
        use_config: Dict[str, Any] = config
        if use_config is None:
            use_config = empty

        # Prepare for sanity in checks below
        context_type: str = use_config.get("context_type")
        if context_type is None:
            context_type = "langchain"
        context_type = context_type.lower()

        return context_type
