
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
from typing import List

import copy
import json
import uuid

import grpc

from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

from leaf_server_common.server.grpc_metadata_forwarder import GrpcMetadataForwarder
from leaf_server_common.server.request_logger import RequestLogger

from neuro_san.api.grpc import concierge_pb2 as concierge_messages
from neuro_san.api.grpc import concierge_pb2_grpc


from neuro_san.session.direct_concierge_session import DirectConciergeSession


# pylint: disable=too-few-public-methods
class ConciergeService(concierge_pb2_grpc.ConciergeServiceServicer):
    """
    A gRPC implementation of the Neuro-San Concierge Service.
    """

    def __init__(self,
                 request_logger: RequestLogger,
                 security_cfg: Dict[str, Any],
                 forwarded_request_metadata: List[str]):
        """
        Set the gRPC interface up for health checking so that the service
        will be opened to callers when the mesh sees it operational, if this
        is not done the mesh will treat the service instance as nonfunctional

        :param request_logger: The instance of the RequestLogger that helps
                    keep track of stats
        :param security_cfg: A dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  If None, uses insecure channel.
        :param forwarded_request_metadata: A list of http metadata request keys
                        to forward to logs/other requests
        """
        self.request_logger = request_logger
        self.security_cfg = security_cfg
        self.forwarder = GrpcMetadataForwarder(forwarded_request_metadata)

    # pylint: disable=no-member
    def Describe(self, request: concierge_messages.ConciergeRequest,
                 context: grpc.ServicerContext) \
            -> concierge_messages.ConciergeResponse:
        """
        Allows a client to get the description of available agents
        served by this service.

        :param request: a ConciergeRequest
        :param context: a grpc.ServicerContext
        :return: a ConciergeResponse
        """
        request_log = None
        log_marker: str = "concierge request"
        service_logging_dict: Dict[str, str] = {
            "request_id": f"server-{uuid.uuid4()}"
        }
        request_log = self.request_logger.start_request("Describe",
                                                        log_marker, context,
                                                        service_logging_dict)

        # Get the metadata to forward on to another service
        metadata: Dict[str, str] = copy.copy(service_logging_dict)
        metadata.update(self.forwarder.forward(context))

        # Get our args in order to pass to grpc-free session level
        request_dict: Dict[str, Any] = MessageToDict(request)

        # Delegate to Direct*Session
        session = DirectConciergeSession(metadata=metadata,
                                         security_cfg=self.security_cfg)
        response_dict = session.describe(request_dict)

        # Convert the response dictionary to a grpc message
        response_string = json.dumps(response_dict)
        response = concierge_messages.ConciergeResponse()
        Parse(response_string, response)

        if request_log is not None:
            self.request_logger.finish_request("Describe", log_marker, request_log)

        return response
