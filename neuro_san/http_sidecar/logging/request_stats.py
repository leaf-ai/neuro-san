
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
"""
See class comment for details
"""
from typing import Any, Dict

from neuro_san.interfaces.event_loop_logger import EventLoopLogger

class RequestStats:

    def __init__(self, requests_limit: int, logger: EventLoopLogger):
        self.total: int = 0
        self.num_processing: int = 0
        self.requests_stats: Dict[str, int] = {}
        self.requests_limit: int = requests_limit
        self.logger: EventLoopLogger = logger
        self.serving: bool = True
        self.shutdown_initiated: bool = False

    def is_serving(self) -> bool:
        return self.serving

    def start_request(self, caller: str):
        pass

    def finish_request(self, metadata: Dict[str, Any], caller: str):
        pass

    def get_stats(self) -> str:
        return ""
