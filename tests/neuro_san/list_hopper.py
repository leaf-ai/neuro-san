
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
from typing import List

from neuro_san.internals.interfaces.async_hopper import AsyncHopper


class ListHopper(AsyncHopper):
    """
    An AsyncHopper implementation for tests that captures items in a list
    """

    def __init__(self):
        """
        Constructor
        """
        self.items: List[Any] = []

    async def put(self, item: Any):
        """
        :param item: The item to put in the hopper.
        """
        self.items.append(item)

    def get_items(self) -> List[Any]:
        """
        :return: The items in the hopper list
        """
        return self.items
