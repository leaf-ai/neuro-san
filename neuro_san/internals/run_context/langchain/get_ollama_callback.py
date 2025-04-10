
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

from neuro_san.internals.run_context.langchain.ollama_callback_handler import OllamaCallbackHandler


ollama_callback_var: ContextVar[Optional[OllamaCallbackHandler]] = (
        ContextVar("ollama_callback", default=None)
    )
register_configure_hook(ollama_callback_var, inheritable=True)


@contextmanager
def get_ollama_callback() -> Generator[OllamaCallbackHandler, None, None]:
    """Get ollama callback.

    Get context manager for tracking usage metadata across chat model calls using
    ``AIMessage.usage_metadata``.
    """
    cb = OllamaCallbackHandler()
    ollama_callback_var.set(cb)
    yield cb
    ollama_callback_var.set(None)
