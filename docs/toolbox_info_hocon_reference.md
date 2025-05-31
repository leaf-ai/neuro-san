# Toolbox Info HOCON File Reference

This document describes the specifications for the `toolbox_info.hocon` file used in the **neuro-san** system. This file allows you to extend or override the default tools shipped with the `neuro-san` library.

The **neuro-san** system uses the HOCON (Human-Optimized Config Object Notation) format for data-driven configuration. HOCON is similar to JSON but includes enhancements such as comments and more concise syntax. You can explore the HOCON specification [here](https://github.com/lightbend/config/blob/main/HOCON.md) for further details.

Specifications in this document are organized hierarchically, with header levels indicating the nesting depth of dictionary keys. For dictionary-type values, their sub-keys will be described in the next heading level.

<!--TOC-->

- [Toolbox Info Specifications](#toolbox-info-specifications)
- [Tool Definition Schema](#tool-definition-schema)
  - [Langchain Tools](#langchain-tools)
  - [Coded Tools](#coded-tools)
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

- **HTTP Request Tools** (using `RequestsToolkit` with a `TextRequestsWrapper`):
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

The value for each key is a dictionary describing the tool's properties. The schema differs slightly between `langchain` tools and coded tools, as detailed below.

### Langchain Tools

| Field | Description |
|-------|-------------|
| `class` | Fully qualified class name of the tool. |
| `args` | Dictionary of arguments required for tool initialization. May include nested configurations. |
| `base_tool_info_url` | *(Optional)* URL to reference documentation for the tool. |
| `display_as` | *(Optional)* Display type for the client. Options: `"coded_tool"`, `"external_agent"`, `"langchain_tool"` (default), or `"llm_agent"`. |

### Coded Tools

| Field | Description |
|-------|-------------|
| [`class`](./agent_hocon_reference.md#class) | Fully qualified class name in the format `tool_module.ClassName`. `tool_module` must be in the `AGENT_TOOL_PATH`. |
| [`description`](./agent_hocon_reference.md#description) | Description of when and how to use the tool. |
| [`parameters`](./agent_hocon_reference.md#parameters) | *(Optional)* Details about the tool's parameters. |
| `display_as` | *(Optional)* Display type for the client. Options: `"coded_tool"` (default), `"external_agent"`, `"langchain_tool"`, or `"llm_agent"`. |

---

## Extending Toolbox Info

To add or override tools in the system, you can supply your own `toolbox_info.hocon` file and specify its path via the environment variable:

```bash
AGENT_TOOLBOX_INFO_FILE=/path/to/your/toolbox_info.hocon
```
This allows you to customize the set of available tools without modifying the built-in configuration.
