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


from neuro_san.api.grpc import mime_data_pb2 as neuro__san_dot_api_dot_grpc_dot_mime__data__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dneuro_san/api/grpc/chat.proto\x12(dev.cognizant_ai.neuro_san.api.grpc.chat\x1a\"neuro_san/api/grpc/mime_data.proto\"\xd9\x02\n\x0b\x43hatMessage\x12S\n\x04type\x18\x01 \x01(\x0e\x32\x45.dev.cognizant_ai.neuro_san.api.grpc.chat.ChatMessage.ChatMessageType\x12\x0c\n\x04text\x18\x02 \x01(\t\x12U\n\tmime_data\x18\x03 \x03(\x0b\x32\x37.dev.cognizant_ai.neuro_san.api.grpc.mime_data.MimeDataR\tmime_data\x12\x16\n\x06origin\x18\x04 \x03(\tR\x06origin\"x\n\x0f\x43hatMessageType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\n\n\x06SYSTEM\x10\x01\x12\t\n\x05HUMAN\x10\x02\x12\x08\n\x04TOOL\x10\x03\x12\x06\n\x02\x41I\x10\x04\x12\t\n\x05\x41GENT\x10\x64\x12\x13\n\x0f\x41GENT_FRAMEWORK\x10\x65\x12\x0f\n\x0bLEGACY_LOGS\x10\x66\x42\\ZZgithub.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/chat/v1;chatb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'neuro_san.api.grpc.chat_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'ZZgithub.com/leaf-ai/neuro_san/internal/gen/dev.cognizant_ai/neuro_san/api/grpc/chat/v1;chat'
  _globals['_CHATMESSAGE']._serialized_start=112
  _globals['_CHATMESSAGE']._serialized_end=457
  _globals['_CHATMESSAGE_CHATMESSAGETYPE']._serialized_start=337
  _globals['_CHATMESSAGE_CHATMESSAGETYPE']._serialized_end=457
# @@protoc_insertion_point(module_scope)
