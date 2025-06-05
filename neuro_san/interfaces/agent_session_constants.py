
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


class AgentSessionConstants:
    """
    Interface for shared constants between AgentSession and AsyncAgentSession
    """

    # Default gRPC port for the Agent Service
    # This port number will also be mentioned in its Dockerfile
    DEFAULT_GRPC_PORT: int = 30011

    # For backwards compatibility
    DEFAULT_PORT: int = DEFAULT_GRPC_PORT

    # Default port for the Agent HTTP Service
    # This port number will also be mentioned in its Dockerfile
    DEFAULT_HTTP_PORT: int = 8080
