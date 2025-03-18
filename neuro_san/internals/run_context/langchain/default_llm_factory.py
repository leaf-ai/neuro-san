
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

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel

from leaf_common.config.dictionary_overlay import DictionaryOverlay

from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.run_context.langchain.langchain_llm_factory import LangChainLlmFactory
from neuro_san.internals.run_context.langchain.llm_info_restorer import LlmInfoRestorer
from neuro_san.internals.run_context.langchain.standard_langchain_llm_factory import StandardLangChainLlmFactory


class DefaultLlmFactory(ContextTypeLlmFactory, LangChainLlmFactory):
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
        self.llm_factories: List[LangChainLlmFactory] = [
            StandardLangChainLlmFactory()
        ]

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

        # Resolve any new llm factories

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
        llm: BaseLanguageModel = None

        found_exception: Exception = None

        # Loop through the loaded factories in order until we can find one
        # that can create the llm.
        for llm_factory in self.llm_factories:
            try:
                llm = llm_factory.create_base_chat_model(config, callbacks)
                if llm is not None:
                    found_exception = None
                    break
            except ValueError as exception:
                # Let the next model have a crack
                found_exception = exception

        if found_exception is not None:
            raise found_exception

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
