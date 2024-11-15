from typing import Dict

from grpc import GenericRpcHandler
from grpc import RpcMethodHandler
from grpc import Server
from grpc import method_handlers_generic_handler
from grpc import unary_unary_rpc_method_handler

from neuro_san.session.agent_service_stub import DEFAULT_SERVICE_PREFIX
from neuro_san.session.agent_service_stub import AgentServiceStub
import neuro_san.grpc.generated.agent_pb2 as agent__pb2
from neuro_san.grpc.generated.agent_pb2_grpc import AgentServiceServicer


# pylint: disable=too-few-public-methods
class AgentServicerToServer:
    """
    Taken from generated gRPC code from the agent_pb2_grpc.py file
    so multiple services of the same service protobuf construction can be serviced
    by the same server with a simple addition of an agent name in the gRPC path.
    """

    def __init__(self, servicer: AgentServiceServicer,
                 agent_name: str = "",
                 service_prefix: str = DEFAULT_SERVICE_PREFIX):
        """
        Constructor
        """
        self.servicer: AgentServiceServicer = servicer
        self.agent_name: str = agent_name
        self.service_prefix: str = service_prefix

    def add_rpc_handlers(self, server: Server):
        """
        Adds the RpcMethodHandlers to the server
        :param server: The grpc.Server to which method handlers should be added
        """

        # One entry for each grpc method defined in the agent handling protobuf
        # Note that all methods (as of 8/27/2024) are unary_unary.
        # (Watch generated _grpc.py for changes).
        # pylint: disable=no-member
        rpc_method_handlers: Dict[str, RpcMethodHandler] = {
            'Function': unary_unary_rpc_method_handler(
                    self.servicer.Function,
                    request_deserializer=agent__pb2.FunctionRequest.FromString,
                    response_serializer=agent__pb2.FunctionResponse.SerializeToString,
            ),
            'Chat': unary_unary_rpc_method_handler(
                    self.servicer.Chat,
                    request_deserializer=agent__pb2.ChatRequest.FromString,
                    response_serializer=agent__pb2.ChatResponse.SerializeToString,
            ),
            'Logs': unary_unary_rpc_method_handler(
                    self.servicer.Logs,
                    request_deserializer=agent__pb2.LogsRequest.FromString,
                    response_serializer=agent__pb2.LogsResponse.SerializeToString,
            ),
            'Reset': unary_unary_rpc_method_handler(
                    self.servicer.Reset,
                    request_deserializer=agent__pb2.ResetRequest.FromString,
                    response_serializer=agent__pb2.ResetResponse.SerializeToString,
            ),
        }

        # Prepare the service name on a per-agent basis
        service_name: str = AgentServiceStub.prepare_service_name(self.agent_name, self.service_prefix)

        generic_handler: GenericRpcHandler = method_handlers_generic_handler(service_name,
                                                                             rpc_method_handlers)
        server.add_generic_rpc_handlers((generic_handler,))
