
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
from typing import Any, Dict, Generator
import json

import asyncio

from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import ChatRequest, ChatResponse

from neuro_san.http_sidecar.handlers.base_request_handler import BaseRequestHandler
from neuro_san.interfaces.async_agent_session import AsyncAgentSession


class StreamingChatHandler(BaseRequestHandler):
    """
    Handler class for neuro-san streaming chat API call.
    """

    async def stream_out(self,
                         generator: Generator[Generator[ChatResponse, None, None], None, None]):
        """
        Process streaming out generator output to HTTP connection.
        :param generator: async gRPC generator
        """
        # Set up headers for chunked response
        self.set_header("Content-Type", "application/json")
        self.set_header("Transfer-Encoding", "chunked")
        # Flush headers immediately
        await self.flush()

        # async for result_message in result_generator:
        # result_generator = self.async_generator()
        async for sub_generator in generator:
            async for result_message in sub_generator:
                result_dict: Dict[str, Any] = MessageToDict(result_message)
                result_str: str = json.dumps(result_dict) + "\n"
                self.write(result_str)
                await self.flush()

    async def post(self):
        """
        Implementation of POST request handler for streaming chat API call.
        """

        try:
            # Parse JSON body
            data = json.loads(self.request.body)

            grpc_request = Parse(json.dumps(data), ChatRequest())
            metadata: Dict[str, Any] = self.get_metadata()
            grpc_session: AsyncAgentSession = self.get_agent_grpc_session(metadata)

            # Mind the type hint:
            # here we are getting Generator of Generators of ChatResponses!
            result_generator: Generator[Generator[ChatResponse, None, None], None, None] =\
                grpc_session.streaming_chat(grpc_request)
            await self.stream_out(result_generator)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.process_exception(exc)
        finally:
            await self.flush()
        # We are done with response stream:
        await self.finish()
