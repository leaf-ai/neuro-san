
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

import threading
from typing import Any
from typing_extensions import override

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult


class OllamaCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that tracks token usage via "AIMessage.usage_metadata".

    This class is a modification of LangChain’s "UsageMetadataCallbackHandler" and "OpenAICallbackHandler":
    - https://python.langchain.com/api_reference/_modules/langchain_core/callbacks/usage.html
    #get_usage_metadata_callback
    - https://python.langchain.com/api_reference/_modules/langchain_community/callbacks/openai_info.html
    #OpenAICallbackHandler

    It collects token usage from the "usage_metadata" field of "AIMessage" each time an LLM or chat model
    finishes execution.
    The metadata is a dictionary that may include:
    - "input_tokens" (collected as "prompt_tokens")
    - "output_tokens" (collected as "completion_tokens")
    - "total_tokens"

    This handler tracks these values internally and is compatible with models that populate "usage_metadata",
    regardless of provider.

    **Note**: While the "AIMessage.response_data" may contain model names, they are not currently included in the
    report format. A future version may support returning usage statistics grouped by model name.

    Example of expected future output structure (not currently implemented):

        {
            "gpt-4o-mini-2024-07-18": {
                "input_tokens": 8,
                "output_tokens": 10,
                "total_tokens": 18,
                "input_token_details": {"audio": 0, "cache_read": 0},
                "output_token_details": {"audio": 0, "reasoning": 0}
            },
            "claude-3-5-haiku-20241022": {
                "input_tokens": 8,
                "output_tokens": 21,
                "total_tokens": 29,
                "input_token_details": {"cache_read": 0, "cache_creation": 0}
            }
        }

    Note: Ollama models currently have no associated cost, so "total_cost" is always set to 0.0 for compatibility with
    reporting templates.
    """

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0
    # There is no cost for Ollama model. Define "total_cost" and set at 0.0 to fit the report template.
    total_cost: float = 0.0

    def __init__(self) -> None:
        """Initialize the CallbackHandler."""
        super().__init__()
        self._lock = threading.Lock()

    @override
    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.total_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"Successful Requests: {self.successful_requests}\n"
            f"Total Cost (USD): ${self.total_cost}"
        )

    @override
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Collect token usage when llm ends.
        :param response: Output from chat model
        """
        # Check for usage_metadata (Only work for langchain-core >= 0.2.2)
        try:
            generation = response.generations[0][0]
        except IndexError:
            generation = None

        usage_metadata = None
        if isinstance(generation, ChatGeneration):
            try:
                message = generation.message
                if isinstance(message, AIMessage):
                    # Token info is in an attribute of AIMessage called "usage_metadata".
                    usage_metadata: UsageMetadata = message.usage_metadata
            except AttributeError:
                pass

        if usage_metadata:
            total_tokens: int = usage_metadata.get("total_tokens", 0)
            completion_tokens: int = usage_metadata.get("output_tokens", 0)
            prompt_tokens: int = usage_metadata.get("input_tokens", 0)

            # update shared state behind lock
            with self._lock:
                self.total_tokens += total_tokens
                self.prompt_tokens += prompt_tokens
                self.completion_tokens += completion_tokens
                self.successful_requests += 1
