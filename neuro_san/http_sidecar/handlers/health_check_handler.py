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
import http
import os
from typing import Any, Dict, List

from tornado.web import RequestHandler
from neuro_san.http_sidecar.logging.http_logger import HttpLogger


class HealthCheckHandler(RequestHandler):
    """
    Handler class for API endpoint health check.
    """

    # pylint: disable=attribute-defined-outside-init
    def initialize(self, forwarded_request_metadata: List[str]):
        """
        This method is called by Tornado framework to allow
        injecting service-specific data into local handler context.
        Here we use it to inject CORS headers if so configured.
        """
        self.logger = HttpLogger(forwarded_request_metadata)
        if os.environ.get("AGENT_ALLOW_CORS_HEADERS") is not None:
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.set_header("Access-Control-Allow-Headers", "Content-Type, Transfer-Encoding")

    async def get(self):
        """
        Implementation of GET request handler for API health check.
        """

        try:
            result_dict: Dict[str, Any] = \
                {"service": "neuro-san agents",
                 "status": "healthy"}
            self.set_header("Content-Type", "application/json")
            self.write(result_dict)
        except Exception:  # pylint: disable=broad-exception-caught
            # Handle unexpected errors
            self.set_status(500)
            self.write({"error": "Internal server error"})
        finally:
            self.finish()

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get request metadata
        """
        return {}

    def data_received(self, chunk):
        """
        Method overrides abstract method of RequestHandler
        with no-op implementation.
        """
        return

    async def options(self, *_args, **_kwargs):
        """
        Handles OPTIONS requests for CORS support
        """
        # No body needed. Just return a 204 No Content
        self.set_status(http.HTTPStatus.NO_CONTENT)
        self.finish()
