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

export SERVICE_DIR=service
export SERVICE_TAG=neuro-san
export SERVICE_VERSION=0.0.1
export SERVICE_REQUIREMENTS_TXT=neuro_san/${SERVICE_DIR}/requirements.txt


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

function check_vault_access() {
    # Check to see that we have the proper environment variables
    # set so that we can get from the Vault service some ephemeral GitHub creds
    # that will be used in the git credential file briefly mounted
    # in the container.

    if [ -z "${VAULT_ADDR}" ]
    then
        # Try to use LEAF_TEAM_VAULT_ADDR if it's set
        if [ -z "${LEAF_TEAM_VAULT_ADDR}" ]
        then
            echo "VAULT_ADDR needs to be set to a valid Vault server"
            echo "that dispenses ephemeral GitHub tokens in order to load"
            echo "source-available GitHub code into echo the new container"
            exit 2
        else
            VAULT_ADDR=${LEAF_TEAM_VAULT_ADDR}
        fi
    fi

    if [ -z "${VAULT_GITHUB_AUTH_TOKEN}" ]
    then
        echo "VAULT_GITHUB_AUTH_TOKEN needs to be set to a valid"
        echo "GitHub token from your account that will get you into"
        echo "the vault server at ${VAULT_ADDR} so that it can"
        echo "dispense ephemeral GitHub tokens to load"
        echo "source-available GitHub code into echo the new container."
        echo "The VAULT_GITHUB_AUTH_TOKEN needs read:org permissions *only*."
        exit 3
    fi
}

function create_git_creds_requirements() {
    # Create the temporary file that gets mounted into the container
    # which contains ephemeral git creds for source-available repos.

    # Get rid of any turds from any previous attempts with a fresh copy
    # of the base requirements file.
    WITH_CREDS_REQUIREMENTS=/tmp/.git_creds_requirements.txt
    cp requirements.txt ${WITH_CREDS_REQUIREMENTS}

    # If there are any service requirements use those instead as a complete
    # list.
    if [ -f "${SERVICE_REQUIREMENTS_TXT}" ]
    then
        cp ${SERVICE_REQUIREMENTS_TXT} ${WITH_CREDS_REQUIREMENTS}
    fi

    # Login into Vault only once
    vault login -address="${VAULT_ADDR}" -method=github token="${VAULT_GITHUB_AUTH_TOKEN}" \
            | grep -Ev "(token |token_accessor)"

    # Get the ephemeral token for public repos
    EPHEMERAL_TOKEN=$(vault read -address="${VAULT_ADDR}" -field=token /github-secrets/token/repo-read)
    EPHEMERAL_LEAF_SOURCE_CREDENTIALS="x-access-token:${EPHEMERAL_TOKEN}"
    sed -i.bak "s/\${LEAF_SOURCE_CREDENTIALS}/${EPHEMERAL_LEAF_SOURCE_CREDENTIALS}/g" ${WITH_CREDS_REQUIREMENTS}

    # Get the ephemeral token for private repos
    EPHEMERAL_TOKEN=$(vault read -address="${VAULT_ADDR}" -field=token /github-private-secrets/token/repo-read)
    EPHEMERAL_LEAF_SOURCE_CREDENTIALS="x-access-token:${EPHEMERAL_TOKEN}"
    sed -i.bak "s/\${LEAF_PRIVATE_SOURCE_CREDENTIALS}/${EPHEMERAL_LEAF_SOURCE_CREDENTIALS}/g" ${WITH_CREDS_REQUIREMENTS}

    chmod 600 ${WITH_CREDS_REQUIREMENTS}
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
    check_vault_access

    create_git_creds_requirements

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
        --secret id=with_creds_requirements,src=${WITH_CREDS_REQUIREMENTS} \
        --build-arg="UNILEAF_VERSION=${USER}-$(date +'%Y-%m-%d-%H-%M')" \
        -f ./neuro_san/${SERVICE_DIR}/Dockerfile \
        ${CACHE_OR_NO_CACHE} \
        .

    # Remove the temporary creds file created in create_git_creds_requirements() above
    rm ${WITH_CREDS_REQUIREMENTS}
}


# Call the build_main() outline function
build_main "$@"
