
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
from typing import List
from typing import Type

import os

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

from tiktoken import Encoding
from tiktoken import encoding_for_model
from tiktoken import get_encoding

from leaf_common.config.dictionary_overlay import DictionaryOverlay

DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7

# Max tokens in the docs is a combination of prompt tokens + response tokens
# Use this fraction as a default split between what we expect between
# prompt and response.
DEFAULT_PROMPT_TOKEN_FRACTION = 0.5

LLM_ENTRIES = {
    # Model context and output tokens: https://platform.openai.com/docs/models
    # Model compatibility: https://platform.openai.com/docs/models#model-endpoint-compatibility
    "gpt-3.5-turbo": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "gpt-3.5-turbo-16k": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 16384  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "gpt-4o": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models says 16,384
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4o-mini": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models says 16,384
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-turbo": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-turbo says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-turbo-preview": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-turbo-preview says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-1106-preview": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-1106-preview says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-vision-preview": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-vision-preview says 12800
                            # but that is for input. Not yet tested
    },
    "gpt-4": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4 says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-32k": {
        "class": "openai",
        "api_key": "openai_api_key",
        "max_tokens": 32768  # From https://platform.openai.com/docs/models/gpt-4-32k
    },
    "azure-gpt-3.5-turbo": {
        "use_model_name": "gpt-3.5-turbo",
        "class": "azure-openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "azure-gpt-4": {
        "use_model_name": "gpt-4",
        "class": "azure-openai",
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4 says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "claude-3-haiku": {
        "use_model_name": "claude-3-haiku-20240307",
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-3-sonnet": {
        "use_model_name": "claude-3-sonnet-20240229",
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-3-opus": {
        "use_model_name": "claude-3-opus-20240229",
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-2.1": {
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-2.0": {
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-instant-1.2": {
        "class": "anthropic",
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "llama2": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llama3": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llama3.1": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llama3:70b": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llava": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "mistral": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "mistral-nemo": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "mixtral": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "qwen2.5:14b": {
        "class": "ollama",
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "deepseek-r1:14b": {  # Does not support tools
        "class": "ollama",
        "max_tokens": 4096
    },
    "nvidia-llama-3.1-405b-instruct": {
        "use_model_name": "meta/llama-3.1-405b-instruct",
        "class": "nvidia",
        "api_key": "nvidia_api_key",
        "max_tokens": 4096  # From https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/
    },
    "nvidia-llama-3.3-70b-instruct": {
        "use_model_name": "meta/llama-3.3-70b-instruct",
        "class": "nvidia",
        "api_key": "nvidia_api_key",
        "max_tokens": 4096  # From https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/
    },
    "nvidia-deepseek-r1": {
        "use_model_name": "deepseek-ai/deepseek-r1",
        "class": "nvidia",
        "api_key": "nvidia_api_key",
        "max_tokens": 4096  # From https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/
    },
}


DEFAULT_CONFIG = {

    "model_name": DEFAULT_MODEL,            # The string name of the default model to use.
                                            # Default if not specified is "gpt-3.5-turbo"

    "temperature": DEFAULT_TEMPERATURE,     # The default LLM temperature (randomness) to use.
                                            # Values are floats between 0.0 (least random) to
                                            # 1.0 (most random).

    "token_encoding": None,                 # The tiktoken encoding name to use with the
                                            # create_tokenizer() method.  If not specified,
                                            # tiktoken has a default for each model_name.

    "prompt_token_fraction": DEFAULT_PROMPT_TOKEN_FRACTION,
                                            # The fraction of total tokens (not necessarily words
                                            # or letters) to use for a prompt. Each model_name
                                            # has a documented number of max_tokens it can handle
                                            # which is a total count of message + response tokens
                                            # which goes into the calculation involved in
                                            # get_max_prompt_tokens().
                                            # By default the value is 0.5.

    "max_tokens": None,                     # The maximum number of tokens to use in
                                            # computing prompt tokens. By default this comes from
                                            # the model description in this class.

    "verbose": False,                       # When True, responses from ChatEngine are logged to stdout

    "openai_api_key": None,                 # The string api key to use when accessing an LLM.
                                            # Default is None, which indicates that the code should
                                            # get the value from the OS environment variable
                                            # OPENAI_API_KEY.  This is true for OpenAI LLM models,
                                            # which is the default and most often used. However, the name
                                            # of the API key itself can be  different depending on the model
                                            # and its own norms.


    # The following keys are used with Azure OpenAI models.

    "openai_api_base": None,                # The string url to use when accessing an Azure OpenAI model.
                                            # By default this value is None, which indicates the value
                                            # should come from the OS environment variable OPENAI_API_BASE.

    "openai_api_version": None,             # The string version to use when accessing an Azure OpenAI model.
                                            # By default this value is None, which indicates the value
                                            # should come from the OS environment variable OPENAI_API_VERSION.

    "openai_proxy": None,                   # The string version to use when accessing an Azure OpenAI model.
                                            # By default this value is None, which indicates the value
                                            # should come from the OS environment variable OPENAI_PROXY.

    "openai_api_type": None,                # The string type to use when accessing an Azure OpenAI model.
                                            # By default this value is None, which indicates the value
                                            # should come from the OS environment variable OPENAI_API_TYPE.
    # The following keys are used with Azure OpenAI models.
    "nvidia_api_key": None,
}


class LlmFactory:
    """
    Factory class for LLM operations

    Most methods take a config dictionary which consists of the following keys:

        "model_name"                The name of the model.
                                    Default if not specified is "gpt-3.5-turbo"

        "temperature"               A float "temperature" value with which to
                                    initialize the chat model.  In general,
                                    higher temperatures yield more random results.
                                    Default if not specified is 0.7

        "token_encoding"            The tiktoken encoding name to use with the
                                    create_tokenizer() method.  If not specified,
                                    tiktoken has a default for each model_name.

        "prompt_token_fraction"     The fraction of total tokens (not necessarily words
                                    or letters) to use for a prompt. Each model_name
                                    has a documented number of max_tokens it can handle
                                    which is a total count of message + response tokens
                                    which goes into the calculation involved in
                                    get_max_prompt_tokens().
                                    By default the value is 0.5.

        "max_tokens"                The maximum number of tokens to use in
                                    get_max_prompt_tokens(). By default this comes from
                                    the model description in this class.

        "openai_api_key"            Key for OpenAI API access.
                                    Required for OpenAI and Azure model_names.

        "openai_api_base"           This assortment of config keys are for use
        "openai_api_version"        with Azure-hosted OpenAI models
        "openai_proxy"
        "openai_api_type"
        "nvidia_api_key"
    """

    def create_llm(self, config: Dict[str, Any], callbacks: List[BaseCallbackHandler] = None) -> BaseLanguageModel:
        """
        Creates a langchain LLM based on the 'model_name' value of
        the config passed in.

        :param config: A dictionary which describes which LLM to use.
                See the class comment for details.
        :param callbacks: A list of BaseCallbackHandlers to add to the chat model.
        :return: A BaseLanguageModel (can be Chat or LLM)
                Can raise a ValueError if the config's model_name value is
                unknown to this method.
        """
        overlayer = DictionaryOverlay()
        use_config = overlayer.overlay(DEFAULT_CONFIG, config)

        model_name = use_config.get("model_name", DEFAULT_MODEL)

        llm_entry = LLM_ENTRIES.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        # Get some bits from the llm_entry
        chat_class_name: str = llm_entry.get("class")
        api_key = llm_entry.get("api_key")
        use_model_name = llm_entry.get("use_model_name", model_name)

        base_class: Type[BaseLanguageModel] = self.get_chat_class(chat_class_name)

        use_max_tokens = self.get_max_prompt_tokens(use_config)

        # Construct the LLM
        llm: BaseLanguageModel = None
        if base_class == ChatOpenAI:
            # Higher temperature is more random
            llm = ChatOpenAI(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            openai_api_key=self.get_value_or_env(use_config, api_key,
                                                                 "OPENAI_API_KEY"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name,
                            callbacks=callbacks,
                            # Set stream_usage to True in order to get token counting chunks.
                            stream_usage=True)
        elif base_class == AzureChatOpenAI:
            # Higher temperature is more random
            llm = AzureChatOpenAI(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            openai_api_key=self.get_value_or_env(use_config, api_key,
                                                                 "OPENAI_API_KEY"),
                            openai_api_base=self.get_value_or_env(use_config, "openai_api_base",
                                                                  "OPENAI_API_BASE"),
                            openai_api_version=self.get_value_or_env(use_config, "openai_api_version",
                                                                     "OPENAI_API_VERSION"),
                            openai_proxy=self.get_value_or_env(use_config, "openai_proxy",
                                                               "OPENAI_PROXY"),
                            openai_api_type=self.get_value_or_env(use_config, "openai_api_type",
                                                                  "OPENAI_API_TYPE"),
                            azure_endpoint=self.get_value_or_env(use_config, "azure_endpoint",
                                                                 "AZURE_OPENAI_ENDPOINT"),
                            # AD here means "ActiveDirectory"
                            azure_ad_token=self.get_value_or_env(use_config, "azure_ad_token",
                                                                 "AZURE_OPENAI_AD_TOKEN"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name,
                            callbacks=callbacks)
        elif base_class == ChatAnthropic:
            # Higher temperature is more random
            llm = ChatAnthropic(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            anthropic_api_key=self.get_value_or_env(use_config, api_key,
                                                                    "ANTHROPIC_API_KEY"),
                            anthropic_api_url=self.get_value_or_env(use_config, "anthropic_api_url",
                                                                    "ANTHROPIC_API_URL"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name,
                            callbacks=callbacks)
        elif base_class == ChatOllama:
            # Higher temperature is more random
            llm = ChatOllama(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            num_predict=use_max_tokens,
                            model=use_model_name,
                            callbacks=callbacks)
        elif base_class == ChatNVIDIA:
            # Higher temperature is more random
            llm = ChatNVIDIA(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            nvidia_api_key=self.get_value_or_env(use_config, api_key,
                                                                 "NVIDIA_API_KEY"),
                            max_tokens=use_max_tokens,
                            model=use_model_name,
                            callbacks=callbacks)
        elif base_class is None:
            raise ValueError(f"Class name {chat_class_name} for model_name {model_name} is unrecognized")
        else:
            raise ValueError(f"Class {base_class.__name__} for model_name {model_name} unknown")

        return llm

    def get_chat_class(self, chat_class_name: str) -> Type[BaseLanguageModel]:
        """
        :param chat_class_name: The name of the chat class.
        :return: The actual class corresponding to that name
        """

        if chat_class_name is None or not isinstance(chat_class_name, str):
            return None

        low_class: str = chat_class_name.lower()

        chat_class_lookup: Dict[str, Type[BaseLanguageModel]] = {
            "azure-openai": AzureChatOpenAI,
            "openai": ChatOpenAI,
            "anthropic": ChatAnthropic,
            "nvidia": ChatNVIDIA,
            "ollama": ChatOllama,
        }

        chat_class: Type[BaseLanguageModel] = chat_class_lookup.get(low_class)

        return chat_class

    def create_tokenizer(self, config: Dict[str, Any]) -> Encoding:
        """
        Creates a tiktoken tokenizer based on the 'model_name' value of
        the config passed in.

        :param config: A dictionary which describes which LLM to use.
                See the class comment for details.
        :return: A Encoding
                Can raise a ValueError if the config's model_name value is
                unknown to this method.
        """
        tokenizer: Encoding = None

        overlayer = DictionaryOverlay()
        use_config = overlayer.overlay(DEFAULT_CONFIG, config)

        token_encoding = use_config.get("token_encoding")
        if token_encoding is None:
            model_name = use_config.get("model_name", DEFAULT_MODEL)

            llm_entry = LLM_ENTRIES.get(model_name)
            if llm_entry is None:
                raise ValueError(f"No tokenizer entry for model_name {model_name}")

            # Get some bits from the llm_entry
            token_encoding = llm_entry.get("token_encoding")

            if token_encoding is None:
                # Use the model name to construct the encoding
                use_model_name = llm_entry.get("use_model_name", model_name)
                tokenizer = encoding_for_model(use_model_name)

        if tokenizer is None:
            # Construct the tokenizer from the token_encoding
            tokenizer = get_encoding(token_encoding)

        return tokenizer

    def get_max_prompt_tokens(self, config: Dict[str, Any]) -> int:
        """
        :param config: A dictionary which describes which LLM to use.
                See the class comment for details.
        :return: The maximum number of tokens given the 'model_name' in the
                config dictionary.
        """

        overlayer = DictionaryOverlay()
        use_config = overlayer.overlay(DEFAULT_CONFIG, config)

        model_name = use_config.get("model_name", DEFAULT_MODEL)

        llm_entry = LLM_ENTRIES.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        entry_max_tokens = llm_entry.get("max_tokens")
        prompt_token_fraction = use_config.get("prompt_token_fraction",
                                               DEFAULT_PROMPT_TOKEN_FRACTION)
        use_max_tokens = int(entry_max_tokens * prompt_token_fraction)

        # Allow the actual value for max_tokens to come from the config, if there
        max_prompt_tokens = use_config.get("max_tokens", use_max_tokens)
        if max_prompt_tokens is None:
            max_prompt_tokens = use_max_tokens

        return max_prompt_tokens

    def get_value_or_env(self, config: Dict[str, Any], key: str, env_key: str) -> Any:
        """
        :param config: The config dictionary to search
        :param key: The key for the config to look for
        :param env_key: The os.environ key whose value should be gotten if either
                        the key does not exist or the value for the key is None
        """
        value = None
        if config is not None:
            value = config.get(key)

        if value is None:
            value = os.getenv(env_key)

        return value
