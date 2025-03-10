
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

import os

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

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
        full_config: Dict[str, Any] = self.create_full_llm_config(config)
        llm: BaseLanguageModel = self.create_base_chat_model(full_config, callbacks)
        return llm

    def create_full_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param config: The llm_config from the user
        :return: The fully specified config with defaults filled in.
        """
        default_config: Dict[str, Any] = self.llm_infos.get("default_config")
        use_config = self.overlayer.overlay(default_config, config)

        model_name = use_config.get("model_name")

        llm_entry = self.llm_infos.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        # Get some bits from the llm_entry
        use_model_name = llm_entry.get("use_model_name", model_name)
        if len(llm_entry.keys()) <= 2 and use_model_name is not None:
            # We effectively have an alias. Switch out the llm entry.
            llm_entry = self.llm_infos.get(use_model_name)

        # Take a look at the chat classes.
        chat_class_name: str = llm_entry.get("class")
        if chat_class_name is None:
            raise ValueError(f"llm info entry for {use_model_name} requires a 'class' key/value pair.")

        # Get defaults for the chat class
        chat_args: Dict[str, Any] = self.get_chat_class_args(chat_class_name, use_model_name)

        # Get a new sense of the default config now that we have the default args for the chat class.
        default_config = self.overlayer.overlay(chat_args, default_config)

        # Now that we have the true defaults, overlay the config that came in to get the
        # config we are going to use.
        full_config: Dict[str, Any] = self.overlayer.overlay(default_config, config)
        full_config["class"] = chat_class_name

        # Attempt to get a max_tokens through calculation
        full_config["max_tokens"] = self.get_max_prompt_tokens(full_config)

        return full_config

    def get_chat_class_args(self, chat_class_name: str, use_model_name: str) -> Dict[str, Any]:
        """
        :param chat_class_name: string name of the chat class to look up.
        :param use_model_name: the original model name that prompted the chat class lookups
        :return: A dictionary of default arguments for the chat class.
                Can throw an exception if the chat class does not exist.
        """

        # Find the chat class.
        chat_classes: Dict[str, Any] = self.llm_infos.get("classes")
        chat_class: Dict[str, Any] = chat_classes.get(chat_class_name)
        if chat_class is None:
            raise ValueError(f"llm info entry for {use_model_name} uses a 'class' of {chat_class_name} "
                             "which is not defined in the 'classes' table.")

        # Get the args from the chat class
        args: Dict[str, Any] = chat_class.get("args")

        extends: str = chat_class.get("extends")
        if extends is not None:
            # If this class extends another, get its args too.
            extends_args: Dict[str, Any] = self.get_chat_class_args(extends, use_model_name)
            args = self.overlayer.overlay(args, extends_args)

        return args

    def create_base_chat_model(self, config: Dict[str, Any],
                               callbacks: List[BaseCallbackHandler] = None) -> BaseLanguageModel:
        """
        Create a BaseLanguageModel from the fully-specified llm config.
        :param config: The fully specified llm config which is a product of
                    _create_full_llm_config() above.
        :param callbacks: A list of BaseCallbackHandlers to add to the chat model.
        :return: A BaseLanguageModel (can be Chat or LLM)
                Can raise a ValueError if the config's class or model_name value is
                unknown to this method.
        """
        # Construct the LLM
        llm: BaseLanguageModel = None
        chat_class: str = config.get("class")
        if chat_class is not None:
            chat_class = chat_class.lower()

        model_name: str = config.get("model_name")

        if chat_class == "openai":
            llm = ChatOpenAI(
                            model_name=model_name,
                            temperature=config.get("temperature"),
                            openai_api_key=self.get_value_or_env(config, "openai_api_key",
                                                                 "OPENAI_API_KEY"),
                            openai_api_base=self.get_value_or_env(config, "openai_api_base",
                                                                  "OPENAI_API_BASE"),
                            openai_organization=self.get_value_or_env(config, "openai_organization",
                                                                      "OPENAI_ORG_ID"),
                            openai_proxy=self.get_value_or_env(config, "openai_organization",
                                                               "OPENAI_PROXY"),
                            request_timeout=config.get("request_timeout"),
                            max_retries=config.get("max_retries"),
                            presence_penalty=config.get("presence_penalty"),
                            frequency_penalty=config.get("frequency_penalty"),
                            seed=config.get("seed"),
                            logprobs=config.get("logprobs"),
                            top_logprobs=config.get("top_logprobs"),
                            logit_bias=config.get("logit_bias"),
                            streaming=True,     # streaming is always on. Without it token counting will not work.
                            n=1,                # n is always 1.  neuro-san will only ever consider one chat completion.
                            top_p=config.get("top_p"),
                            max_tokens=config.get("max_tokens"),    # This is always for output
                            tiktoken_model_name=config.get("tiktoken_model_name"),
                            stop=config.get("stop"),

                            # Set stream_usage to True in order to get token counting chunks.
                            stream_usage=True,
                            callbacks=callbacks)
        elif chat_class == "azure-openai":
            llm = AzureChatOpenAI(
                            model_name=model_name,
                            temperature=config.get("temperature"),
                            openai_api_key=self.get_value_or_env(config, "openai_api_key",
                                                                 "OPENAI_API_KEY"),
                            openai_api_base=self.get_value_or_env(config, "openai_api_base",
                                                                  "OPENAI_API_BASE"),
                            openai_organization=self.get_value_or_env(config, "openai_organization",
                                                                      "OPENAI_ORG_ID"),
                            openai_proxy=self.get_value_or_env(config, "openai_organization",
                                                               "OPENAI_PROXY"),
                            request_timeout=config.get("request_timeout"),
                            max_retries=config.get("max_retries"),
                            presence_penalty=config.get("presence_penalty"),
                            frequency_penalty=config.get("frequency_penalty"),
                            seed=config.get("seed"),
                            logprobs=config.get("logprobs"),
                            top_logprobs=config.get("top_logprobs"),
                            logit_bias=config.get("logit_bias"),
                            streaming=True,     # streaming is always on. Without it token counting will not work.
                            n=1,                # n is always 1.  neuro-san will only ever consider one chat completion.
                            top_p=config.get("top_p"),
                            max_tokens=config.get("max_tokens"),    # This is always for output
                            tiktoken_model_name=config.get("tiktoken_model_name"),
                            stop=config.get("stop"),

                            # Azure-specific
                            azure_endpoint=self.get_value_or_env(config, "azure_endpoint",
                                                                 "AZURE_OPENAI_ENDPOINT"),
                            deployment_name=config.get("deployment_name"),
                            openai_api_version=self.get_value_or_env(config, "openai_api_version",
                                                                     "OPENAI_API_VERSION"),

                            # AD here means "ActiveDirectory"
                            azure_ad_token=self.get_value_or_env(config, "azure_ad_token",
                                                                 "AZURE_OPENAI_AD_TOKEN"),
                            model_version=config.get("model_version"),
                            openai_api_type=self.get_value_or_env(config, "openai_api_type",
                                                                  "OPENAI_API_TYPE"),
                            callbacks=callbacks)
        elif chat_class == "anthropic":
            llm = ChatAnthropic(
                            model_name=model_name,
                            max_tokens=config.get("max_tokens"),    # This is always for output
                            temperature=config.get("temperature"),
                            top_k=config.get("top_k"),
                            top_p=config.get("top_p"),
                            default_request_timeout=config.get("default_request_timeout"),
                            max_retries=config.get("max_retries"),
                            stop_sequences=config.get("stop_sequences"),
                            anthropic_api_url=self.get_value_or_env(config, "anthropic_api_url",
                                                                    "ANTHROPIC_API_URL"),
                            anthropic_api_key=self.get_value_or_env(config, "anthropic_api_key",
                                                                    "ANTHROPIC_API_KEY"),
                            streaming=True,     # streaming is always on. Without it token counting will not work.
                            # Set stream_usage to True in order to get token counting chunks.
                            stream_usage=True,
                            callbacks=callbacks)
        elif chat_class == "ollama":
            # Higher temperature is more random
            llm = ChatOllama(
                            model=model_name,
                            mirostat=config.get("mirostat"),
                            mirostat_eta=config.get("mirostat_eta"),
                            mirostat_tau=config.get("mirostat_tau"),
                            num_ctx=config.get("num_ctx"),
                            num_gpu=config.get("num_gpu"),
                            num_thread=config.get("num_thread"),
                            num_predict=config.get("num_predict", config.get("max_tokens")),
                            repeat_last_n=config.get("repeat_last_n"),
                            repeat_penalty=config.get("repeat_penalty"),
                            temperature=config.get("temperature"),
                            seed=config.get("seed"),
                            stop=config.get("stop"),
                            tfs_z=config.get("tfs_z"),
                            top_k=config.get("top_k"),
                            top_p=config.get("top_p"),
                            keep_alive=config.get("keep_alive"),
                            base_url=config.get("base_url"),

                            callbacks=callbacks)
        elif chat_class == "nvidia":
            # Higher temperature is more random
            llm = ChatNVIDIA(
                            base_url=config.get("base_url"),
                            model=model_name,
                            temperature=config.get("temperature"),
                            max_tokens=config.get("max_tokens"),
                            top_p=config.get("top_p"),
                            seed=config.get("seed"),
                            stop=config.get("stop"),
                            nvidia_api_key=self.get_value_or_env(config, "nvidia_api_key",
                                                                 "NVIDIA_API_KEY"),
                            nvidia_base_url=self.get_value_or_env(config, "nvidia_base_url",
                                                                  "NVIDIA_BASE_URL"),
                            callbacks=callbacks)
        elif chat_class is None:
            raise ValueError(f"Class name {chat_class} for model_name {model_name} is unspecified.")
        else:
            raise ValueError(f"Class {chat_class} for model_name {model_name} is unrecognized.")

        return llm

    def get_max_prompt_tokens(self, config: Dict[str, Any]) -> int:
        """
        :param config: A dictionary which describes which LLM to use.
        :return: The maximum number of tokens given the 'model_name' in the
                config dictionary.
        """

        model_name = config.get("model_name")

        llm_entry = self.llm_infos.get(model_name)
        if llm_entry is None:
            raise ValueError(f"No llm entry for model_name {model_name}")

        use_model_name = llm_entry.get("use_model_name", model_name)
        if len(llm_entry.keys()) <= 2 and use_model_name is not None:
            # We effectively have an alias. Switch out the llm entry.
            llm_entry = self.llm_infos.get(use_model_name)

        entry_max_tokens = llm_entry.get("max_output_tokens")
        prompt_token_fraction = config.get("prompt_token_fraction")
        use_max_tokens = int(entry_max_tokens * prompt_token_fraction)

        # Allow the actual value for max_tokens to come from the config, if there
        max_prompt_tokens = config.get("max_tokens", use_max_tokens)
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
