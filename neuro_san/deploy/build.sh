#!/bin/bash -e

# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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
#
# Furthermore, you should have all neuro-san wheel files installed in your
# virtual environment

export SERVICE_TAG=${SERVICE_TAG:-neuro-san}
export SERVICE_VERSION=${SERVICE_VERSION:-0.0.1}

function check_directory() {
    working_dir=$(pwd)
    if [ "neuro-san" == "$(basename "${working_dir}")" ]
    then
        # We are in the neuro-san repo.
        # Change directories so that the rest of the script will work OK.
        cd neuro_san || exit 1
    fi
}

function gather_wheels() {

    # 1. Look through the output of pip freeze
    # 2. Look for entries where wheel files were installed locally (file:)
    # 3. Only use the local file location of the wheel file from the pip output (print $3)
    # 4. Strip off the file:// beginning to get a local path
    # 5. Strip off the end #<sha> information
    # 6. Replace any %2B occurrence with + - this allows for local builds of neuro-san wheels for testing
    # This should give us the local file where the wheel was installed from.
    local_wheels=$(pip freeze | \
                    grep file: | \
                    awk '{ print $3 }' | \
                    sed "s/file:\/\///g" | \
                    awk 'BEGIN { FS = "#" } ; { print $1 }' | \
                    sed "s/%2B/+/g") 

    # If you change this, the Dockerfile needs to match
    export INSTALL_WHEELS="./.requirements-wheels"

    # Get rid of any cruft from previous runs
    rm -rf ${INSTALL_WHEELS}
    mkdir -p ${INSTALL_WHEELS}

    echo "Copying local installed wheels to ${INSTALL_WHEELS}"
    for wheel_file in ${local_wheels}
    do
        dest_file=$(basename "${wheel_file}")
        cp "${wheel_file}" "${INSTALL_WHEELS}/${dest_file}"
    done
}


function build_main() {
    # Outline function which delegates most work to other functions

    check_directory

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

    gather_wheels

    DOCKERFILE=$(find . -name Dockerfile | sort | head -1)

    # Build the docker image
    # DOCKER_BUILDKIT needed for secrets
    # shellcheck disable=SC2086
    DOCKER_BUILDKIT=1 docker build \
        -t neuro-san/${SERVICE_TAG}:${SERVICE_VERSION} \
        --platform ${TARGET_PLATFORM} \
        --build-arg="NEURO_SAN_VERSION=${USER}-$(date +'%Y-%m-%d-%H-%M')" \
        -f "${DOCKERFILE}" \
        ${CACHE_OR_NO_CACHE} \
        .

    # Remove the temporary creds file created in create_git_creds_requirements() above
    rm -rf ${INSTALL_WHEELS}
}


# Call the build_main() outline function
build_main "$@"
