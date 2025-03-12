
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

import copy
import logging
from typing import Any, Dict, List

from tornado.ioloop import IOLoop
from tornado.web import Application

from neuro_san.service.agent_server import DEFAULT_FORWARDED_REQUEST_METADATA

from neuro_san.http_sidecar.handlers.health_check_handler import HealthCheckHandler
from neuro_san.http_sidecar.handlers.connectivity_handler import ConnectivityHandler
from neuro_san.http_sidecar.handlers.function_handler import FunctionHandler
from neuro_san.http_sidecar.handlers.streaming_chat_handler import StreamingChatHandler
from neuro_san.http_sidecar.handlers.concierge_handler import ConciergeHandler


class HttpSidecar:
    """
    Class provides simple http endpoint for neuro-san API,
    working as a client to neuro-san gRPC service.
    """
    def __init__(self, port: int, http_port: int,
                 agents: Dict[str, Any],
                 forwarded_request_metadata: str = DEFAULT_FORWARDED_REQUEST_METADATA):
        """
        Constructor:
        :param port: port for gRPC neuro-san service;
        :param http_port: port for http neuro-san service;
        :param agents: dictionary of registered agents;
        :param forwarded_request_metadata: A space-delimited list of http metadata request keys
               to forward to logs/other requests
        """
        self.port = port
        self.http_port = http_port
        self.agents = copy.deepcopy(agents)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.forwarded_request_metadata: List[str] = forwarded_request_metadata.split(" ")

    def __call__(self):
        """
        Method to be called by a process running tornado HTTP server
        to actually start serving requests.
        """
        app = self.make_app()
        app.listen(self.http_port)
        self.logger.info("HTTP server is running on port %d", self.http_port)
        self.logger.debug("Serving agents: %s", repr(self.agents.keys()))
        IOLoop.current().start()

    def make_app(self):
        """
        Construct tornado HTTP "application" to run.
        """
        handlers = []
        handlers.append(("/", HealthCheckHandler))
        concierge_data: Dict[str, Any] = \
            {"agent_name": "concierge",
             "port": self.port,
             "forwarded_request_metadata": self.forwarded_request_metadata}
        handlers.append(("/describe", ConciergeHandler, concierge_data))

        for agent_name in self.agents.keys():
            # For each of registered agents, we define 3 request paths -
            # one for each of neuro-san service API methods.
            # For each request http path, we build corresponding request handler
            # and put it in "handlers" list,
            # which is used to construct tornado "application".
            request_data: Dict[str, Any] =\
                {"agent_name": agent_name,
                 "port": self.port,
                 "forwarded_request_metadata": self.forwarded_request_metadata}
            route: str = f"/api/v1/{agent_name}/connectivity"
            handlers.append((route, ConnectivityHandler, request_data))
            self.logger.info("Registering URL path: %s", route)
            route: str = f"/api/v1/{agent_name}/function"
            handlers.append((route, FunctionHandler, request_data))
            self.logger.info("Registering URL path: %s", route)
            route: str = f"/api/v1/{agent_name}/streaming_chat"
            handlers.append((route, StreamingChatHandler, request_data))
            self.logger.info("Registering URL path: %s", route)

        return Application(handlers)
