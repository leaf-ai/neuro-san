
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
# This Dockerfile is expected to be run from the top-level of neuro-san.

# Stage 1: Builder Stage - Use our python and git base image for installations
# Set python image as base image
FROM python:3.10-slim as builder

# Define the build argument for the Git version, no default provided by design
ARG GIT_VERSION=2.46.0

# Set the Git version as an environment variable
ENV GIT_VERSION=${GIT_VERSION}

# Set the shell and options per hadolint recommendations
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set the temporary working directory for downloading and building Git
WORKDIR /tmp

# Install dependencies required to build Git from source
# hadolint ignore=DL3008
RUN apt-get update && apt-get install --yes \
    build-essential \
    dh-autoreconf \
    libcurl4-gnutls-dev \
    libexpat1-dev \
    gettext \
    libz-dev \
    libssl-dev \
    curl \
    --no-install-recommends && \
    curl -LO https://github.com/git/git/archive/refs/tags/v${GIT_VERSION}.tar.gz && \
    tar -zxf v${GIT_VERSION}.tar.gz && \ 
    rm -rf /var/lib/apt/lists/*

# Change to the Git source directory to build and install Git
WORKDIR /tmp/git-${GIT_VERSION}

RUN make prefix=/usr/local all && \
    make prefix=/usr/local install

# Reset to the root directory
WORKDIR /

# Set the shell and options in each FROM section per hadolint recommendations
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# App-specific constants
ENV USERNAME leaf-ai
ENV APP_HOME /usr/local/${USERNAME}
ENV APP_SOURCE ${APP_HOME}/myapp
ENV PIP3_VERSION 23.3.1

# Explicitly get the desired pip version
RUN pip3 install --upgrade pip==${PIP3_VERSION} --no-cache-dir

COPY ./requirements.txt ${APP_SOURCE}/requirements.txt
RUN pip install --prefix=/install --no-cache-dir -r ${APP_SOURCE}/requirements.txt

# The id with_creds_requirements refers to our requirements.txt file re-written with
# the necessary credential. That file is mounted in the codefresh docker build
# step. By not supplying a dst, we use dockers default secret location
# of /runs/secrets/<id>
#
# This Dockerfile for the Data Profiling service does not need:
#   kserve
#   tensorflow
# ... which drags in a lot of extra unnecessary stuff for the Data Profiling
# service and as of 3/01/2022 also drags in some dependency conflicts which are
# resolved differently for services that require kserve. Among these conflicts:
#   numpy

# We use a modified requirements file as a Docker secret,
# but we must break the docker cache in the event the
# requirements change. So copy in the unmodified file
# before using the secret.
COPY ./requirements-private.txt ${APP_SOURCE}/requirements-private.txt
RUN --mount=type=secret,id=with_creds_requirements \
    pip install --prefix=/install --no-cache-dir -r /run/secrets/with_creds_requirements

# Stage 2: Final Stage - Use a slim Python image
FROM python:3.10-slim AS final

# Set the shell and options in each FROM section per hadolint recommendations
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# App-specific constants
ENV USERNAME leaf-ai
ENV APP_HOME /usr/local/${USERNAME}
ENV APP_SOURCE ${APP_HOME}/myapp

# Set up user for app running in container
RUN \
    useradd -ms /bin/bash -d ${APP_HOME} -u 1001 ${USERNAME} \
    && echo ${USERNAME}:pw | chpasswd \
    && mkdir -p ${APP_HOME}/.ssh \
    && chown -R ${USERNAME}: ${APP_HOME} \
    && chown -R ${USERNAME}: /usr/local/ \
    && chown -R ${USERNAME}: /var/log

# Set up a place for the mount of secrets to happen
RUN mkdir -p ${APP_HOME}/certs/aws \
    && ln -s ${APP_HOME}/certs/aws ${APP_HOME}/.aws

# This is the port the service will accept requests on
# This should be consistent with the main port for the service as described
# in the <service>.yaml file
# This port number is also mentioned as DecisionAssistantSession.DEFAULT_PORT
EXPOSE 30011

# MD server
EXPOSE 30001

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code and necessary files
COPY ./neuro_san ${APP_SOURCE}/neuro_san

# Set up the entry point for when the container is run
USER ${USERNAME}
WORKDIR ${APP_SOURCE}

ENV APP_ENTRYPOINT neuro_san/deploy/entrypoint.sh

# Tool registry file environment variable
ENV TOOL_REGISTRY_FILE=${TOOL_REGISTRY_FILE}
ENV AGENT_SERVICE_LOG_JSON=${APP_SOURCE}/neuro_san/deploy/logging.json

ENTRYPOINT "${APP_SOURCE}/${APP_ENTRYPOINT}" --tool_registry_file="${TOOL_REGISTRY_FILE}"

