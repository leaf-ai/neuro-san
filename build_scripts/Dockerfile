# Base image
FROM python:3.10-slim

##############################################################
#			Basic Housekeeping
##############################################################
LABEL maintainer=donn.goodhew@cognizant.com
ENV LANG C.UTF-8
ENV PYTHON_VERSION 3.10
ENV PIP3_VERSION 24.0
ENV DEBIAN_FRONTEND noninteractive

# Debian basics
RUN apt-get update -y
RUN apt-get install curl git -y

# Install shellcheck test utility.
# Get all our apt-get installs out of the way early
RUN apt-get install shellcheck -y

# Change EXTERNAL_BUILD_ROOT to . if debugging locally
ENV EXTERNAL_BUILD_ROOT .

ARG USERNAME=leaf
RUN  adduser --disabled-password --gecos '' ${USERNAME}

# The APP_HOME home is our root directory within the image
# where we place the repo's source directory.
ARG APP_HOME=/home/${USERNAME}

ENV OUR_VENV ${APP_HOME}/venv/python-${PYTHON_VERSION}
ENV PATH="$OUR_VENV/bin:$PATH"

# Make directories as needed
RUN mkdir -p ${APP_HOME}

# Set up python and pip
RUN python${PYTHON_VERSION} -m venv $OUR_VENV
RUN pip3 install --upgrade pip==${PIP3_VERSION} \
    && pip3 install wheel \
                    virtualenv

ARG REPO
ARG APP_SOURCE=${APP_HOME}/${REPO}
RUN mkdir -p ${APP_SOURCE}

# Now bring all of our requirement files in and pip install as needed.
# Create a separate layer for each of the requirements files for maximum
# caching performance. Ordered by general frequency of change, least-to-most.
# We use A COPY step before the pip install in the RUN step so that requirements
# only changes cause a proper container rebuild.
COPY --chown=${USERNAME}:${USERNAME} ${EXTERNAL_BUILD_ROOT}/requirements-build.txt ${APP_SOURCE}
RUN /bin/bash -c "pip3 install -r ${APP_SOURCE}/requirements-build.txt"

COPY --chown=${USERNAME}:${USERNAME} ${EXTERNAL_BUILD_ROOT}/requirements.txt ${APP_SOURCE}
RUN /bin/bash -c "pip3 install -r ${APP_SOURCE}/requirements.txt"

# Use the with_creds_requirements secret as the basis for the pip install
# of the main requirements.  We still do the COPY first so the container
# cache is properly broken on changes.
#
# NOTE: We expect the with_creds_requirement file to provide us with
#       ephemeral GitHub creds from vault as the proper replacement mechanism
#       for LEAF_SOURCE_CREDENTIALS.  This way, it's OK if these inherently
#       short-lived happen to be stored in the container.
COPY --chown=${USERNAME}:${USERNAME}  ${EXTERNAL_BUILD_ROOT}/requirements-private.txt ${APP_SOURCE}
RUN --mount=type=secret,id=with_creds_requirements \
    /bin/bash -c "pip3 install -r <(cat /run/secrets/with_creds_requirements)"

# Now we copy the full source tree into the container, which will almost always
# in practice break the cache since we build when code changes.
# We do this after all the requirements are installed as code changes more often than requirements
COPY --chown=${USERNAME}:${USERNAME} . ${APP_SOURCE}

# Generate any grc
USER ${USERNAME}
RUN cd ${APP_SOURCE} ; ./neuro_san/api/scripts/do_generate.sh

WORKDIR ${APP_HOME}
