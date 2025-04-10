
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
# This Dockerfile is expected to be run from the top-level of neuro-san.

# Stage 1: Builder Stage - Use our python and git base image for installations
# Set python image as base image
FROM python:3.12-slim as builder

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

# App-specific constants
ENV USERNAME leaf-ai
ENV APP_HOME /usr/local/${USERNAME}
ENV APP_SOURCE ${APP_HOME}/myapp
ENV PIP3_VERSION 25.0.1

# Explicitly get the desired pip version
RUN pip3 install --upgrade pip==${PIP3_VERSION} --no-cache-dir

COPY ./requirements.txt ${APP_SOURCE}
RUN pip install --prefix=/install --no-cache-dir -r ${APP_SOURCE}/requirements.txt
COPY ./requirements-private.txt ${APP_SOURCE}
RUN pip install --prefix=/install --no-cache-dir -r ${APP_SOURCE}/requirements-private.txt

# Stage 2: Final Stage - Use a slim Python image
FROM python:3.12-slim AS final

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

# This is the port the service will accept grpc requests on.
# This should be consistent with the main port for the service as described
# in the <service>.yaml file
# This port number is also mentioned as AGENT_PORT below
# and ServiceAgentSession.DEFAULT_PORT
# In order to be self-discovered by supporting build/run scripts this must
# be the first port exposed in the Dockerfile.
EXPOSE 30011

# This is the port the service will accept http requests on.
# This should be consistent with the main port for the service as described
# in the <service>.yaml file
# This port number is also mentioned as AGENT_HTTP_PORT below
# and ServiceAgentSession.DEFAULT_HTTP_PORT
EXPOSE 8080

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code and necessary files
COPY ./neuro_san ${APP_SOURCE}/neuro_san
RUN chmod -R a+r ${APP_SOURCE}

# Set up the entry point for when the container is run
USER ${USERNAME}
WORKDIR ${APP_SOURCE}

ENV APP_ENTRYPOINT neuro_san/deploy/entrypoint.sh

#
# Server configuration
#

# Where to find the tool registry manifest file which lists all the agent hocon
# files to serve up from this server instance.
ENV AGENT_MANIFEST_FILE=${APP_SOURCE}/neuro_san/registries/manifest.hocon

# An llm_info hocon file with user-provided llm descriptions that are to be used
# in addition to the neuro-san defaults.
ENV AGENT_LLM_INFO_FILE=""

# Where to find the classes for CodedTool class implementations
# that are used by specific agent networks.
ENV AGENT_TOOL_PATH=${APP_SOURCE}/neuro_san/coded_tools

# Where to find the configuration file for Python logging.
# See https://docs.python.org/3/library/logging.config.html#dictionary-schema-details
# as to how this file can be configured for your own needs.  Examples there are provided in YAML,
# but these can be easily translated to JSON (which we prefer).
ENV AGENT_SERVICE_LOG_JSON=${APP_SOURCE}/neuro_san/deploy/logging.json

# Threshold for logging.
# See https://docs.python.org/3/library/logging.html#logging.Handler.setLevel
# and https://docs.python.org/3/library/logging.html#logging-levels for details.
ENV AGENT_SERVICE_LOG_LEVEL="DEBUG"

# The name of the service for health reporting purposes
ENV AGENT_SERVER_NAME="neuro-san.Agent"

# Name of the service as seen in logs
ENV AGENT_SERVER_NAME_FOR_LOGS="Agent Server"

# A space-delimited list of http metadata request keys to forward to logs/other requests
# Note that any metadata key needs to be all lowercase.
ENV AGENT_FORWARDED_REQUEST_METADATA="request_id user_id"

# Port number for the grpc service endpoint
ENV AGENT_PORT=30011

# Port number for http service endpoint
# If you are changing this, you should also change the first EXPOSE port above
ENV AGENT_HTTP_PORT=8080

# Maximm number of requests that can be served at the same time
# If you are changing this, you should also change the second EXPOSE port above
ENV AGENT_MAX_CONCURRENT_REQUESTS 10

# Number of requests served before the server shuts down in an orderly fashion.
# This is useful for testing response handling in clusters with duplicated pods.
ENV AGENT_REQUEST_LIMIT=1000000

ENTRYPOINT "${APP_SOURCE}/${APP_ENTRYPOINT}"

