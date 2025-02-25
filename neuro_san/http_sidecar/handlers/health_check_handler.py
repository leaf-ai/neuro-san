
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
from typing import Any, Dict

from tornado.web import RequestHandler


class HealthCheckHandler(RequestHandler):
    """
    Handler class for API endpoint health check.
    """

    def get(self):
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
            self.flush()

    def data_received(self, chunk):
        """
        Method overrides abstract method of RequestHandler
        with no-op implementation.
        """
        return
