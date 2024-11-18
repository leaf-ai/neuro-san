
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

from os import path
from pathlib import Path

import json

from leaf_common.config.config_filter_chain import ConfigFilterChain
from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.interface.restorer import Restorer

from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.graph.registry.defaults_config_filter import DefaultsConfigFilter
from neuro_san.graph.registry.dictionary_common_defs_config_filter \
    import DictionaryCommonDefsConfigFilter
from neuro_san.graph.registry.name_correction_config_filter import NameCorrectionConfigFilter
from neuro_san.graph.registry.string_common_defs_config_filter \
    import StringCommonDefsConfigFilter


# pylint: disable=too-few-public-methods
class AgentToolRegistryRestorer(Restorer):
    """
    Implementation of the Restorer interface to read in an AgentToolRegistry
    instance given a JSON file name.
    """

    def __init__(self, registry_dir: str = None):
        """
        Constructor

        :param registry_dir: The directory under which file_references
                    for registry files are allowed to be found.
                    If None, there are no limits, but paths must be absolute
        """
        self.registry_dir: str = registry_dir

    def restore(self, file_reference: str = None):
        """
        :param file_reference: The file reference to use when restoring.
                Default is None, implying the file reference is up to the
                implementation.
        :return: an object from some persisted store
        """
        config: Dict[str, Any] = None

        if file_reference is None or len(file_reference) == 0:
            raise ValueError(f"file_reference {file_reference} cannot be None or empty string")

        if file_reference.startswith("/") and self.registry_dir is not None:
            raise ValueError(f"file_reference {file_reference} cannot be an absolute path")

        use_file: str = file_reference
        if self.registry_dir is not None:
            use_file = path.join(self.registry_dir, file_reference)

        if use_file.endswith(".json"):
            config = json.load(use_file)
        elif use_file.endswith(".hocon"):
            hocon = EasyHoconPersistence(full_ref=use_file, must_exist=True)
            config = hocon.restore()
        else:
            raise ValueError(f"file_reference {use_file} must be a .json or .hocon file")

        # Perform a filter chain on the config that was read in
        filter_chain = ConfigFilterChain()
        filter_chain.register(DictionaryCommonDefsConfigFilter())
        filter_chain.register(StringCommonDefsConfigFilter())
        filter_chain.register(DefaultsConfigFilter())
        filter_chain.register(NameCorrectionConfigFilter())
        config = filter_chain.filter_config(config)

        # Now create the AgentToolRegistry
        name = Path(use_file).stem
        tool_registry = AgentToolRegistry(config, name)

        return tool_registry
