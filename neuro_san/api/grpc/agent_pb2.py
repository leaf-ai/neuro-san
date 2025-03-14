
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
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: neuro_san/api/grpc/agent.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from neuro_san.api.grpc import chat_pb2 as neuro__san_dot_api_dot_grpc_dot_chat__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1eneuro_san/api/grpc/agent.proto\x12)dev.cognizant_ai.neuro_san.api.grpc.agent\x1a\x1cgoogle/protobuf/struct.proto\x1a\x1dneuro_san/api/grpc/chat.proto\"\x11\n\x0f\x46unctionRequest\"e\n\x08\x46unction\x12 \n\x0b\x64\x65scription\x18\x01 \x01(\tR\x0b\x64\x65scription\x12\x37\n\nparameters\x18\x02 \x01(\x0b\x32\x17.google.protobuf.StructR\nparameters\"c\n\x10\x46unctionResponse\x12O\n\x08\x66unction\x18\x01 \x01(\x0b\x32\x33.dev.cognizant_ai.neuro_san.api.grpc.agent.FunctionR\x08\x66unction\"s\n\nChatFilter\x12\x65\n\x10\x63hat_filter_type\x18\x01 \x01(\x0e\x32\x39.dev.cognizant_ai.neuro_san.api.grpc.agent.ChatFilterTypeR\x10\x63hat_filter_type\"\xd1\x02\n\x0b\x43hatRequest\x12\x33\n\x08sly_data\x18\x03 \x01(\x0b\x32\x17.google.protobuf.StructR\x08sly_data\x12Y\n\x0cuser_message\x18\x04 \x01(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatMessageR\x0cuser_message\x12Y\n\x0c\x63hat_context\x18\x05 \x01(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatContextR\x0c\x63hat_context\x12W\n\x0b\x63hat_filter\x18\x06 \x01(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.agent.ChatFilterR\x0b\x63hat_filter\"\xaa\x01\n\x0c\x43hatResponse\x12G\n\x07request\x18\x01 \x01(\x0b\x32\x36.dev.cognizant_ai.neuro_san.api.grpc.agent.ChatRequest\x12Q\n\x08response\x18\x04 \x01(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatMessageR\x08response\"\x15\n\x13\x43onnectivityRequest\"@\n\x10\x43onnectivityInfo\x12\x16\n\x06origin\x18\x01 \x01(\tR\x06origin\x12\x14\n\x05tools\x18\x02 \x03(\tR\x05tools\"\x81\x01\n\x14\x43onnectivityResponse\x12i\n\x11\x63onnectivity_info\x18\x01 \x03(\x0b\x32;.dev.cognizant_ai.neuro_san.api.grpc.agent.ConnectivityInfoR\x11\x63onnectivity_info**\n\x0e\x43hatFilterType\x12\x0b\n\x07MINIMAL\x10\x00\x12\x0b\n\x07MAXIMAL\x10\x01\x32\xb1\x03\n\x0c\x41gentService\x12\x85\x01\n\x08\x46unction\x12:.dev.cognizant_ai.neuro_san.api.grpc.agent.FunctionRequest\x1a;.dev.cognizant_ai.neuro_san.api.grpc.agent.FunctionResponse\"\x00\x12\x84\x01\n\rStreamingChat\x12\x36.dev.cognizant_ai.neuro_san.api.grpc.agent.ChatRequest\x1a\x37.dev.cognizant_ai.neuro_san.api.grpc.agent.ChatResponse\"\x00\x30\x01\x12\x91\x01\n\x0c\x43onnectivity\x12>.dev.cognizant_ai.neuro_san.api.grpc.agent.ConnectivityRequest\x1a?.dev.cognizant_ai.neuro_san.api.grpc.agent.ConnectivityResponse\"\x00\x42^Z\\github.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/agent/v1;agentb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'neuro_san.api.grpc.agent_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\\github.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/agent/v1;agent'
  _globals['_CHATFILTERTYPE']._serialized_start=1212
  _globals['_CHATFILTERTYPE']._serialized_end=1254
  _globals['_FUNCTIONREQUEST']._serialized_start=138
  _globals['_FUNCTIONREQUEST']._serialized_end=155
  _globals['_FUNCTION']._serialized_start=157
  _globals['_FUNCTION']._serialized_end=258
  _globals['_FUNCTIONRESPONSE']._serialized_start=260
  _globals['_FUNCTIONRESPONSE']._serialized_end=359
  _globals['_CHATFILTER']._serialized_start=361
  _globals['_CHATFILTER']._serialized_end=476
  _globals['_CHATREQUEST']._serialized_start=479
  _globals['_CHATREQUEST']._serialized_end=816
  _globals['_CHATRESPONSE']._serialized_start=819
  _globals['_CHATRESPONSE']._serialized_end=989
  _globals['_CONNECTIVITYREQUEST']._serialized_start=991
  _globals['_CONNECTIVITYREQUEST']._serialized_end=1012
  _globals['_CONNECTIVITYINFO']._serialized_start=1014
  _globals['_CONNECTIVITYINFO']._serialized_end=1078
  _globals['_CONNECTIVITYRESPONSE']._serialized_start=1081
  _globals['_CONNECTIVITYRESPONSE']._serialized_end=1210
  _globals['_AGENTSERVICE']._serialized_start=1257
  _globals['_AGENTSERVICE']._serialized_end=1690
# @@protoc_insertion_point(module_scope)
