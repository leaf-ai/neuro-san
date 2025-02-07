
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
from typing import Any, Dict

from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

from neuro_san.http_sidecar.handlers.connectivity_handler import ConnectivityHandler
from neuro_san.http_sidecar.handlers.function_handler import FunctionHandler
from neuro_san.http_sidecar.handlers.streaming_chat_handler import StreamingChatHandler


class HttpSidecar:
    """
    Class provides simple http endpoint for neuro-san API,
    working as a client to neuro-san gRPC service.
    """
    def __init__(self, port: int, agents: Dict[str, Any]):
        """
        Constructor:
        :param port: port for gRPC neuro-san service;
        :param agents: dictionary of registered agents;
        """
        self.port = port
        # Set HTTP service port to be a next one to gRPC service port.
        self.http_port: int = self.port+1
        self.agents = copy.deepcopy(agents)
        self.logger = logging.getLogger(self.__class__.__name__)

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
        for agent_name in self.agents.keys():
            # For each of registered agents, we define 3 request paths -
            # one for each of neuro-san service API methods.
            # For each request http path, we build corresponding request handler
            # and put it in "handlers" list,
            # which is used to construct tornado "application".
            route: str = f"/api/v1/{agent_name}/connectivity"
            handler_class = ConnectivityHandler().build(self.port, agent_name, "connectivity")
            handlers.append((route, handler_class,))
            self.logger.debug("Registering: %s", route)
            route: str = f"/api/v1/{agent_name}/function"
            handler_class = FunctionHandler().build(self.port, agent_name, "function")
            handlers.append((route, handler_class,))
            self.logger.debug("Registering: %s", route)
            route: str = f"/api/v1/{agent_name}/streaming_chat"
            handler_class = StreamingChatHandler().build(self.port, agent_name, "streaming_chat")
            handlers.append((route, handler_class,))
            self.logger.debug("Registering: %s", route)

        return Application(handlers)
