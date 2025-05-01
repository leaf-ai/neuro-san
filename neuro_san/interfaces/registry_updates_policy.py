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

from typing import Set
from neuro_san.interfaces.registry_update_type import RegistryUpdateType

class RegistryUpdatePolicy:
    """
    Abstract policy interface for modifying agents registry definitions.
    """

    def get_allowed_modes(self, src_path: str) -> Set[RegistryUpdateType]:
        """
        Get allowed update modes for agent or manifest definition files.
        :param src_path: file path for agent or manifest definition being updated;
        :return: set of allowed modification modes.
            Could be empty, in which case no updates are allowed for this file.
        """
        raise NotImplementedError