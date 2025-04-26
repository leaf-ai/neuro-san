#!/bin/bash -e

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

# Script used to build the container that runs the Decision Assistant Service
# Usage:
#   build.sh [--no-cache]
#
# The script must be run from the top-level directory of where your
# registries and code lives so as to properly import them into the Dockerfile.

export SERVICE_TAG=${SERVICE_TAG:-neuro-san}
export SERVICE_VERSION=${SERVICE_VERSION:-0.0.1}

function build_main() {
    # Outline function which delegates most work to other functions

    # Parse for a specific arg when debugging
    CACHE_OR_NO_CACHE="--rm"
    if [ "$1" == "--no-cache" ]
    then
        CACHE_OR_NO_CACHE="--no-cache --progress=plain"
    fi

    if [ -z "${TARGET_PLATFORM}" ]
    then
        TARGET_PLATFORM="linux/amd64"
    fi
    echo "Target Platform for Docker image generation: ${TARGET_PLATFORM}"

    DOCKERFILE=$(find . -name Dockerfile | sort | tail -1)

    # See if we are building from within neuro-san repo to optionally set a build arg.
    PACKAGE_INSTALL="DUMMY=dummy"
    if [ "$(ls -d neuro_san)" == "neuro_san" ]
    then
        PACKAGE_INSTALL="PACKAGE_INSTALL=/usr/local/neuro-san/myapp"
    fi
    echo "PACKAGE_INSTALL is ${PACKAGE_INSTALL}"

    # Build the docker image
    # DOCKER_BUILDKIT needed for secrets
    # shellcheck disable=SC2086
    DOCKER_BUILDKIT=1 docker build \
        -t neuro-san/${SERVICE_TAG}:${SERVICE_VERSION} \
        --platform ${TARGET_PLATFORM} \
        --build-arg NEURO_SAN_VERSION="${USER}-$(date +'%Y-%m-%d-%H-%M')" \
        --build-arg "${PACKAGE_INSTALL}" \
        -f "${DOCKERFILE}" \
        ${CACHE_OR_NO_CACHE} \
        .
}


# Call the build_main() outline function
build_main "$@"
