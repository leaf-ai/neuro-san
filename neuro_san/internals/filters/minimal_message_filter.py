
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
from typing import List

from neuro_san.internals.filters.chat_context_message_filter import ChatContextMessageFilter
from neuro_san.internals.filters.compound_message_filter import CompoundMessageFilter
from neuro_san.internals.filters.message_filter import MessageFilter


class MinimalMessageFilter(CompoundMessageFilter):
    """
    A CompoundMessageFilter that lets the minimal messages needed for an agent interaction
    go through.
    """

    def __init__(self):
        """
        Constructor
        """
        filters: List[MessageFilter] = [
            ChatContextMessageFilter(),
        ]
        super().__init__(filters)
