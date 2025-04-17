# Setup your virtual environment

## Install Python dependencies

From the project top-level:

Set PYTHONPATH environment variable

    export PYTHONPATH=$(pwd)

Create and activate a new virtual environment:

    python3 -m venv venv
    . ./venv/bin/activate

Install packages specified in the following requirements files:

    pip install -r requirements.txt
    pip install -r requirements-build.txt

## Set necessary environment variables

In a terminal window, set at least these environment variables:

    export OPENAI_API_KEY="XXX_YOUR_OPENAI_API_KEY_HERE"

Any other API key environment variables for other LLM provider(s) also need to be set if you are using them.
