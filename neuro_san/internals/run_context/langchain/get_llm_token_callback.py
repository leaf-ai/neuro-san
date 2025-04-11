
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

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional

from langchain_core.tracers.context import register_configure_hook

from neuro_san.internals.run_context.langchain.llm_token_callback_handler import LlmTokenCallbackHandler


llm_token_callback_var: ContextVar[Optional[LlmTokenCallbackHandler]] = (
        ContextVar("llm_token_callback", default=None)
    )
register_configure_hook(llm_token_callback_var, inheritable=True)


@contextmanager
def get_llm_token_callback() -> Generator[LlmTokenCallbackHandler, None, None]:
    """Get llm token callback.

    Get context manager for tracking usage metadata across chat model calls using
    "AIMessage.usage_metadata".

    This class is a modification of LangChain’s "UsageMetadataCallbackHandler":
    - https://python.langchain.com/api_reference/_modules/langchain_core/callbacks/usage.html
    #get_usage_metadata_callback
    """
    cb = LlmTokenCallbackHandler()
    llm_token_callback_var.set(cb)
    yield cb
    llm_token_callback_var.set(None)
