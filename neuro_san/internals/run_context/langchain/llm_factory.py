
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

from neuro_san.internals.run_context.langchain.llm_info_restorer import LlmInfoRestorer


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

    def __init__(self):
        """
        Constructor
        """
        self.llm_infos: Dict[str, Any] = {}
        self.overlayer = DictionaryOverlay()

    def load(self):
        """
        Loads the LLM information from hocon files.
        """
        restorer = LlmInfoRestorer()
        self.llm_infos = restorer.restore()

        # Mix in user-specified llm info, if available.
        llm_info_file: str = os.getenv("AGENT_LLM_INFO_FILE")
        if llm_info_file is not None and len(llm_info_file) > 0:
            extra_llm_infos: Dict[str, Any] = restorer.restore(file_reference=llm_info_file)
            self.llm_infos = self.overlayer.overlay(self.llm_infos, extra_llm_infos)

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
        default_config: Dict[str, Any] = self.llm_infos.get("default_config")
        use_config = self.overlayer.overlay(default_config, config)

        model_name = use_config.get("model_name")

        llm_entry = self.llm_infos.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        # Get some bits from the llm_entry
        api_key = llm_entry.get("api_key")
        use_model_name = llm_entry.get("use_model_name", model_name)

        chat_class_name: str = llm_entry.get("class")
        base_class: Type[BaseLanguageModel] = self.get_chat_class(chat_class_name)

        use_max_tokens = self.get_max_prompt_tokens(use_config)

        # Construct the LLM
        llm: BaseLanguageModel = None
        if base_class == ChatOpenAI:
            # Higher temperature is more random
            llm = ChatOpenAI(
                            temperature=use_config.get("temperature"),
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
                            temperature=use_config.get("temperature"),
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
                            temperature=use_config.get("temperature"),
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
                            temperature=use_config.get("temperature"),
                            num_predict=use_max_tokens,
                            model=use_model_name,
                            callbacks=callbacks)
        elif base_class == ChatNVIDIA:
            # Higher temperature is more random
            llm = ChatNVIDIA(
                            temperature=use_config.get("temperature"),
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

        default_config = self.llm_infos.get("default_config")
        use_config = self.overlayer.overlay(default_config, config)

        token_encoding = use_config.get("token_encoding")
        if token_encoding is None:
            model_name = use_config.get("model_name")

            llm_entry = self.llm_infos.get(model_name)
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

        default_config = self.llm_infos.get("default_config")
        use_config = self.overlayer.overlay(default_config, config)

        model_name = use_config.get("model_name")

        llm_entry = self.llm_infos.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        entry_max_tokens = llm_entry.get("max_tokens")
        prompt_token_fraction = use_config.get("prompt_token_fraction")
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
