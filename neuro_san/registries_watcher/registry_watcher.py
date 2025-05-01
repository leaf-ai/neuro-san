
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

class RegistryWatcher:

    def __init__(self,
                 registry_path: str,
                 watch_manifest: bool = False,
                 allow_update: bool = False,
                 allow_create: bool = False,
                 allow_delete: bool = False):
        self.watch_manifest: bool = watch_manifest
        self.allow_update: bool = allow_update
        self.allow_create: bool = allow_create
        self.allow_delete: bool = allow_delete
        self.logger = logging.getLogger(self.__class__.__name__)

        self.registry_path = Path(registry_path).resolve()
        if not self.registry_path.is_dir():
            err_msg: str = f"{str(self.registry_path)} doesn't exist or not a directory."
            self.logger.error(err_msg)
            raise ValueError(err_msg)




