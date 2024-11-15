#!/bin/bash

# Entry point script which manages the transition from
# Docker bash to Python

cat /etc/os-release

PYTHON=python3
echo "Using python ${PYTHON}"

PIP=pip3
echo "Using pip ${PIP}"

echo "Preparing app..."
cd myapp || exit
PYTHONPATH=$(pwd)
export PYTHONPATH

echo "Toolchain:"
${PYTHON} --version
${PIP} --version
${PIP} freeze

echo "Starting grpc service with args '$1'..."
${PYTHON} backend/agents/service/agent_main_loop.py "$@"

echo "Done."
