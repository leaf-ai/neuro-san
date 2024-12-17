
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

# Set the shell and options per hadolint recommendations
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Reset to the root directory
WORKDIR /

# App-specific constants
ENV USERNAME neuro-san
ENV APP_HOME /usr/local/${USERNAME}
ENV APP_SOURCE ${APP_HOME}/myapp
ENV PIP3_VERSION 23.3.1

# Explicitly get the desired pip version
RUN pip3 install --upgrade pip==${PIP3_VERSION} --no-cache-dir

# Uncomment this line if you have local requirements.txt for your coded tools
# COPY ./requirements.txt ${APP_SOURCE}/requirements.txt
# RUN pip install --prefix=/install --no-cache-dir -r ${APP_SOURCE}/requirements.txt

# Copy in the wheel files to include in the Dockerfile
ENV WHEEL_DIR .requirements-wheels
COPY ./${WHEEL_DIR} ${APP_SOURCE}/${WHEEL_DIR}
RUN pip install --prefix=/install --no-cache-dir ${APP_SOURCE}/${WHEEL_DIR}/*.whl

# Stage 2: Final Stage - Use a slim Python image
FROM python:3.10-slim AS final

# Set the shell and options in each FROM section per hadolint recommendations
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set up user for app running in container
ENV USERNAME neuro-san
ENV APP_HOME /usr/local/${USERNAME}
ENV APP_SOURCE ${APP_HOME}/myapp

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
# This port number is also mentioned as ServiceAgentSession.DEFAULT_PORT
# In order to be self-discovered by supporting build/run scripts this must
# be the first port exposed in the Dockerfile.
EXPOSE 30011

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code and necessary files
# Note: The registries directory where agent definitions live is mandatory
#       The coded_tools directory where agent code lives is optional
COPY ./registries ./coded_tools* ${APP_SOURCE}

# Set up the entry point for when the container is run
USER ${USERNAME}
WORKDIR ${APP_SOURCE}

# RUN echo "$(pip show neuro-san | grep Location | awk '{print $2}')"
# This value below comes from the above RUN command. Cannot set ENV vars in Dockerfiles based on shell output.
ENV PACKAGE_INSTALL /usr/local/lib/python3.10/site-packages
ENV PACKAGE_DEPLOY ${PACKAGE_INSTALL}/neuro_san/deploy
ENV APP_ENTRYPOINT ${PACKAGE_DEPLOY}/entrypoint.sh

# Tool registry file environment variable
ENV AGENT_MANIFEST_FILE=${APP_SOURCE}/registries/manifest.hocon
ENV TOOL_REGISTRY_FILE=${TOOL_REGISTRY_FILE}
ENV AGENT_SERVICE_LOG_JSON=${PACKAGE_DEPLOY}/logging.json

ENTRYPOINT "${APP_ENTRYPOINT}" --tool_registry_file="${TOOL_REGISTRY_FILE}"

