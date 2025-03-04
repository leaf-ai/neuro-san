
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
from typing import Awaitable
from typing import Dict

from contextvars import ContextVar
from contextvars import copy_context

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_community.callbacks.bedrock_anthropic_callback \
    import BedrockAnthropicTokenUsageCallbackHandler
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.agent_message import AgentMessage


ORIGIN_INFO: ContextVar = ContextVar('origin_info', default=None)


class LangChainTokenCounter:
    """
    Helps with per-llm means of counting tokens.
    """

    def __init__(self, llm: BaseLanguageModel,
                 invocation_context: InvocationContext,
                 journal: Journal = None):
        """
        Constructor

        :param llm: The BaseLanguageModel instance against which token counting is to take place
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param journal: The journal to report token accounting to.
        """
        self.llm: BaseLanguageModel = llm
        self.invocation_context: InvocationContext = invocation_context
        self.journal: Journal = journal

    @staticmethod
    def get_callback_for_llm(llm: BaseLanguageModel) -> Any:
        """
        :param llm: A BaseLanguageModel returned from LlmFactory.
        :return: A handle to a no-args function, that when called will
                open up a context manager for token counting.
                Can be None if no such entity exists for the llm type
        """

        if isinstance(llm, (AzureChatOpenAI, ChatOpenAI)):
            return get_openai_callback

        if isinstance(llm, ChatAnthropic):
            return get_bedrock_anthropic_callback

        return None

    async def count_tokens(self, awaitable: Awaitable) -> Any:

        retval: Any = None

        # Attempt to count tokens/costs while invoking the agent.
        # The means by which this happens is on a per-LLM basis, so get the right hook
        # given the LLM we've got.
        callback: BaseCallbackHandler = None
        token_counter_context_manager = self.get_callback_for_llm(self.llm)

        if token_counter_context_manager is not None:
            # Use the context manager to count tokens as per
            #   https://python.langchain.com/docs/how_to/llm_token_usage_tracking/#using-callbacks
            #
            # Caveats:
            # * In using this context manager approach, any tool that is called
            #   also has its token counts contributing to its callers for better or worse.
            # * As of 2/21/25, it seems that tool-calling agents (branch nodes) are not
            #   registering their tokens correctly. Not sure if this is a bug in langchain
            #   or there is something we are not doing in that scenario that we should be.
            with token_counter_context_manager() as callback:
                retval = await awaitable
        else:
            # No token counting was available for the LLM, but we still need to invoke.
            retval = await awaitable

        await self.report(callback)

        return retval

    async def report(self, callback: BaseCallbackHandler):
        """
        Report on the token accounting results of the callback
        :param callback: A BaseCallbackHandler instance that contains token counting information
        """
        # Token counting results are collected in the callback, if there are any.
        # Different LLMs can count things in different ways, so normalize.
        token_dict: Dict[str, Any] = self.normalize_token_count(callback)
        if token_dict is None or not bool(token_dict):
            return

        # Accumulate what we learned about tokens to request reporting.
        # For now we just overwrite the one key because we know
        # the last one out will be the front man, and as of 2/21/25 his stats
        # are cumulative.  At some point we might want a finer-grained breakdown
        # that perhaps contributes to a service/er-wide periodic token stats breakdown
        # of some kind.  For now, get something going.
        request_reporting: Dict[str, Any] = self.invocation_context.get_request_reporting()
        request_reporting["token_accounting"] = token_dict

        if self.journal is not None:
            # We actually have a token dictionary to report, so go there.
            agent_message = AgentMessage(structure=token_dict)
            await self.journal.write_message(agent_message)

    @staticmethod
    def normalize_token_count(callback: BaseCallbackHandler) -> Dict[str, Any]:
        """
        Normalizes the values in the token counting callback into a standard dictionary

        :param callback: A BaseCallbackHandler instance that contains token counting information
        """

        token_dict: Dict[str, Any] = {}
        if callback is None:
            return token_dict

        if isinstance(callback, (OpenAICallbackHandler, BedrockAnthropicTokenUsageCallbackHandler)):
            # So far these two instances share the same reporting structure
            token_dict = {
                "total_tokens": callback.total_tokens,
                "prompt_tokens": callback.prompt_tokens,
                "completion_tokens": callback.completion_tokens,
                "successful_requests": callback.successful_requests,
                "total_cost": callback.total_cost,
                "caveats": [
                    "Langchain only allows accounting for OpenAI and Anthropic models.",
                    "Each LLM Branch Node also includes accounting for each of its callees.",
                    "Each LLM Branch Node does not yet properly account for its own tokens.",
                ]
            }

        return token_dict
