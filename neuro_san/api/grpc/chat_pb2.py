
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
# source: neuro_san/api/grpc/chat.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from neuro_san.api.grpc import mime_data_pb2 as neuro__san_dot_api_dot_grpc_dot_mime__data__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dneuro_san/api/grpc/chat.proto\x12(dev.cognizant_ai.neuro_san.api.grpc.chat\x1a\x1cgoogle/protobuf/struct.proto\x1a\"neuro_san/api/grpc/mime_data.proto\"N\n\x06Origin\x12\x12\n\x04tool\x18\x01 \x01(\tR\x04tool\x12\x30\n\x13instantiation_index\x18\x02 \x01(\x05R\x13instantiation_index\"\xaa\x01\n\x0b\x43hatHistory\x12H\n\x06origin\x18\x01 \x03(\x0b\x32\x30.dev.cognizant_ai.neuro_san.api.grpc.chat.OriginR\x06origin\x12Q\n\x08messages\x18\x02 \x03(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatMessageR\x08messages\"l\n\x0b\x43hatContext\x12]\n\x0e\x63hat_histories\x18\x01 \x03(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatHistoryR\x0e\x63hat_histories\"\x97\x05\n\x0b\x43hatMessage\x12S\n\x04type\x18\x01 \x01(\x0e\x32\x45.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatMessage.ChatMessageType\x12\x0c\n\x04text\x18\x02 \x01(\t\x12U\n\tmime_data\x18\x03 \x03(\x0b\x32\x37.dev.cognizant_ai.neuro_san.api.grpc.mime_data.MimeDataR\tmime_data\x12H\n\x06origin\x18\x04 \x03(\x0b\x32\x30.dev.cognizant_ai.neuro_san.api.grpc.chat.OriginR\x06origin\x12\x35\n\tstructure\x18\x05 \x01(\x0b\x32\x17.google.protobuf.StructR\tstructure\x12Y\n\x0c\x63hat_context\x18\x06 \x01(\x0b\x32\x35.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatContextR\x0c\x63hat_context\x12`\n\x12tool_result_origin\x18\x07 \x03(\x0b\x32\x30.dev.cognizant_ai.neuro_san.api.grpc.chat.OriginR\x12tool_result_origin\"\x8f\x01\n\x0f\x43hatMessageType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\n\n\x06SYSTEM\x10\x01\x12\t\n\x05HUMAN\x10\x02\x12\x08\n\x04TOOL\x10\x03\x12\x06\n\x02\x41I\x10\x04\x12\t\n\x05\x41GENT\x10\x64\x12\x13\n\x0f\x41GENT_FRAMEWORK\x10\x65\x12\x0f\n\x0bLEGACY_LOGS\x10\x66\x12\x15\n\x11\x41GENT_TOOL_RESULT\x10gB\\ZZgithub.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/chat/v1;chatb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'neuro_san.api.grpc.chat_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'ZZgithub.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/chat/v1;chat'
  _globals['_ORIGIN']._serialized_start=141
  _globals['_ORIGIN']._serialized_end=219
  _globals['_CHATHISTORY']._serialized_start=222
  _globals['_CHATHISTORY']._serialized_end=392
  _globals['_CHATCONTEXT']._serialized_start=394
  _globals['_CHATCONTEXT']._serialized_end=502
  _globals['_CHATMESSAGE']._serialized_start=505
  _globals['_CHATMESSAGE']._serialized_end=1168
  _globals['_CHATMESSAGE_CHATMESSAGETYPE']._serialized_start=1025
  _globals['_CHATMESSAGE_CHATMESSAGETYPE']._serialized_end=1168
# @@protoc_insertion_point(module_scope)
