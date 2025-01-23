
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

from neuro_san.internals.run_context.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.internals.run_context.langchain.langchain_run_context import LangChainRunContext
from neuro_san.internals.run_context.openai.openai_run_context import OpenAIRunContext


# pylint: disable=too-few-public-methods
class RunContextFactory:
    """
    Creates the correct kind of RunContext
    """

    @staticmethod
    def create_run_context(parent_run_context: RunContext,
                           tool_caller: ToolCaller,
                           config: Dict[str, Any] = None,
                           session_factory: AsyncAgentSessionFactory = None) \
            -> RunContext:
        """
        Creates an appropriate RunContext

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param tool_caller: The ToolCaller whose lifespan matches that
                            of the newly created RunContext
        :param config: The config dictionary which may or may not contain
                       keys for the context_type and default llm_config
        :param session_factory: The AsyncAgentSessionFactory to use when attempting
                        to query external agents. Default is None, implying that
                        the parent's version should be used.
        """

        # Initialize return value
        run_context: RunContext = None

        empty: Dict[str, Any] = {}
        use_config: Dict[str, Any] = config
        if use_config is None:
            use_config = empty

        # Get some fields from the config with reasonable defaults
        default_llm_config: Dict[str, Any] = {
            "model_name": "gpt-4-turbo",
            "verbose": True
        }
        default_llm_config = use_config.get("llm_config", default_llm_config)

        # Prepare for sanity in checks below
        context_type: str = use_config.get("context_type")
        if context_type is None:
            context_type = "langchain"
        context_type = context_type.lower()

        use_session_factory: AsyncAgentSessionFactory = session_factory
        if use_session_factory is None and parent_run_context is not None:
            use_session_factory = parent_run_context.get_session_factory()

        if context_type.startswith("openai"):
            run_context = OpenAIRunContext(default_llm_config, parent_run_context, tool_caller)
        elif context_type.startswith("langchain"):
            run_context = LangChainRunContext(default_llm_config, tool_caller,
                                              use_session_factory)
        else:
            # Default case
            run_context = LangChainRunContext(default_llm_config, tool_caller,
                                              use_session_factory)

        return run_context
