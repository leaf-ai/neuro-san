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

import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler

from neuro_san.interfaces.registry_update_type import RegistryUpdateType
from neuro_san.interfaces.registry_updates_policy import RegistryUpdatePolicy
from neuro_san.internals.tool_factories.service_tool_factory_provider import ServiceToolFactoryProvider
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer

class RegistryChangeHandler(FileSystemEventHandler):
    """
    Class for handling watchdog events in server registry directory.
    """
    def __init__(self,
                 registry_path: str,
                 policy: RegistryUpdatePolicy):
        """
        Constructor.
        :param registry_path: file path to local directory containing registry manifest
            and agents definitions;
        :param policy: externally provided updates policy for registry elements.
        """
        self.registry_path: str = registry_path
        self.policy: RegistryUpdatePolicy = policy
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tool_factory: ServiceToolFactoryProvider =\
            ServiceToolFactoryProvider.get_instance()

    def on_modified(self, event):
        """
        Handler for modified registry files.
        """
        src_path: str = event.src_path
        if not self.filter_src_name(src_path):
            return
        allowed: Set[RegistryUpdateType] =\
            self.policy.get_allowed_modes(src_path)
        if RegistryUpdateType.MODIFY not in allowed:
            return
        try:
            if self.is_manifest(src_path):
                self.logger.info("Updating manifest file: %s", src_path)
                registries: Dict[str, AgentToolRegistry] =\
                    RegistryManifestRestorer().restore(src_path)
                self.tool_factory.setup_tool_registries(registries)
                return

            agent_name: str = self.get_agent_name(src_path)
            self.logger.info("🔔 File updated: %s for agent: %s", src_path, agent_name)
            registry = AgentToolRegistryRestorer().restore(src_path)
            self.tool_factory.add_agent_tool_registry(agent_name, registry)
            self.logger.info("🔔 Updated registry for agent: %s", agent_name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.error("FAILED to update registry for %s/%s - %s",
                              self.registry_path, src_path, exc)

    def on_created(self, event):
        src_path: str = event.src_path
        if not self.filter_src_name(src_path):
            return
        allowed: Set[RegistryUpdateType] =\
            self.policy.get_allowed_modes(src_path)
        if RegistryUpdateType.CREATE not in allowed:
            return
        try:
            self.logger.info("🔔 File created: %s", src_path)
            agent_name: str = self.get_agent_name(src_path)
            registry = AgentToolRegistryRestorer().restore(src_path)
            self.tool_factory.add_agent_tool_registry(agent_name, registry)
            self.logger.info("🔔 Created registry for agent: %s", agent_name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.error("FAILED to create registry for %s/%s - %s",
                              self.registry_path, src_path, exc)

    def on_deleted(self, event):
        src_path: str = event.src_path
        if not self.filter_src_name(src_path):
            return
        allowed: Set[RegistryUpdateType] =\
            self.policy.get_allowed_modes(src_path)
        if RegistryUpdateType.DELETE not in allowed:
            return
        try:
            self.logger.info("🔔 File deleted: %s", src_path)
            agent_name: str = self.get_agent_name(src_path)
            self.tool_factory.remove_agent_tool_registry(agent_name)
            self.logger.info("🔔 Removed registry for agent: %s", agent_name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.error("FAILED to delete registry for %s/%s - %s",
                              self.registry_path, src_path, exc)

    def filter_src_name(self, src_name: str) -> bool:
        """
        Filter source names we are getting notifications for.
        :param src_name: file path we get notified about
        :return: True if we should consider this file path;
                 False otherwise.
        """
        if not src_name:
            return False
        if src_name.endswith(".hocon") or src_name.endswith(".json"):
            return True
        return False

    def is_manifest(self, src_name: str) -> bool:
        """
        Is this a file path of registry manifest?
        """
        return Path(src_name).stem == "manifest"

    def get_agent_name(self, src_name: str):
        """
        Get agent name from file path
        """
        return Path(src_name).stem



