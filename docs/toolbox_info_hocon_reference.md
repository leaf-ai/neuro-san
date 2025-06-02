# Toolbox Info HOCON File Reference

This document describes the specifications for the `toolbox_info.hocon` file used in the **neuro-san** system. This file allows you to extend or override the default tools shipped with the `neuro-san` library.

The **neuro-san** system uses the HOCON (Human-Optimized Config Object Notation) format for data-driven configuration. HOCON is similar to JSON but includes enhancements such as comments and more concise syntax. You can explore the HOCON specification [here](https://github.com/lightbend/config/blob/main/HOCON.md) for further details.

Specifications in this document are organized hierarchically, with header levels indicating the nesting depth of dictionary keys. For dictionary-type values, their sub-keys will be described in the next heading level.

<!--TOC-->

- [Toolbox Info HOCON File Reference](#toolbox-info-hocon-file-reference)
    - [Toolbox Info Specifications](#toolbox-info-specifications)
        - [Default Supported Tools](#default-supported-tools)
            - [Langchain Tools](#langchain-tools)
            - [Coded Tools](#coded-tools)
    - [Tool Definition Schema](#tool-definition-schema)
        - [Langchain Tools](#langchain-tools-1)
            - [class](#class)
            - [args](#args)
            - [base_tool_info_url](#base_tool_info_url-optional)
            - [display_as](#display_as-optional)
        - [Coded Tools](#coded-tools-1)
            - [class](#class-1)
            - [description](#description)
            - [parameters](#parameters-optional)
            - [display_as](#display_as-optional-1)
    - [Extending Toolbox Info](#extending-toolbox-info)

<!--TOC-->

---

## Toolbox Info Specifications

The default configuration file used by the system is:
[toolbox_info.hocon](../neuro_san/internals/run_context/langchain/toolbox_info.hocon).

This file defines all tools that the system can recognize. Currently supported tool types include:

- **Langchain tools** (based on `langchain` library)
- **Coded tools** (custom Python tools)

### Default Supported Tools

#### Langchain Tools

- **Search Tools:**
  - `bing_search`: Uses `BingSearchResults` to perform Bing queries.
  - `tavily_search`: Uses `TavilySearchResults` to perform Tavily queries.

- **HTTP Request Tools**:
  - `requests_get`: Sends GET requests.
  - `requests_post`: Sends POST requests.
  - `requests_patch`: Sends PATCH requests.
  - `requests_put`: Sends PUT requests.
  - `requests_delete`: Sends DELETE requests.
  - `requests_toolkit`: A wrapper for all the above request methods.

#### Coded Tools

- `website_search`: Performs DuckDuckGo-based internet search.
- `rag_retriever`: Performs retrieval-augmented generation (RAG) over given URLs.

---

## Tool Definition Schema

Each top-level key in the `toolbox_info.hocon` file represents a usable tool name. These names can be referenced in the agent network’s [`toolbox`](./agent_hocon_reference.md#toolbox).

The value for each key is a dictionary describing the tool's properties. The schema differs slightly between `langchain tools` and `coded tools`, as detailed below.

### Langchain Tools
These tools extend from the Langchain's `BaseTool` class.
- #### `class`
    Fully qualified class name of the tool. It must exist in the server's `PYTHONPATH`. 

    Example:
    ```json
        "class": "langchain_community.tools.bing_search.BingSearchResults"
    ```

    If the class is a Langchain **toolkit** (such as `RequestsToolkit`), it must implement a `get_tools()` method. When instantiated, the toolkit returns a list of individual tools via this method — each of which will be available for the agent to call.

- #### `args`
    A dictionary of arguments for tool initialization. 
    
    Example:
    ```json
    "args": {
        "max_results": 5
    }
    ```

    May include nested configurations.
    Example:
    ```json
    "args": {
        "api_wrapper": {
            "class": "langchain_community.utilities.BingSearchAPIWrapper",
            "args": {
                "k": 3
            }
        }
    }
    ```
    This instantiates `BingSearchResults(api_wrapper=BingSearchAPIWrapper(k=3))`

- #### `base_tool_info_url` *(optional)*
    Reference URL pointing to Langchain’s documentation for the specific tool.

- #### `display_as` *(optional)*
    Display type for clients. Options:
  - `"coded_tool"`
  - `"external_agent"`
  - `"langchain_tool"` (default)
  - `"llm_agent"`
    
  If not provided, the tool is inferred as `"langchain_tool"` unless it contains a [`description`](#coded-description).

### Coded Tools
These tools extend from the `CodedTool` class.

- #### [`class`](./agent_hocon_reference.md#class)
    Fully qualified class name in the format `tool_module.ToolClass`. The `class` must point to a module available in your `AGENT_TOOL_PATH` and server `PYTHONPATH`.

    Example:
    ```json
    "class": "web_search.WebSearch"
    ```

- #### [`description`](./agent_hocon_reference.md#description)
    A plain-language explanation of the tool’s behavior. This is essential for agents to understand how and when to use the tool.

- #### [`parameters`](./agent_hocon_reference.md#parameters) *(optional)*
    JSON schema-like structure describing the expected input arguments, types, and which are required.

    Example:
    ```json
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        },
        "required": ["query"]
    }
    ```

- #### `display_as` *(optional)*
    Display type for clients. Options:
  - `"coded_tool"` (default)
  - `"external_agent"`
  - `"langchain_tool"`
  - `"llm_agent"`

  If omitted, tools with a `description` are treated as `"coded_tool"`; otherwise, `"langchain_tool"`.

---

## Extending Toolbox Info

To add or override tools in the system, you can supply your own `toolbox_info.hocon` file and specify its path via the environment variable:

```bash
AGENT_TOOLBOX_INFO_FILE=/path/to/your/toolbox_info.hocon
```
This allows you to customize the set of available tools without modifying the built-in configuration.
