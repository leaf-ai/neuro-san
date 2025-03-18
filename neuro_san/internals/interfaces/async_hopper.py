
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


class AsyncHopper:
    """
    An interface whose clients store things for later use.
    """

    async def put(self, item: Any):
        """
        :param item: The item to put in the hopper.
        """
        raise NotImplementedError
