
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
                         generator: Generator[Generator[ChatResponse, None, None], None, None]) -> int:
        """
        Process streaming out generator output to HTTP connection.
        :param generator: async gRPC generator
        :return: number of chat responses streamed out.
        """
        # Set up headers for chunked response
        self.set_header("Content-Type", "application/json-lines")
        self.set_header("Transfer-Encoding", "chunked")
        # Flush headers immediately
        flush_ok: bool = await self.do_flush()
        if not flush_ok:
            return 0

        sent_out: int = 0
        async for sub_generator in generator:
            async for result_message in sub_generator:
                result_dict: Dict[str, Any] = MessageToDict(result_message)
                result_str: str = json.dumps(result_dict) + "\n"
                self.write(result_str)
                flush_ok = await self.do_flush()
                if not flush_ok:
                    return sent_out
                sent_out += 1
        return sent_out

    async def post(self, agent_name: str):
        """
        Implementation of POST request handler for streaming chat API call.
        """

        metadata: Dict[str, Any] = self.get_metadata()
        update_done: bool = await self.update_agents(metadata=metadata)
        if not update_done:
            return

        if not self.agent_policy.allow(agent_name):
            self.set_status(404)
            self.logger.error({}, "error: Invalid request path %s", self.request.path)
            self.do_finish()
            return

        self.logger.info(metadata, "Start POST %s/streaming_chat", agent_name)
        sent_out = 0
        try:
            # Parse JSON body
            data = json.loads(self.request.body)

            grpc_request = Parse(json.dumps(data), ChatRequest())
            grpc_session: AsyncAgentSession = self.get_agent_grpc_session(metadata, agent_name)

            # Mind the type hint:
            # here we are getting Generator of Generators of ChatResponses!
            result_generator: Generator[Generator[ChatResponse, None, None], None, None] =\
                grpc_session.streaming_chat(grpc_request)
            sent_out = await self.stream_out(result_generator)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.process_exception(exc)
        finally:
            # We are done with response stream:
            self.do_finish()
            self.logger.info(metadata, "Finish POST %s/streaming_chat %d responses", agent_name, sent_out)
