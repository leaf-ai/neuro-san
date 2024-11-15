
# Copyright (C) 2019-2023 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
#
# This software is a trade secret, and contains proprietary and confidential
# materials of Cognizant Digital Business Evolutionary AI.
# Cognizant Digital Business prohibits the use, transmission, copying,
# distribution, or modification of this software outside of the
# Cognizant Digital Business EAI organization.
#
# END COPYRIGHT

from typing import Dict

import logging
import os

from leaf_server_common.logging.logging_setup import setup_logging
from leaf_server_common.server.server_lifetime import ServerLifetime
from leaf_server_common.server.server_loop_callbacks import ServerLoopCallbacks

from neuro_sanenerated import agent_pb2

from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.service.agent_servicer_to_server import AgentServicerToServer
from neuro_san.service.agent_service import AgentService
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.asyncio_executor import AsyncioExecutor


SERVER_NAME = 'neuro-san.Agent'
SERVER_NAME_FOR_LOGS = 'Agent Server'

# Better that we kill ourselves than kubernetes doing it for us
# in the middle of a request if there are resource leaks.
# This is per the lifetime of the server (before it kills itself).
REQUEST_LIMIT = 1000 * 1000


# pylint: disable=too-few-public-methods
class AgentServer:
    """
    Server implementation for the Agent gRPC Service.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, port: int,
                 server_loop_callbacks: ServerLoopCallbacks,
                 chat_session_map: ChatSessionMap,
                 tool_registries: Dict[str, AgentToolRegistry],
                 asyncio_executor: AsyncioExecutor):
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
        """
        self.port = port
        self.server_loop_callbacks = server_loop_callbacks
        current_dir = os.path.dirname(os.path.abspath(__file__))

        setup_logging(SERVER_NAME_FOR_LOGS, current_dir,
                      'DECISION_ASSISTANT_SERVICE_LOG_JSON',
                      'DECISION_ASSISTANT_SERVICE_LOG_LEVEL')
        # This module within openai library can be quite chatty w/rt http requests
        logging.getLogger("httpx").setLevel(logging.WARNING)

        self.logger = logging.getLogger(__name__)

        self.chat_session_map: ChatSessionMap = chat_session_map
        self.tool_registries: Dict[str, AgentToolRegistry] = tool_registries
        self.asyncio_executor: AsyncioExecutor = asyncio_executor

    def serve(self):
        """
        Start serving gRPC requests
        """
        values = agent_pb2.DESCRIPTOR.services_by_name.values()
        server_lifetime = ServerLifetime(SERVER_NAME,
                                         SERVER_NAME_FOR_LOGS,
                                         self.port, self.logger,
                                         request_limit=REQUEST_LIMIT,
                                         # Used for health checking. Probably needs agent-specific love.
                                         protocol_services_by_name_values=values,
                                         loop_sleep_seconds=5,
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
            servicer_to_server = AgentServicerToServer(service, agent_name=agent_name)
            servicer_to_server.add_rpc_handlers(server)

        server_lifetime.run()
