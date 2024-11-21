
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

from typing import Any
from typing import Dict

import json

import grpc

from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

from leaf_server_common.server.grpc_metadata_forwarder import GrpcMetadataForwarder
from leaf_server_common.server.request_logger import RequestLogger

from neuro_san.grpc.generated import agent_pb2 as service_messages
from neuro_san.grpc.generated import agent_pb2_grpc

from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.asyncio_executor import AsyncioExecutor
from neuro_san.session.direct_agent_session import DirectAgentSession

# A list of methods to not log requests for
# Some of these can be way to chatty
DO_NOT_LOG_REQUESTS = [
    "Logs"
]


class AgentService(agent_pb2_grpc.AgentServiceServicer):
    """
    A gRPC implementation of the Decision Assistant Service.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 request_logger: RequestLogger,
                 security_cfg: Dict[str, Any],
                 chat_session_map: ChatSessionMap,
                 asyncio_executor: AsyncioExecutor,
                 agent_name: str,
                 tool_registry: AgentToolRegistry):
        """
        Set the gRPC interface up for health checking so that the service
        will be opened to callers when the mesh sees it operational, if this
        is not done the mesh will treat the service instance as non functional

        :param request_logger: The instance of the RequestLogger that helps
                    keep track of stats
        :param security_cfg: A dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  If None, uses insecure channel.
        :param chat_session_map: The ChatSessionMap containing the global
                        map of session_id string to Agent
        :param asyncio_executor: The global AsyncioExecutor for running
                        stuff in the background.
        :param agent_name: The agent name for the service
        :param tool_registry: The AgentToolRegistry to use for the service.
        """
        self.request_logger = request_logger
        self.security_cfg = security_cfg

        forward_list = ["request_id", "user_id", "url", "group_id"]
        self.forwarder = GrpcMetadataForwarder(forward_list)

        self.chat_session_map: ChatSessionMap = chat_session_map
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.tool_registry: AgentToolRegistry = tool_registry
        self.agent_name: str = agent_name

    # pylint: disable=no-member
    def Function(self, request: service_messages.FunctionRequest,
                 context: grpc.ServicerContext) \
            -> service_messages.FunctionResponse:
        """
        Allows a client to get the outward-facing function for the agent
        served by this service.

        :param request: a FunctionRequest
        :param context: a grpc.ServicerContext
        :return: a FunctionResponse
        """
        request_log = None
        log_marker: str = "function request"
        if "Function" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Function",
                                                            log_marker, context)

        # Get the metadata to forward on to another service
        metadata = self.forwarder.forward(context)

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     asyncio_executor=self.asyncio_executor,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.function(request_dict)

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.FunctionResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Function", log_marker, request_log)

        return response

    # pylint: disable=no-member
    def Chat(self, request: service_messages.ChatRequest,
             context: grpc.ServicerContext) \
            -> service_messages.ChatResponse:
        """
        Initiates or continues the agent chat with the session_id
        context in the request.

        :param request: a ChatRequest
        :param context: a grpc.ServicerContext
        :return: a ChatResponse which indicates that the request
                 was successful
        """
        request_log = None
        log_marker = f"'{request.user_input}' on assistant {request.session_id}"
        if "Chat" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Chat",
                                                            log_marker, context)

        # Get the metadata to forward on to another service
        metadata = self.forwarder.forward(context)

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     asyncio_executor=self.asyncio_executor,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.chat(request_dict)
        response_dict["request"] = request_dict

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.ChatResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Chat", log_marker, request_log)

        return response

    # pylint: disable=no-member
    def Logs(self, request: service_messages.LogsRequest,
             context: grpc.ServicerContext) \
            -> service_messages.LogsResponse:
        """
        Polls for the asynchronous results of Chat() above.
        Results include the most recent chat response and the "Thought Process" logs.

        :param request: a LogsRequest
        :param context: a grpc.ServicerContext
        :return: a LogsResponse which indicates that the request
                 was successful
        """
        request_log = None
        log_marker = f"Polling for logs on assistant {request.session_id}"
        if "Logs" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Logs",
                                                            log_marker, context)

        # Get the metadata to forward on to another service
        metadata = self.forwarder.forward(context)

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     asyncio_executor=self.asyncio_executor,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.logs(request_dict)
        response_dict["request"] = request_dict

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.LogsResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Logs", log_marker, request_log)

        return response

    # pylint: disable=no-member
    def Reset(self, request: service_messages.ResetRequest,
              context: grpc.ServicerContext) \
            -> service_messages.ResetResponse:
        """
        Resets the chat history of an existing assistant.

        :param request: a ResetRequest
        :param context: a grpc.ServicerContext
        :return: a ResetResponse which indicates that the request
                 was successful
        """
        request_log = None
        log_marker = f"Reset assistant {request.session_id}"
        if "Reset" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Reset",
                                                            log_marker, context)

        # Get the metadata to forward on to another service
        metadata = self.forwarder.forward(context)

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     asyncio_executor=self.asyncio_executor,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.reset(request_dict)
        response_dict["request"] = request_dict

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.ResetResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Reset", log_marker, request_log)

        return response
