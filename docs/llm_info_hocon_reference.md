# LLM Info HOCON File Reference

This document describes the neuro-san specifications for the llm_info.hocon file
which allows for extending the default descriptions of llms shipped with the neuro-san library.

The neuro-san system uses the HOCON (Human-Optimized Config Object Notation) file format
for its data-driven configuration elements.  Very simply put, you can think of
.hocon files as JSON files that allow comments, but there is more to the hocon
format than that which you can explore on your own.

Specifications in this document each have header changes for the depth of scope of the dictionary
header they pertain to.
Some key descriptions refer to values that are dictionaries.
Sub-keys to those dictionaries will be described in the next-level down heading scope from their parent.

<!--TOC-->

## LLM Info Specifications

All parameters listed here have global scope (to the agent network) and are listed at the top of the file by convention.

### Model Name Keys

Top-level keys in the file correspond to newly defined usable names for models an the agent network's
[llm_config](./agent_hocon_reference.md#model-name).

The value for any model name key is a dictionary describing the model itself, which the next few headings
will describe.

#### class
#### model_info_url
#### modalities
##### input
##### output
#### capabilities
#### context_window_size
#### max_output_tokens
#### knowledge_cutoff

### classes
#### Class Name Keys
##### token_counting
##### extends
##### args

### default_config
