from typing import Any
from typing import Dict
from typing import List
from typing import Union

import json
import logging

from pathlib import Path

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.interface.restorer import Restorer

from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.graph.registry.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.utils.file_of_class import FileOfClass


# pylint: disable=too-few-public-methods
class RegistryManifestRestorer(Restorer):
    """
    This interface provides a way to retrieve an object
    from some storage like a file, a database or S3.
    """

    def __init__(self, manifest_files: Union[str, List[str]] = None):
        """
        Constructor

        :param manifest_files: Either:
            * A single local name for the manifest file listing the agents to host.
            * A list of local names for multiple manifest files to host
            * None (the default) which gets a single manifest file from a known source.
        """
        self.manifest_files: List[str] = []
        if manifest_files is None:
            file_of_class = FileOfClass(__file__, path_to_basis="../registries")
            self.manifest_files.append(file_of_class.get_file_in_basis("manifest.hocon"))
        elif isinstance(manifest_files, str):
            self.manifest_files.append(manifest_files)
        else:
            self.manifest_files = manifest_files

        self.logger = logging.getLogger(self.__class__.__name__)

    def restore(self, file_reference: str = None):
        """
        :param file_reference: The file reference to use when restoring.
                Default is None, implying the file reference is up to the
                implementation.
        :return: an object from some persisted store
        """

        tool_registries: Dict[str, AgentToolRegistry] = {}

        # Loop through all the manifest files in the list to make a composite
        for manifest_file in self.manifest_files:

            one_manifest: Dict[str, Any] = {}
            if manifest_file.endswith(".hocon"):
                hocon = EasyHoconPersistence()
                one_manifest = hocon.restore(file_reference=manifest_file)
            else:
                with open(manifest_file, "r", encoding="utf-8") as json_file:
                    one_manifest = json.load(json_file)

            for key, value in one_manifest.items():

                # Keys sometimes come with quotes.
                use_key: str = key.replace(r'"', "")

                if not bool(value):
                    continue

                file_of_class = FileOfClass(manifest_file)
                manifest_dir: str = file_of_class.get_basis()
                registry_restorer = AgentToolRegistryRestorer(manifest_dir)
                tool_registry: AgentToolRegistry = registry_restorer.restore(file_reference=use_key)
                if tool_registry is not None:
                    tool_name: str = Path(use_key).stem
                    tool_registries[tool_name] = tool_registry
                else:
                    self.logger.error("manifest registry %s not found in %s", use_key, manifest_file)

        return tool_registries
