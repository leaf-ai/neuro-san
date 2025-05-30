#!/usr/bin/env bash

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

# This script will:
# 1) Generate GRPC code for any services (generated or not) from its PROTO_FILE
# 2) Modify the code generated by protoc to conform to Python 3
#    by fully specifying package paths for local imports.

# Exit on any error during execution
set -e

# Find out where we are
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define some directories relative to where we are
# Note: All the protobuf guides say to not mix absolute and relative paths
#       So we pick absolute paths.
ONE_LEVEL_UP=${DIR%/*}
ANOTHER_LEVEL_UP=${ONE_LEVEL_UP%/*}
# Up one more directory is the top level
TOP_LEVEL=${ANOTHER_LEVEL_UP%/*}

GENERATED_DIR=neuro_san/api/grpc

# Ordering matters w/rt where generated file is output
PROTO_PATH="--proto_path=${TOP_LEVEL} --proto_path=${TOP_LEVEL}/${GENERATED_DIR}"
echo "PROTO_PATH is ${PROTO_PATH}"

# Inputs to the script
LOCAL_PROTO_FILES=$(< "${DIR}"/protobuf_manifest.txt)

COPYRIGHT_FILE="${TOP_LEVEL}/build_scripts/source_available_copyright.txt"

# Where output files go.
PYTHON_OUT=${TOP_LEVEL}

# Configuration values for OpenAPI specification document
SERVICE_TITLE=NeuroSan
SERVICE_VERSION=0.0.1

# Requirements:
#   We need to be able to export .proto files from here so they can be
#   protoc-compiled into external projects.
#   We also need to be able to run code in here that references pre-built
#   *_pb2*.py as a standalone library.
#
# Constraints:
#   When exported .proto files from here are used in external projects,
#   protoc-generated python there creates *another* local set of *_pb2*.py files
#   with a serialized version of a *copy* of the original .proto file in
#   its call to _descriptor_pool.Default().AddSerializedFile. When files
#   from both neuro-san and the external project are mixed, this sometimes
#   causes errors in the form of one of 2 errors:
#
#       1)  TypeError: Couldn't build proto file into descriptor pool:
#               Depends on file 'neuro_san/grpc/generated/agent.proto',
#               but it has not been loaded
#       2)  TypeError: Couldn't build proto file into descriptor pool:
#               duplicate symbol 'neuro_san.grpc.generated.agent.AgentStatus'
#
#   These errors arise due to unforgiving naming in the .proto here and unforgiving
#   placement constraints in the directory/package hierarchy.
#   When compiling the .proto file copy, it includes in the description sent to
#   AddSerializedFile() a file path that needs to be both relative to the
#   copied version of the .proto file and the external .proto file that is including
#   it for definitions.
#
#   Because of all this, we end up having to do a couple of things in this repo:
#       1)  .proto files need to live in the same place as where
#           the generated python files end up.
#       2)  Path/package/file names need to be specified from the top level of this repo.
#
#   In the end, any .proto file that is protoc-compiled here needs to come out
#   with the exact same contents of what is passed to AddSerializedFile()
#   when the external project's protoc operation copies and recompiles the .proto
#   file for its own purposes.  Though this isn't really documented anywhere AFAICT,
#   file placement and package naming is tweaked here so that kind of thing can happen
#   more easily in other external repos.

echo "Generating gRPC code in ${GENERATED_DIR}..."

# Create the generated directory if it doesn't exist already
mkdir -p "${GENERATED_DIR}"

# Create a file so that the python compiler can find source in the new dir.
touch "${GENERATED_DIR}"/__init__.py

# Copy over external proto files
ALL_PROTO_FILES=""
ALL_PROTO_FILES="${ALL_PROTO_FILES} ${LOCAL_PROTO_FILES}"

# Google API proto files are not automatically updated,
# but if this needs to be done, uncomment the lines below:
## Install google API related protobufs:
#GOOGLE_API_FILES="annotations.proto http.proto"
#GOOGLE_API_DIR="${TOP_LEVEL}"/"${GENERATED_DIR}"/google/api
#mkdir -p "${GOOGLE_API_DIR}"
#
#for PROTO_FILE in ${GOOGLE_API_FILES}
#do
#    curl --header "Accept: application/vnd.github.raw+json" \
#        --output "${GOOGLE_API_DIR}"/"${PROTO_FILE}" \
#    --location --show-error --silent --fail \
#    "https://api.github.com/repos/googleapis/googleapis/contents/google/api"/"${PROTO_FILE}"
#done
# End of lines to uncomment if you need
# to update Google API files with latest versions.

# Generate the python files and make them happy w/rt Python 3
for PROTO_FILE in ${ALL_PROTO_FILES}
do
    # Generate the GRPC code for a single service proto file.
    echo "generating gRPC code for ${PROTO_FILE}."
    # shellcheck disable=SC2086    # PROTO_PATH is compilation of cmd line args
    python -m grpc_tools.protoc ${PROTO_PATH} \
        --python_out="${PYTHON_OUT}" \
        --grpc_python_out="${PYTHON_OUT}" \
        "${PROTO_FILE}"

    # Prepend copyrights to output files
    MESSAGE_FILE="${PROTO_FILE/.proto/_pb2.py}"
    SERVICE_FILE="${PROTO_FILE/.proto/_pb2_grpc.py}"

    TEMPFILE=$(mktemp)
    cat "${COPYRIGHT_FILE}" "${MESSAGE_FILE}" > "${TEMPFILE}" && mv "${TEMPFILE}" "${MESSAGE_FILE}"
    TEMPFILE=$(mktemp)
    cat "${COPYRIGHT_FILE}" "${SERVICE_FILE}" > "${TEMPFILE}" && mv "${TEMPFILE}" "${SERVICE_FILE}"

done

# Now generate OpenAI specification for our service
# Check that we have necessary protoc plug-in installed:
"${TOP_LEVEL}"/neuro_san/api/scripts/check_openapi_plugin.sh

# Generate OpenAPI service specification
echo "generating OpenAPI specification for ${TOP_LEVEL}/${GENERATED_DIR}/agent.proto"
# shellcheck disable=SC2086    # PROTO_PATH is compilation of cmd line args
python -m grpc_tools.protoc ${PROTO_PATH} \
    --plugin=protoc-gen-openapi=${HOME}/go/bin/protoc-gen-openapi-enums \
    --openapi_out="${TOP_LEVEL}"/${GENERATED_DIR} \
    --openapi_opt title="${SERVICE_TITLE}" \
    --openapi_opt version="${SERVICE_VERSION}" \
    "${TOP_LEVEL}"/${GENERATED_DIR}/agent.proto \
    "${TOP_LEVEL}"/${GENERATED_DIR}/concierge.proto

# OpenAPI plug-in always generates openapi.yaml,
# so we rename it and convert to json format

OPENAPI_RESULT=${TOP_LEVEL}/${GENERATED_DIR}/openapi.yaml
REQUIRED_RESULT=${TOP_LEVEL}/${GENERATED_DIR}/agent_service.json

"${TOP_LEVEL}"/neuro_san/api/scripts/convert_yaml_to_json.sh "${OPENAPI_RESULT}" "${REQUIRED_RESULT}"

echo "generated output: ${REQUIRED_RESULT}"



