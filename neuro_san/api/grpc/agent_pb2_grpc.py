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
# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from neuro_san.api.grpc import agent_pb2 as neuro__san_dot_api_dot_grpc_dot_agent__pb2


class AgentServiceStub(object):
    """The service comprises all the exchanges to the backend in support of a single agent's
    services.  Routing is done by way of agent name on the grpc service hosting the agent,
    so as to keep info about which agents are hosted private (grpc gives the hand when a
    particular agent is unknown.

    Note that as of 3/21/24, this is *not* yet a REST-ful service due to constraints
    with OpenAI service and/or linux socket timeouts used behind the scenes.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Function = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Function',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionResponse.FromString,
                )
        self.Chat = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Chat',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.FromString,
                )
        self.Logs = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Logs',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsResponse.FromString,
                )
        self.Reset = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Reset',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetResponse.FromString,
                )
        self.StreamingChat = channel.unary_stream(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/StreamingChat',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.FromString,
                )
        self.Connectivity = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Connectivity',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityResponse.FromString,
                )


class AgentServiceServicer(object):
    """The service comprises all the exchanges to the backend in support of a single agent's
    services.  Routing is done by way of agent name on the grpc service hosting the agent,
    so as to keep info about which agents are hosted private (grpc gives the hand when a
    particular agent is unknown.

    Note that as of 3/21/24, this is *not* yet a REST-ful service due to constraints
    with OpenAI service and/or linux socket timeouts used behind the scenes.
    """

    def Function(self, request, context):
        """Called when a client needs the function description of an agent.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Chat(self, request, context):
        """Called when the user needs to initialize a new chat request
        or respond to an LLM's request during an already initialized chat.
        NOTE: This method is deprecated in favor of StreamingChat
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Logs(self, request, context):
        """Polls for chat results which are processed asynchronously from Chat() above.
        NOTE: This method is deprecated in favor of StreamingChat
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Reset(self, request, context):
        """Resets the chat initiated with Chat() above.
        NOTE: This method is deprecated in favor of StreamingChat
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StreamingChat(self, request, context):
        """Unidirectional streaming method which would supercede Chat() and Logs() above.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Connectivity(self, request, context):
        """Called when a client needs the internal connectivity description of an agent.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AgentServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Function': grpc.unary_unary_rpc_method_handler(
                    servicer.Function,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionResponse.SerializeToString,
            ),
            'Chat': grpc.unary_unary_rpc_method_handler(
                    servicer.Chat,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.SerializeToString,
            ),
            'Logs': grpc.unary_unary_rpc_method_handler(
                    servicer.Logs,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsResponse.SerializeToString,
            ),
            'Reset': grpc.unary_unary_rpc_method_handler(
                    servicer.Reset,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetResponse.SerializeToString,
            ),
            'StreamingChat': grpc.unary_stream_rpc_method_handler(
                    servicer.StreamingChat,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.SerializeToString,
            ),
            'Connectivity': grpc.unary_unary_rpc_method_handler(
                    servicer.Connectivity,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class AgentService(object):
    """The service comprises all the exchanges to the backend in support of a single agent's
    services.  Routing is done by way of agent name on the grpc service hosting the agent,
    so as to keep info about which agents are hosted private (grpc gives the hand when a
    particular agent is unknown.

    Note that as of 3/21/24, this is *not* yet a REST-ful service due to constraints
    with OpenAI service and/or linux socket timeouts used behind the scenes.
    """

    @staticmethod
    def Function(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Function',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.FunctionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Chat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Chat',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Logs(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Logs',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.LogsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Reset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Reset',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ResetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StreamingChat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/StreamingChat',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ChatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Connectivity(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.agent.AgentService/Connectivity',
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_agent__pb2.ConnectivityResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
