
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

from leaf_common.session.abstract_service_session import AbstractServiceSession
from leaf_common.time.timeout import Timeout

from neuro_san.session.agent_service_stub import AgentServiceStub
from neuro_san.session.agent_session import AgentSession
from neuro_san.api.grpc import agent_pb2 as service_messages


class ServiceAgentSession(AbstractServiceSession, AgentSession):
    """
    Implementation of AgentSession that talks to a
    gRPC service.  This is largely only used by command-line tests.
    """

    DEFAULT_AGENT_NAME: str = "esp_decision_assistant"

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, host: str = None,
                 port: str = None,
                 timeout_in_seconds: int = 30,
                 metadata: Dict[str, str] = None,
                 security_cfg: Dict[str, Any] = None,
                 umbrella_timeout: Timeout = None,
                 agent_name: str = DEFAULT_AGENT_NAME,
                 service_prefix: str = None):
        """
        Creates a AgentSession that connects to the
        Agent Service and delegates its implementations to the service.

        :param host: the service host to connect to
                        If None, will use a default
        :param port: the service port
                        If None, will use a default
        :param timeout_in_seconds: timeout to use when communicating
                        with the service
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        :param security_cfg: An optional dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  Default is None, uses insecure channel.
        :param umbrella_timeout: A Timeout object under which the length of all
                        looping and retries should be considered
        :param agent_name: The name of the agent to talk to
        :param service_prefix: The service prefix to use. Default is None,
                        implying the policy in AgentServiceStub takes over.
        """
        use_host: str = "localhost"
        if host is not None:
            use_host = host

        use_port: str = str(self.DEFAULT_PORT)
        if port is not None:
            use_port = port

        # Normally we pass around the service_stub like a class,
        # but AgentServiceStub has a __call__() method to intercept
        # constructor-like behavior.
        service_stub = AgentServiceStub(agent_name, service_prefix)
        AbstractServiceSession.__init__(self, "Agent Server",
                                        service_stub,
                                        use_host, use_port,
                                        timeout_in_seconds, metadata,
                                        security_cfg, umbrella_timeout)

    def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
                "status" - status for finding the function.
        """
        # pylint: disable=no-member
        return self.call_grpc_method(
            "function",
            self._function_from_stub,
            request_dict,
            service_messages.FunctionRequest())

    def chat(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              Upon first contact this can be blank.
            "user_input"    - A string representing the user input to the chat stream

        :return: A dictionary version of the ChatResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              This will always be filled upon response.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          on this service instance and the user_input
                                          has been registered in the chat stream.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - Returned when no session_id was given (initiation
                                          of new chat by client) and a new chat session is created.

            Note that responses to the chat input are asynchronous and come by polling the
            logs() method below.
        """
        # pylint: disable=no-member
        return self.call_grpc_method(
            "chat",
            self._chat_from_stub,
            request_dict,
            service_messages.ChatRequest())

    def logs(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the LogsRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              When calling logs(), this cannot be blank.

        :return: A dictionary version of the LogsResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          on this service instance.
                                          Other keys below will be filled in.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat session.
                              CREATED   - While valid in other situations, this method will
                                          never return this value.
            "chat_response" - A single string representing the most recent chat response.
            "logs"          - A list of strings representing the "thinking" logs thus far.

            Worth noting that this particular method does not need to be asynchronous.
        """
        # pylint: disable=no-member
        return self.call_grpc_method(
            "logs",
            self._logs_from_stub,
            request_dict,
            service_messages.LogsRequest())

    def reset(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ResetRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              When calling reset(), this cannot be blank.
        :return: A dictionary version of the ResetResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          and has been reset. No retry needed.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - While valid in other situations, this method will
                                          never return this value.
        """
        # pylint: disable=no-member
        return self.call_grpc_method(
            "reset",
            self._reset_from_stub,
            request_dict,
            service_messages.ResetRequest())

    @staticmethod
    def _function_from_stub(stub, timeout_in_seconds,
                            metadata, credentials, *args):
        """
        Global method associated with the session that calls Function
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.Function(*args, timeout=timeout_in_seconds,
                                 metadata=metadata,
                                 credentials=credentials)
        return response

    @staticmethod
    def _chat_from_stub(stub, timeout_in_seconds,
                        metadata, credentials, *args):
        """
        Global method associated with the session that calls Chat
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.Chat(*args, timeout=timeout_in_seconds,
                             metadata=metadata,
                             credentials=credentials)
        return response

    @staticmethod
    def _logs_from_stub(stub, timeout_in_seconds,
                        metadata, credentials, *args):
        """
        Global method associated with the session that calls Logs
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.Logs(*args, timeout=timeout_in_seconds,
                             metadata=metadata,
                             credentials=credentials)
        return response

    @staticmethod
    def _reset_from_stub(stub, timeout_in_seconds,
                         metadata, credentials, *args):
        """
        Global method associated with the session that calls Reset
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.Reset(*args, timeout=timeout_in_seconds,
                              metadata=metadata,
                              credentials=credentials)
        return response
