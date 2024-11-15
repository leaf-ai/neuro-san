
from grpc import Channel
from grpc import UnaryUnaryMultiCallable

import neuro_san.grpc.generated.agent_pb2 as agent__pb2


# This comes from the 'package' definition in the agent.proto
DEFAULT_SERVICE_PREFIX: str = "localhost"


class AgentServiceStub:
    """
    The service comprises all the exchanges to the backend in support of agent services.
    Note that as of 3/21/24, this is *not* a RESTful service due to constraints
    with OpenAI service used behind the scenes.
    """

    def __init__(self, agent_name: str = "",
                 service_prefix: str = DEFAULT_SERVICE_PREFIX):
        """
        Constructor.
        """
        self._agent_name: str = agent_name
        self._service_prefix: str = service_prefix

        # Stub methods. These all happen to be the same kind of method, but
        # note that thare are more defined on grpc.Channel if needed (see the source).
        # pylint: disable=invalid-name
        self.Function: UnaryUnaryMultiCallable = None
        self.Chat: UnaryUnaryMultiCallable = None
        self.Logs: UnaryUnaryMultiCallable = None
        self.Reset: UnaryUnaryMultiCallable = None

    def set_agent_name(self, agent_name: str):
        """
        Exclusively called by ForwardedAgentSession.

        :param agent_name: the agent name to set
        """
        self._agent_name = agent_name

    def get_agent_name(self) -> str:
        """
        Exclusively called by tests.
        :return: the agent_name
        """
        return self._agent_name

    def __call__(self, channel: Channel):
        """
        Because of how service stubs are used to being passed around
        like a class, we use __call__() to short circuit a constructor-like
        call to use an actual instance.
        """

        # Prepare the service name given the agent name
        service_name: str = self.prepare_service_name(self._agent_name, self._service_prefix)

        # Below comes from generated _grpc.py code for the Stub,
        # with the modification of the service name going into the args.
        # One member variable for each grpc method.
        # pylint: disable=no-member
        self.Function = channel.unary_unary(
                f"/{service_name}/Function",
                request_serializer=agent__pb2.FunctionRequest.SerializeToString,
                response_deserializer=agent__pb2.FunctionResponse.FromString,
                )
        self.Chat = channel.unary_unary(
                f"/{service_name}/Chat",
                request_serializer=agent__pb2.ChatRequest.SerializeToString,
                response_deserializer=agent__pb2.ChatResponse.FromString,
                )
        self.Logs = channel.unary_unary(
                f"/{service_name}/Logs",
                request_serializer=agent__pb2.LogsRequest.SerializeToString,
                response_deserializer=agent__pb2.LogsResponse.FromString,
                )
        self.Reset = channel.unary_unary(
                f"/{service_name}/Reset",
                request_serializer=agent__pb2.ResetRequest.SerializeToString,
                response_deserializer=agent__pb2.ResetResponse.FromString,
                )

        return self

    @staticmethod
    def prepare_service_name(agent_name: str, service_prefix: str) -> str:
        """
        Prepares the full grpc service name given the name of the agent
        :param agent_name: The string agent name
        :param service_prefix: The service prefix.
                    This is often the same as the package name in the grpc file.
        :return: A service name that specifies the agent name as part of the routing.
        """

        # Prepare the service name on a per-agent basis
        service_name: str = f"{service_prefix}"

        # The agent name adds the voodoo to handle the request routing for each
        # agent on the same server.
        if agent_name is not None and len(agent_name) > 0:
            service_name += f".{agent_name}"

        # This string comes from the service definition within agent.proto
        service_name += ".AgentService"

        return service_name
