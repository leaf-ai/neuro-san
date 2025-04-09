# Setup your virtual environment

## Install Python dependencies

From the project top-level:

Set PYTHONPATH environment variable

    export PYTHONPATH=$(pwd)

Create and activate a new virtual environment:

    python3 -m venv venv
    . ./venv/bin/activate

Install packages specified in the following requirments files:

    pip install -r requirements.txt
    pip install -r requirements-build.txt

Most common:
If the dependency wheel files are available, install the wheel files for leaf-common
and leaf-server-common:

    pip install leaf-common.whl
    pip install leaf-server-common.whl

Less common:
If they are directly available via git, install the semi-private libraries
(like leaf-common and leaf-server-common):

    export LEAF_SOURCE_CREDENTIALS=<Your GitHub Personal Access Token>
    export LEAF_PRIVATE_SOURCE_CREDENTIALS=<Your GitHub Personal Access Token>
    pip install -r requirements-private.txt

## Set necessary environment variables

In a terminal window, set at least these environment variables:

    export OPENAI_API_KEY="XXX_YOUR_OPENAI_API_KEY_HERE"

Any other API key environment variables for other LLM provider(s) also need to be set if you are using them.
