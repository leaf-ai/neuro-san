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

from enum import Enum

class RegistryUpdateType(Enum):
    """
    Types of agents registry updates.
    """
    CREATE = 1
    MODIFY = 2
    DELETE = 3

