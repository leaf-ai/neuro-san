# LLM Info HOCON File Reference

This document describes the neuro-san specifications for the test case .hocon files
found within this repo under the [tests/fixtures](../tests/fixtures) section of this repo.

The neuro-san system uses the HOCON (Human-Optimized Config Object Notation) file format
for its data-driven configuration elements.  Very simply put, you can think of
.hocon files as JSON files that allow comments, but there is more to the hocon
format than that which you can explore on your own.

Specifications in this document each have header changes for the depth of scope of the dictionary
header they pertain to.
Some key descriptions refer to values that are dictionaries.
Sub-keys to those dictionaries will be described in the next-level down heading scope from their parent.

## Data-Driven Test Case Specifications

### agent

The value gives the string name of the agent to be tested.

While all agents are named according to the filename of their agent network hocon file,
this value should only be the stem of that file.

### connections

Single string values can be:

| connection type | meanining |
|:----------------|:----------|
| direct (default)| Connect directly to the agent via a neuro-san library call. No server required. |
| http  |  Connect to the agent via a server via http |
| grpc  |  Connect to the agent via a server via gRPC |
| https |  Connect to the agent via a server via gRPC |


Note that it is possible to specify a list of connection types for the same test case.
If this is the case, the test driver will conduct the same test via each connection type.

Example of a list:

```
    ...
    "connections": [ "direct", "http", "grpc" ]
    ...
```

Currently, only testing against a locally running server is supported.

### success_ratio

A string value that represents the fraction of test attempts that need to succeed
in order to call the test passing.

The big idea here is that this is an acknowledgement of the realities of working with LLMs:
* agents do not always do what you want them to
* getting agents to give you correct output given existing prompts and a prticular input is fundamentally an optimization exercise against the prompts themselves.

The denominator (bottom) of the fraction is an integer indicating how many test samples (repeat iterations)
should be attempted.

The numerator (top) of the fraction is an integer indicating how many of those test samples
need to execute without failure in order to call the test "passing" within a unit test infrastructure
that needs some kind of boolean assessment.

When using the (Assessor)[../neuro_san/test/assessor/assessor.py] tool to categorize modes of failure,
the denominator here is also used as the indication of how many test samples should be taken.

By default this value is "1/1" indicating that the test case will only run once,
and that single test sample *must* pass in order to "pass".  This is in keeping with
standard expectations w/ non-statistically-oriented tests.

### use_direct
### metadata
### interactions
#### text
#### sly_data
#### response
##### text
####### tests
######## value/not_value
######## less/not_less
######## greater/not_greater
######## keywords/not_keywords
######## gist/not_gist
##### sly_data
#### chat_filter
#### continue_conversation
