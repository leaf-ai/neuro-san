
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

from neuro_san.api.grpc import concierge_pb2 as neuro__san_dot_api_dot_grpc_dot_concierge__pb2


class ConciergeServiceStub(object):
    """The service
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.List = channel.unary_unary(
                '/dev.cognizant_ai.neuro_san.api.grpc.concierge.ConciergeService/List',
                request_serializer=neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeRequest.SerializeToString,
                response_deserializer=neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeResponse.FromString,
                )


class ConciergeServiceServicer(object):
    """The service
    """

    def List(self, request, context):
        """Called when a client needs the information about available agents.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ConciergeServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'List': grpc.unary_unary_rpc_method_handler(
                    servicer.List,
                    request_deserializer=neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeRequest.FromString,
                    response_serializer=neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dev.cognizant_ai.neuro_san.api.grpc.concierge.ConciergeService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ConciergeService(object):
    """The service
    """

    @staticmethod
    def List(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dev.cognizant_ai.neuro_san.api.grpc.concierge.ConciergeService/List',
            neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeRequest.SerializeToString,
            neuro__san_dot_api_dot_grpc_dot_concierge__pb2.ConciergeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
