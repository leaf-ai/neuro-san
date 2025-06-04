
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
from tornado.web import Application

from neuro_san.interfaces.event_loop_logger import EventLoopLogger


class HttpServerApp(Application):
    """
    Class provides customized Tornado application for neuro-san service -
    with redefined internal logger so we can include custom request metadata.
    """
    def __init__(self, handlers, requests_limit: int, logger: EventLoopLogger):
        """
        Constructor:
        :param handlers: list of request handlers
        """
        # Call the base constructor
        super().__init__(handlers=handlers)
        self.total: int = 0
        self.num_processing: int = 0
        self.requests_stats: Dict[str, int] = {}
        self.requests_limit: int = requests_limit
        self.logger: EventLoopLogger = logger
        self.serving: bool = True
        self.shutdown_initiated: bool = False

    def is_serving(self) -> bool:
        print(">>>>>>>>>>>>> CHECK SERVING.")
        return self.serving

    def start_client_request(self, caller: str):
        pass

    def finish_client_request(self, metadata: Dict[str, Any], caller: str):
        pass

    def get_stats(self) -> str:
        return ""

    def log_request(self, handler):
        request = handler.request
        metadata: Dict[str, Any] = handler.get_metadata()
        status = handler.get_status()
        duration = 1000 * request.request_time()  # in milliseconds
        # handler.logger is our custom HttpLogger
        handler.logger.info(metadata, "%d %s %s (%s) %.2fms",
                            status, request.method, request.uri, request.remote_ip, duration)
