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

from pathlib import Path
from watchdog.events import FileSystemEventHandler

from neuro_san.internals.tool_factories.service_tool_factory_provider import ServiceToolFactoryProvider
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer

class RegistryChangeHandler(FileSystemEventHandler):

    def __init__(self,
                 registry_path: str,
                 watch_manifest: bool,
                 allow_update: bool,
                 allow_create: bool,
                 allow_delete: bool):
        self.registry_path: str = registry_path
        self.watch_manifest: bool = watch_manifest
        self.allow_update: bool = allow_update
        self.allow_create: bool = allow_create
        self.allow_delete: bool = allow_delete
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
        try:
            if self.is_manifest(src_path):
                if self.watch_manifest:
                    pass
                return
            if not self.allow_update:
                return
            agent_name: str = self.get_agent_name(src_path)
            self.logger.info("🔔 File updated: %s for agent: %s", src_path, agent_name)
            registry = AgentToolRegistryRestorer().restore(src_path)
            self.tool_factory.add_agent_tool_registry(agent_name, registry)
            self.logger.info("🔔 Updated registry for agent: %s", agent_name)
        except Exception as exc:
            pass

    def on_created(self, event):
        src_path: str = event.src_path
        if not self.filter_src_name(src_path):
            return
        if self.is_manifest(src_path):
            # We don't handle creating the manifest file:
            return
        if not self.allow_create:
            return
        try:
            self.logger.info("🔔 File created: %s", src_path)
            agent_name: str = self.get_agent_name(src_path)
            registry = AgentToolRegistryRestorer().restore(src_path)
            self.tool_factory.add_agent_tool_registry(agent_name, registry)
            self.logger.info("🔔 Created registry for agent: %s", agent_name)
        except Exception as exc:
            pass

    def on_deleted(self, event):
        src_path: str = event.src_path
        if not self.filter_src_name(src_path):
            return
        if self.is_manifest(src_path):
            # We don't handle deleting the manifest file:
            return
        if not self.allow_delete:
            return
        try:
            self.logger.info("🔔 File deleted: %s", src_path)
            agent_name: str = self.get_agent_name(src_path)
            self.tool_factory.remove_agent_tool_registry(agent_name)
            self.logger.info("🔔 Removed registry for agent: %s", agent_name)
        except Exception as exc:
            pass

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
        return src_name == "manifest.hocon" or src_name == "manifest.json"

    def get_agent_name(self, src_name: str):
        """
        Get agent name from file path
        """
        return Path(src_name).stem



