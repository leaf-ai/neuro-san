
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

import asyncio
from typing import Any
from typing import Dict
from typing import List
from typing_extensions import override

from langchain_community.callbacks.bedrock_anthropic_callback import MODEL_COST_PER_1K_INPUT_TOKENS
from langchain_community.callbacks.bedrock_anthropic_callback import MODEL_COST_PER_1K_OUTPUT_TOKENS
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult

EMPTY = ""


def calculate_anthropic_token_cost(input_tokens: int, output_tokens: int, model_name: str) -> float:
    """
    Calculate the token cost for an Anthropic Claude model from lookup table MODEL_COST_PER_1K_INPUT_TOKENS
    and MODEL_COST_PER_1K_OUTPUT_TOKENS.

    This function allows users to input a partial model name (e.g., 'claude-3-7-sonnet-20250219')
    instead of requiring the full internal model ID (e.g., 'anthropic.claude-3-7-sonnet-20250219-v1:0').

    Since users often do not know or use the full system-defined model names,
    we perform a flexible substring match across all known models:
    - If exactly one match is found, we calculate the cost based on that model.
    - If multiple matches are found, we return 0.0 and print an error to alert the user.
    - If no matches are found, we also return 0.0 and print an error.

    :param prompt_tokens: Number of input (prompt) tokens.
    :param completion_tokens: Number of output (completion) tokens.
    :param model_name: A model name (e.g., 'claude-3-7-sonnet-20250219').

    :return: The total cost as a float.
    """

    if not model_name:
        print("[Error] model_name must be provided.")
        return 0.0

    # Check if "model_name" is in any keys of the lookup table.
    matching_models: List[str] = [
        model for model in MODEL_COST_PER_1K_INPUT_TOKENS if model_name in model
    ]

    # Return cost = 0.0 if there are no match or more than one matches.
    if not matching_models:
        print(
            f"[Error] Unknown model: '{model_name}'. No matches found. "
            "Known models are: " + ", ".join(MODEL_COST_PER_1K_INPUT_TOKENS.keys())
        )
        return 0.0

    if len(matching_models) > 1:
        print(
            f"[Error] Ambiguous model name '{model_name}'. Matches multiple models: "
            + ", ".join(matching_models)
        )
        return 0.0

    full_model_id: str = matching_models[0]

    input_cost: float = (input_tokens / 1000) * MODEL_COST_PER_1K_INPUT_TOKENS[full_model_id]
    output_cost: float = (output_tokens / 1000) * MODEL_COST_PER_1K_OUTPUT_TOKENS[full_model_id]
    return input_cost + output_cost


# pylint: disable=too-many-ancestors
class LlmTokenCallbackHandler(AsyncCallbackHandler):
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

    Note:
    This class is intended for use with Ollama models, as OpenAICallbackHandler and
    BedrockAnthropicTokenUsageCallbackHandler already handle OpenAI and Anthropic models, respectively.
    Ollama models currently have no associated cost, so total_cost is always set to 0.0 to maintain compatibility
    with reporting templates.
    """

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0

    def __init__(self) -> None:
        """Initialize the CallbackHandler."""
        super().__init__()
        self._lock = asyncio.Lock()

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
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Collect token usage when llm ends.
        :param response: Output from chat model
        """
        # Check for usage_metadata (Only work for langchain-core >= 0.2.2)
        try:
            generation = response.generations[0][0]
        except IndexError:
            generation = None

        usage_metadata: UsageMetadata = None
        response_metadata: Dict[str, Any] = None
        model_name: str = EMPTY
        if isinstance(generation, ChatGeneration):
            try:
                message = generation.message
                if isinstance(message, AIMessage):
                    # Token info is in an attribute of AIMessage called "usage_metadata".
                    usage_metadata = message.usage_metadata
                    # Get model name so that cost can be determined if needed.
                    response_metadata = message.response_metadata
                    if response_metadata:
                        if "model_name" in response_metadata:
                            model_name = response_metadata.get("model_name")
                        elif "model_id" in response_metadata:
                            model_name = response_metadata.get("model_id")
                        elif "model" in response_metadata:
                            model_name = response_metadata.get("model")
            except AttributeError:
                pass

        if usage_metadata:
            total_tokens: int = usage_metadata.get("total_tokens", 0)
            completion_tokens: int = usage_metadata.get("output_tokens", 0)
            prompt_tokens: int = usage_metadata.get("input_tokens", 0)

            # If it is an anthropic model, calculate the cost.
            if "claude" in model_name:
                total_cost: float = calculate_anthropic_token_cost(prompt_tokens, completion_tokens, model_name)
            else:
                total_cost = 0.0

            # update shared state behind lock
            async with self._lock:
                self.total_tokens += total_tokens
                self.prompt_tokens += prompt_tokens
                self.completion_tokens += completion_tokens
                self.successful_requests += 1
                self.total_cost += total_cost
