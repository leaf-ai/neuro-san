
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
from typing import Generator
import json
import requests


from leaf_common.time.timeout import Timeout

from neuro_san.interfaces.agent_session import AgentSession


class HttpServiceAgentSession(AgentSession):
    """
    Implementation of AgentSession that talks to an HTTP service.
    This is largely only used by command-line tests.
    """

    DEFAULT_AGENT_NAME: str = "esp_decision_assistant"

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, host: str = None,
                 port: str = None,
                 timeout_in_seconds: int = 30,
                 metadata: Dict[str, str] = None,
                 security_cfg: Dict[str, Any] = None,
                 umbrella_timeout: Timeout = None,
                 streaming_timeout_in_seconds: int = None,
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
        :param streaming_timeout_in_seconds: timeout to use when streaming to/from
                        the service. Default is None, indicating connection should
                        stay open until the (last) result is yielded.
        :param agent_name: The name of the agent to talk to
        :param service_prefix: The service prefix to use. Default is None,
                        implying the policy in AgentServiceStub takes over.
        """
        _ = security_cfg
        _ = umbrella_timeout
        _ = streaming_timeout_in_seconds

        self.service_prefix: str = service_prefix
        self.use_host: str = "localhost"
        if host is not None:
            self.use_host = host

        self.use_port: str = str(self.DEFAULT_HTTP_PORT)
        if port is not None:
            self.use_port = port

        self.agent_name: str = agent_name
        self.timeout_in_seconds = timeout_in_seconds
        self.metadata: Dict[str, str] = metadata

    def _get_request_path(self, function: str):
        if self.service_prefix is None or len(self.service_prefix) == 0:
            return f"http://{self.use_host}:{self.use_port}/api/v1/{self.agent_name}/{function}"
        return f"http://{self.use_host}:{self.use_port}/api/v1/{self.service_prefix}.{self.agent_name}/{function}"

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
        path: str = self._get_request_path("function")
        response = requests.get(path, json=request_dict, headers=self.metadata,
                                timeout=self.timeout_in_seconds)
        result_dict = json.loads(response.text)
        return result_dict

    def connectivity(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ConnectivityRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the ConnectivityResponse
                    protobufs structure. Has the following keys:
                "connectivity_info" - the list of connectivity descriptions for
                                    each node in the agent network the service
                                    wants the client ot know about.
                "status" - status for finding the function.
        """
        path: str = self._get_request_path("connectivity")
        response = requests.get(path, json=request_dict, headers=self.metadata,
                                timeout=self.timeout_in_seconds)
        result_dict = json.loads(response.text)
        return result_dict

    def chat(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def logs(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def reset(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def streaming_chat(self, request_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              Upon first contact this can be blank.
            "user_input"    - A string representing the user input to the chat stream

        :return: An iterator of dictionary versions of the ChatResponse
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
            "response"      - An optional ChatMessage dictionary.  See chat.proto for details.

            Note that responses to the chat input might be numerous and will come as they
            are produced until the system decides there are no more messages to be sent.
        """
        path: str = self._get_request_path("streaming_chat")
        with requests.post(path, json=request_dict, headers=self.metadata,
                           stream=True,
                           timeout=self.timeout_in_seconds) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line.strip():  # Skip empty lines
                    # print(f"============ RECEIVED: |{line}|")
                    result_dict = json.loads(line)
                    yield result_dict
