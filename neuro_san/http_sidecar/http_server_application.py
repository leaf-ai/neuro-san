
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
"""
See class comment for details
"""
from tornado.web import Application

from neuro_san.client.agent_session_factory import AgentSessionFactory


class HttpServerApplication(Application):
    """
    Subclass of Tornado Application class used to provide
    additional context for requests handling:
    our internal session factory to connect to agents gRPC service.
    """
    def __init__(self, *args, **kwargs):
        # Initialize the base Application
        super().__init__(*args, **kwargs)

        # Initialize and store dependencies:
        self.session_factory: AgentSessionFactory = AgentSessionFactory()

    def get_session_factory(self):
        return self.session_factory
