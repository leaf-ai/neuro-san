
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
from typing import List

from asyncio import Task
from contextvars import Context
from contextvars import ContextVar
from contextvars import copy_context

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_community.callbacks.bedrock_anthropic_callback \
    import BedrockAnthropicTokenUsageCallbackHandler
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback
from langchain_community.callbacks.manager import openai_callback_var
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor

from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.originating_journal import OriginatingJournal
from neuro_san.internals.messages.agent_message import AgentMessage
from neuro_san.internals.messages.origination import Origination


# Keep a ContextVar for the origin info.  We do this because the
# langchain callbacks this stuff is based on also uses ContextVars
# and we want to be sure these are in sync.
# See: https://docs.python.org/3/library/contextvars.html
ORIGIN_INFO: ContextVar[str] = ContextVar('origin_info', default=None)


class LangChainTokenCounter:
    """
    Helps with per-llm means of counting tokens.
    """

    def __init__(self, llm: BaseLanguageModel,
                 invocation_context: InvocationContext,
                 journal: OriginatingJournal = None):
        """
        Constructor

        :param llm: The BaseLanguageModel instance against which token counting is to take place
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param journal: The OriginatingJournal to report token accounting to.
        """
        self.llm: BaseLanguageModel = llm
        self.invocation_context: InvocationContext = invocation_context
        self.journal: OriginatingJournal = journal
        self.debug: bool = False

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
        """
        Counts the tokens (if possible) from what happens inside the awaitable
        within a separate context.  If tokens are counted, they are added to
        the InvocationContext's request_reporting and sent over the message queue
        via the journal

        Recall awaitables are a full async method call with args.  That is, where you would expect to
                baz = await myinstance.foo(bar)
        you instead do
                baz = await token_counter.count_tokens(myinstance.foo(bar)).

        :param awaitable: The awaitable whose tokens we wish to count.
        :return: Whatever the awaitable would return
        """

        retval: Any = None

        # Attempt to count tokens/costs while invoking the agent.
        # The means by which this happens is on a per-LLM basis, so get the right hook
        # given the LLM we've got.
        callback: BaseCallbackHandler = None
        token_counter_context_manager = self.get_callback_for_llm(self.llm)

        if token_counter_context_manager is not None:

            # Record origin information in our own context var so we can associate
            # with the langchain callback context vars more easily.
            origin: List[Dict[str, Any]] = self.journal.get_origin()
            origin_str: str = Origination.get_full_name_from_origin(origin)
            ORIGIN_INFO.set(origin_str)

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
                # Create a new context for different ContextVar values
                # and use the create_task() to run within that context.
                new_context: Context = copy_context()
                task: Task = new_context.run(self.create_task, awaitable)
                retval = await task
        else:
            # No token counting was available for the LLM, but we still need to invoke.
            retval = await awaitable

        await self.report(callback)

        return retval

    def create_task(self, awaitable: Awaitable) -> Task:
        """
        Riffed from:
        https://stackoverflow.com/questions/78659844/async-version-of-context-run-for-context-vars-in-python-asyncio
        """
        executor: AsyncioExecutor = self.invocation_context.get_asyncio_executor()
        origin_str: str = ORIGIN_INFO.get()
        task: Task = executor.create_task(awaitable, origin_str)

        if self.debug:
            # Print to be sure we have a different callback object.
            oai_call = openai_callback_var.get()
            print(f"origin is {origin_str} callback var is {id(oai_call)}")

        return task

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
