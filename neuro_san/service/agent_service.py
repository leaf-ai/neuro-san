
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
from typing import Dict
from typing import Iterator
from typing import List

import copy
import json
import uuid

import grpc

from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

from leaf_server_common.server.atomic_counter import AtomicCounter
from leaf_server_common.server.grpc_metadata_forwarder import GrpcMetadataForwarder
from leaf_server_common.server.request_logger import RequestLogger

from neuro_san.api.grpc import agent_pb2 as service_messages
from neuro_san.api.grpc import agent_pb2_grpc
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.direct_agent_session import DirectAgentSession
from neuro_san.session.external_agent_session_factory import ExternalAgentSessionFactory
from neuro_san.session.session_invocation_context import SessionInvocationContext

# A list of methods to not log requests for
# Some of these can be way too chatty
DO_NOT_LOG_REQUESTS = [
    "Logs"
]


# pylint: disable=too-many-instance-attributes
class AgentService(agent_pb2_grpc.AgentServiceServicer):
    """
    A gRPC implementation of the Neuro-San Agent Service.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 request_logger: RequestLogger,
                 security_cfg: Dict[str, Any],
                 chat_session_map: ChatSessionMap,
                 agent_name: str,
                 tool_registry: AgentToolRegistry,
                 forwarded_request_metadata: List[str]):
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
        :param agent_name: The agent name for the service
        :param tool_registry: The AgentToolRegistry to use for the service.
        :param forwarded_request_metadata: A list of http metadata request keys
                        to forward to logs/other requests
        """
        self.request_logger = request_logger
        self.security_cfg = security_cfg

        self.forwarder = GrpcMetadataForwarder(forwarded_request_metadata)

        self.chat_session_map: ChatSessionMap = chat_session_map

        # When we get to 1 AsyncioExecutor per request, we should also do a
        # leaf_server_common.logging.logging_setup.setup_extra_logging_fields()
        # for each executor thread.
        self.tool_registry: AgentToolRegistry = tool_registry
        self.agent_name: str = agent_name
        self.request_counter = AtomicCounter()

    def get_request_count(self) -> int:
        """
        :return: The number of currently active requests
        """
        return self.request_counter.get_count()

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
        self.request_counter.increment()
        request_log = None
        log_marker: str = "function request"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"{self.request_logger.get_server_name_for_logs()}-{uuid.uuid4()}"
        }
        if "Function" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Function",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(self.forwarder.forward(context))

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     invocation_context=None,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.function(request_dict)

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.FunctionResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Function", log_marker, request_log)

        self.request_counter.decrement()
        return response

    # pylint: disable=no-member
    def Connectivity(self, request: service_messages.ConnectivityRequest,
                     context: grpc.ServicerContext) \
            -> service_messages.ConnectivityResponse:
        """
        Allows a client to get connectivity information for the agent
        served by this service.

        :param request: a ConnectivityRequest
        :param context: a grpc.ServicerContext
        :return: a ConnectivityResponse
        """
        self.request_counter.increment()
        request_log = None
        log_marker: str = "connectivity request"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"{self.request_logger.get_server_name_for_logs()}-{uuid.uuid4()}"
        }
        if "Connectivity" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.Connectivity",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(self.forwarder.forward(context))

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     invocation_context=None,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict = session.connectivity(request_dict)

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = service_messages.ConnectivityResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request(f"{self.agent_name}.Connectivity", log_marker, request_log)

        self.request_counter.decrement()
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
        self.request_counter.increment()
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
        factory = ExternalAgentSessionFactory(use_direct=False)
        invocation_context = SessionInvocationContext(factory)
        invocation_context.start()
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     invocation_context=invocation_context,
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

        self.request_counter.decrement()
        invocation_context.close()
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
        self.request_counter.increment()
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
                                     invocation_context=None,
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

        self.request_counter.decrement()
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
        self.request_counter.increment()
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
        factory = ExternalAgentSessionFactory(use_direct=False)
        invocation_context = SessionInvocationContext(factory)
        invocation_context.start()
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     invocation_context=invocation_context,
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

        self.request_counter.decrement()
        invocation_context.close()
        return response

    # pylint: disable=no-member,too-many-locals
    def StreamingChat(self, request: service_messages.ChatRequest,
                      context: grpc.ServicerContext) \
            -> Iterator[service_messages.ChatResponse]:
        """
        Initiates or continues the agent chat with the session_id
        context in the request.

        :param request: a ChatRequest
        :param context: a grpc.ServicerContext
        :return: an iterator for (eventually) returned ChatResponses
        """
        self.request_counter.increment()
        request_log = None
        log_marker = f"'{request.user_message.text}'"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"{self.request_logger.get_server_name_for_logs()}-{uuid.uuid4()}"
        }
        if "StreamingChat" not in DO_NOT_LOG_REQUESTS:
            request_log = self.request_logger.start_request(f"{self.agent_name}.StreamingChat",
                                                            log_marker, context,
                                                            service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(self.forwarder.forward(context))

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        factory = ExternalAgentSessionFactory(use_direct=False)
        invocation_context = SessionInvocationContext(factory, metadata)
        invocation_context.start()
        session = DirectAgentSession(chat_session_map=self.chat_session_map,
                                     tool_registry=self.tool_registry,
                                     invocation_context=invocation_context,
                                     metadata=metadata,
                                     security_cfg=self.security_cfg)
        response_dict_iterator: Iterator[Dict[str, Any]] = session.streaming_chat(request_dict)

        for response_dict in response_dict_iterator:
            response_dict["request"] = request_dict

            # Convert the response dictionary to a grpc message
            response_string = json.dumps(response_dict)
            response = service_messages.ChatResponse()
            Parse(response_string, response)

            # Yield-ing a single response allows one response to be returned
            # over the connection while keeping it open to wait for more.
            # Grpc client code handling response streaming knows to construct an
            # iterator on its side to do said waiting over there.
            yield response

        # Iterator has finally signaled that there are no more responses to be had.
        # Log that we are done.
        if request_log is not None:
            request_reporting: Dict[str, Any] = invocation_context.get_request_reporting()
            reporting: str = None
            if request_reporting is not None:
                reporting = json.dumps(request_reporting, indent=4, sort_keys=True)
            request_log.metrics("Request reporting: %s", reporting)
            self.request_logger.finish_request(f"{self.agent_name}.StreamingChat", log_marker, request_log)

        self.request_counter.decrement()
        invocation_context.close()
