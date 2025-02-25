
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


class LangChainTokenCounter:
    """
    Helps with per-llm means of counting tokens.
    """

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
            }

        return token_dict
