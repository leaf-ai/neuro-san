
from typing import Any
from typing import Dict

import os

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_community.chat_models.ollama import ChatOllama
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

    "gpt-3.5-turbo": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "gpt-3.5-turbo-16k": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 16384  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "gpt-4o": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-turbo says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-turbo": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-turbo says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-turbo-preview": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-turbo-preview says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-1106-preview": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-1106-preview says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-vision-preview": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4-vision-preview says 12800
                            # but that is for input. Not yet tested
    },
    "gpt-4": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4 says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "gpt-4-32k": {
        "class": ChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 32768  # From https://platform.openai.com/docs/models/gpt-4-32k
    },
    "azure-gpt-3.5-turbo": {
        "use_model_name": "gpt-3.5-turbo",
        "class": AzureChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # From https://platform.openai.com/docs/models/gpt-3-5
    },
    "azure-gpt-4": {
        "use_model_name": "gpt-4",
        "class": AzureChatOpenAI,
        "api_key": "openai_api_key",
        "max_tokens": 4096  # https://platform.openai.com/docs/models/gpt-4 says 12800
                            # but that is for input, and empirical evidence shows this is
                            # the number required for output.
    },
    "claude-3-haiku": {
        "use_model_name": "claude-3-haiku-20240307",
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-3-sonnet": {
        "use_model_name": "claude-3-sonnet-20240229",
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-3-opus": {
        "use_model_name": "claude-3-opus-20240229",
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-2.1": {
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-2.0": {
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "claude-instant-1.2": {
        "class": ChatAnthropic,
        "api_key": "anthropic_api_key",
        "max_tokens": 4096  # From https://docs.anthropic.com/en/docs/models-overview
    },
    "llama2": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llama3": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llama3:70b": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "llava": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "mistral": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
    },
    "mixtral": {
        "class": ChatOllama,
        "max_tokens": 4096  # Scant from https://github.com/ollama/ollama
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
    """

    @staticmethod
    def create_llm(config: Dict[str, Any]) -> BaseLanguageModel:
        """
        Creates a langchain LLM based on the 'model_name' value of
        the config passed in.

        :param config: A dictionary which describes which LLM to use.
                See the class comment for details.
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
        base_class = llm_entry.get("class")
        api_key = llm_entry.get("api_key")
        use_model_name = llm_entry.get("use_model_name", model_name)

        use_max_tokens = LlmFactory.get_max_prompt_tokens(use_config)

        # Construct the LLM
        llm: BaseLanguageModel = None
        if base_class == ChatOpenAI:
            # Higher temperature is more random
            llm = ChatOpenAI(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            openai_api_key=LlmFactory.get_value_or_env(use_config, api_key,
                                                                       "OPENAI_API_KEY"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name)
        elif base_class == AzureChatOpenAI:
            # Higher temperature is more random
            llm = AzureChatOpenAI(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            openai_api_key=LlmFactory.get_value_or_env(use_config, api_key,
                                                                       "OPENAI_API_KEY"),
                            openai_api_base=LlmFactory.get_value_or_env(use_config, "openai_api_base",
                                                                        "OPENAI_API_BASE"),
                            openai_api_version=LlmFactory.get_value_or_env(use_config, "openai_api_version",
                                                                           "OPENAI_API_VERSION"),
                            openai_proxy=LlmFactory.get_value_or_env(use_config, "openai_proxy",
                                                                     "OPENAI_PROXY"),
                            openai_api_type=LlmFactory.get_value_or_env(use_config, "openai_api_type",
                                                                        "OPENAI_API_TYPE"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name)
        elif base_class == ChatAnthropic:
            # Higher temperature is more random
            llm = ChatAnthropic(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            anthropic_api_key=LlmFactory.get_value_or_env(use_config, api_key,
                                                                          "ANTHROPIC_API_KEY"),
                            anthropic_api_url=LlmFactory.get_value_or_env(use_config, "anthropic_api_url",
                                                                          "ANTHROPIC_API_URL"),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name)
        elif base_class == ChatOllama:
            # Higher temperature is more random
            llm = ChatOllama(
                            temperature=use_config.get("temperature", DEFAULT_TEMPERATURE),
                            max_tokens=use_max_tokens,
                            model_name=use_model_name)
        else:
            raise ValueError(f"Class {base_class.__name__} for model_name {model_name} unknown")

        return llm

    @staticmethod
    def create_tokenizer(config: Dict[str, Any]) -> Encoding:
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

    @staticmethod
    def get_max_prompt_tokens(config: Dict[str, Any]) -> int:
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

    @staticmethod
    def get_value_or_env(config: Dict[str, Any], key: str, env_key: str) -> Any:
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
