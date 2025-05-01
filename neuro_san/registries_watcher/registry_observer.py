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
from watchdog.observers import Observer

from neuro_san.registries_watcher.registrie_change_handler import RegistrieChangeHandler


class RegistryObserver:

    def __init__(self, registry_path: str):
        self.registry_path: str = str(Path(registry_path).resolve())
        self.observer: Observer = Observer()
        self.event_handler: RegistriesChangeHandler = RegistriesChangeHandler(self.registry_path)

    def start(self):
        self.observer.schedule(self.event_handler, path=self.registry_path, recursive=False)
        self.observer.start()
        print("~~~~~~~~~~~~~~~~~~ Observer STARTED!")

