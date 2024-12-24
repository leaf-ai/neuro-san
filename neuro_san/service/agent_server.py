
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from typing import Dict

import logging
import os

from leaf_server_common.asyncio.asyncio_executor import AsyncioExecutor
from leaf_server_common.logging.logging_setup import setup_logging
from leaf_server_common.server.server_lifetime import ServerLifetime
from leaf_server_common.server.server_loop_callbacks import ServerLoopCallbacks

from neuro_san.api.grpc import agent_pb2

from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.service.agent_servicer_to_server import AgentServicerToServer
from neuro_san.service.agent_service import AgentService
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.utils.file_of_class import FileOfClass

DEFAULT_SERVER_NAME: str = 'neuro-san.Agent'
DEFAULT_SERVER_NAME_FOR_LOGS: str = 'Agent Server'

# Better that we kill ourselves than kubernetes doing it for us
# in the middle of a request if there are resource leaks.
# This is per the lifetime of the server (before it kills itself).
DEFAULT_REQUEST_LIMIT: int = 1000 * 1000


# pylint: disable=too-few-public-methods,too-many-instance-attributes
class AgentServer:
    """
    Server implementation for the Agent gRPC Service.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, port: int,
                 server_loop_callbacks: ServerLoopCallbacks,
                 chat_session_map: ChatSessionMap,
                 tool_registries: Dict[str, AgentToolRegistry],
                 asyncio_executor: AsyncioExecutor,
                 server_name: str = DEFAULT_SERVER_NAME,
                 server_name_for_logs: str = DEFAULT_SERVER_NAME_FOR_LOGS,
                 request_limit: int = DEFAULT_REQUEST_LIMIT,
                 service_prefix: str = None):
        """
        Constructor

        :param port: The integer port number for the service to listen on
        :param server_loop_callbacks: The ServerLoopCallbacks instance for
                break out methods in main serving loop.
        :param chat_session_map: The ChatSessionMap containing the global
                        map of session_id string to Agent
        :param tool_registries: A dictionary of agent name to AgentToolRegistry to use for the session.
        :param asyncio_executor: The global AsyncioExecutor for running
                        stuff in the background.
        :param server_name: The name of the service
        :param server_name_for_logs: The name of the service for log files
        :param request_limit: The number of requests to service before shutting down.
                        This is useful to be sure production environments can handle
                        a service occasionally going down.
        :param service_prefix: A prefix for grpc routing.
        """
        self.port = port
        self.server_loop_callbacks = server_loop_callbacks
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Make for easy running from the neuro-san repo
        if os.environ.get("AGENT_SERVICE_LOG_JSON") is None:
            # Use the log file that is local to the repo
            file_of_class = FileOfClass(__file__, path_to_basis="../deploy")
            os.environ["AGENT_SERVICE_LOG_JSON"] = file_of_class.get_file_in_basis("logging.json")

        setup_logging(server_name_for_logs, current_dir,
                      'AGENT_SERVICE_LOG_JSON',
                      'AGENT_SERVICE_LOG_LEVEL')
        # This module within openai library can be quite chatty w/rt http requests
        logging.getLogger("httpx").setLevel(logging.WARNING)

        self.logger = logging.getLogger(__name__)

        self.chat_session_map: ChatSessionMap = chat_session_map
        self.tool_registries: Dict[str, AgentToolRegistry] = tool_registries
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.server_name: str = server_name
        self.server_name_for_logs: str = server_name_for_logs
        self.request_limit: int = request_limit
        self.service_prefix: str = service_prefix

    def serve(self):
        """
        Start serving gRPC requests
        """
        values = agent_pb2.DESCRIPTOR.services_by_name.values()
        server_lifetime = ServerLifetime(self.server_name,
                                         self.server_name_for_logs,
                                         self.port, self.logger,
                                         request_limit=self.request_limit,
                                         # Used for health checking. Probably needs agent-specific love.
                                         protocol_services_by_name_values=values,
                                         loop_sleep_seconds=0.5,
                                         server_loop_callbacks=self.server_loop_callbacks)

        server = server_lifetime.create_server()

        # New-style service
        security_cfg = None     # ... yet

        for agent_name, tool_registry in self.tool_registries.items():

            service = AgentService(server_lifetime, security_cfg,
                                   self.chat_session_map,
                                   self.asyncio_executor,
                                   agent_name,
                                   tool_registry)
            servicer_to_server = AgentServicerToServer(service, agent_name=agent_name,
                                                       service_prefix=self.service_prefix)
            servicer_to_server.add_rpc_handlers(server)

        server_lifetime.run()
