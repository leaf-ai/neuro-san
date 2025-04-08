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

# Script used to build the container that runs the Neuro-San Agent Service

export SERVICE_DIR=deploy/internal
export SERVICE_TAG=neuro-san
export SERVICE_VERSION=0.0.1


function check_run_directory() {

    # Everything here needs to be done from the top-level directory for the repo
    working_dir=$(pwd)
    exec_dir=$(basename "${working_dir}")
    if [ "$exec_dir" != "neuro-san" ]
    then
        echo "This script must be run from the top-level directory for the repo"
        exit 1
    fi
}

function build_main() {
    # Outline function which delegates most work to other functions

    # Parse for a specific arg when debugging
    CACHE_OR_NO_CACHE="--rm"
    if [ "$1" == "--no-cache" ]
    then
        CACHE_OR_NO_CACHE="--no-cache --progress=plain"
    fi

    check_run_directory

    if [ -z "${TARGET_PLATFORM}" ]
    then
        TARGET_PLATFORM="linux/amd64"
    fi
    echo "Target Platform for Docker image generation: ${TARGET_PLATFORM}"

    # Build the docker image
    # DOCKER_BUILDKIT needed for secrets stuff
    # shellcheck disable=SC2086
    DOCKER_BUILDKIT=1 docker build \
        -t leaf/${SERVICE_TAG}:${SERVICE_VERSION} \
        --platform ${TARGET_PLATFORM} \
        --build-arg="NEURO_SAN_VERSION=${USER}-$(date +'%Y-%m-%d-%H-%M')" \
        -f ./neuro_san/${SERVICE_DIR}/Dockerfile \
        ${CACHE_OR_NO_CACHE} \
        .
}


# Call the build_main() outline function
build_main "$@"
