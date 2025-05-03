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
import threading
from pathlib import Path

from neuro_san.internals.tool_factories.service_tool_factory_provider import ServiceToolFactoryProvider
from neuro_san.registries_watcher.periodic_updater.registry_observer import RegistryObserver
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer


class ManifestPeriodicUpdater:

    def __init__(self, manifest_path: str, update_period: int):
        """
        Constructor.
        :param manifest_path: file path to server manifest file
        :param update_period: update period in seconds
        """
        self.manifest_path: str = manifest_path
        self.update_period: int = update_period
        self.logger = logging.getLogger(self.__class__.__name__)
        self.updater = threading.Thread(target=self._run, daemon=True)
        self.observer: RegistryObserver = RegistryObserver(self.manifest_path)
        self.tool_factory: ServiceToolFactoryProvider = \
            ServiceToolFactoryProvider.get_instance()
        self.go_run: bool = True

    def _run(self):
        """
        Function runs manifest file update cycle.
        """
        if self.update_period <= 0:
            # We should not run at all.
            return
        while self.go_run:
            time.sleep(self.update_period)
            # Check events that may have been triggered in target registry:
            modified, added, deleted = self.observer.reset_event_counters()
            if modified == added == deleted == 0:
                # Nothing happened - go on observing
                continue
            # Some events were triggered - reload manifest file
            self.logger.info("Observed events: modified %d, added %d, deleted %d",
                             modified, added, deleted)
            self.logger.info("Updating manifest file: %s", self.manifest_path)
            registries: Dict[str, AgentToolRegistry] = \
                RegistryManifestRestorer().restore(src_path)
            self.tool_factory.setup_tool_registries(registries)

    def start(self):
        self.logger.info("Starting manifest updater for %s", self.manifest_path)
        self.observer.start()
        self.updater.start()
