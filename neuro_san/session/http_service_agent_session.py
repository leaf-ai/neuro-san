
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
                 agent_name: str = DEFAULT_AGENT_NAME):
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
        """
        _ = umbrella_timeout
        _ = streaming_timeout_in_seconds

        self.security_cfg: Dict[str, Any] = security_cfg
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
        scheme: str = "http"
        if self.security_cfg is not None:
            scheme = "https"

        return f"{scheme}://{self.use_host}:{self.use_port}/api/v1/{self.agent_name}/{function}"

    def _get_headers(self) -> Dict[str, Any]:
        """
        Get headers for any outgoing request
        """
        headers: Dict[str, Any] = self.metadata
        if headers is None:
            headers = {}
        return headers

    def help_message(self, path: str) -> str:
        """
        Method returning general help message for http connectivity problems.
        :param path: url path of a request
        :return: help message
        """
        message = f"""
        Some basic suggestions to help debug connectivity issues:
        1. Ensure the server is running and reachable:
           ping <server_address>
           curl -v <server_url>
        2. Check network issues:
           traceroute <server_address>  # Linux/macOS
           tracert <server_address>  # Windows
        3. Ensure you are using correct protocol (http/https) and port number;
        4. Run service health check:
           curl <server_url:server_port>
        5. Try testing with increased timeout;
        6. Did you misspell the agent and/or method name in your {path} request path?
        7. If working with a local docker container:
           7.1 Does your http port EXPOSEd in the Dockerfile match your value for AGENT_HTTP_PORT?
           7.2 Did you add a -p <server_port>:<server_port> to your docker run command line to map container port(s)
               to your local ones?
        8. Is the agent turned on in your manifest.hocon?
        9. If you are attempting to use https, know that the default server configurations do not
           provide any of the necessary certificates for this to work and any certs used will
           need to be well known.  If you're unfamiliar with this process, it's a big deal.
           Try regular http instead.
        """
        return message

    def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
        """
        path: str = self._get_request_path("function")
        try:
            response = requests.get(path, json=request_dict, headers=self._get_headers(),
                                    timeout=self.timeout_in_seconds)
            result_dict = json.loads(response.text)
            return result_dict
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError(self.help_message(path)) from exc

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
        """
        path: str = self._get_request_path("connectivity")
        try:
            response = requests.get(path, json=request_dict, headers=self._get_headers(),
                                    timeout=self.timeout_in_seconds)
            result_dict = json.loads(response.text)
            return result_dict
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError(self.help_message(path)) from exc

    def streaming_chat(self, request_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "user_message" - A ChatMessage dict representing the user input to the chat stream
            "chat_context" - A ChatContext dict representing the state of the previous conversation
                            (if any)
        :return: An iterator of dictionary versions of the ChatResponse
                    protobufs structure. Has the following keys:
            "response"      - An optional ChatMessage dictionary.  See chat.proto for details.

            Note that responses to the chat input might be numerous and will come as they
            are produced until the system decides there are no more messages to be sent.
        """
        path: str = self._get_request_path("streaming_chat")
        try:
            with requests.post(path, json=request_dict, headers=self._get_headers(),
                               stream=True,
                               timeout=self.timeout_in_seconds) as response:
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if line.strip():  # Skip empty lines
                        result_dict = json.loads(line)
                        yield result_dict
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValueError(self.help_message(path)) from exc
