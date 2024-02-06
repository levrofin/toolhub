# Welcome to ToolHub!

ToolHub is simple library to help your LLMs take API-based actions. This project includes an initial set of tools we provide on RapidAPI, which has over 10,000 APIs that can be accessed, and an interface to support any OpenAPI spec, as well as arbitrary Python functions that can be implemented and called locally.

The core value prop is:

- Ability to call a large number of APIs using RapidAPI; and easily integrate other APIs that have OpenAPI specs - with robust error handling / communication that allows the LLM to retry.
- Easily integrate your own Python or HTTP backends (future support for GraphQL, gRPC, Thrift, etc.).
- Easily switch LLM backends, from OpenAI chat to assistant (future support for Google Gemini, Anthropic Claude, etc.).
- Customizable Auth

Why did we build this instead of just using one of the following?

- [Langchain](https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/tools): requires installation of Python clients (supports [OpenAPI](https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/utilities/openapi.py) but not RapidAPI), not very easy to use.
- [LlamaHub](https://github.com/run-llama/llama-hub): fairly broad support for document readers; does not extend well to reading dynamic content, or writes.
- [ToolBlench](https://github.com/OpenBMB/ToolBench): RapidAPI-only, not very easy to use, not regularly updated or maintained.
- [ChatGPT plugins](https://platform.openai.com/docs/plugins/introduction): plugins are OpenAI-specific, and furthermore are ChatGPT-specific - they are not available to all users via the chat completions or assistant APIs.

# Example Use Cases

## For Fintechs

- Use the Alpha Vantage API to access stock prices ([https://rapidapi.com/danilo.nobrega88/api/alpha-vantage12](https://rapidapi.com/danilo.nobrega88/api/alpha-vantage12))
- Convert currencies ([https://rapidapi.com/principalapis/api/currency-conversion-and-exchange-rates](https://rapidapi.com/principalapis/api/currency-conversion-and-exchange-rates))
- Get the latest tax rates ([https://rapidapi.com/davidrates/api/taxrates-io/](https://rapidapi.com/davidrates/api/taxrates-io/))

## For Marketing and Sales

- Use the business data API to search for target customers ([https://rapidapi.com/letscrape-6bRBa3QguO5/api/local-business-data/](https://rapidapi.com/letscrape-6bRBa3QguO5/api/local-business-data/))
- Connect to Crunchbase for more research on prospects
- Validate email addresses: [https://rapidapi.com/mr_admin/api/email-verifier/](https://rapidapi.com/mr_admin/api/email-verifier/)

## For All Chat bots

- Use a local ‘random’ syscall to enable your LLM to access random numbers
- Use the Google Translate API to get translations ([https://rapidapi.com/googlecloud/api/google-translate1/](https://rapidapi.com/googlecloud/api/google-translate1/))

# Installation!

Toolhub can be installed via pip:

```
pip install toolhub@git+https://github.com/levrofin/toolhub@61b20b5ba283785525640927b6b12911b1dcd836
```

# How to use

The core product of ToolHub is `toolhub.lib.hub::Hub`, which manages a set of available tools.

The key functionalities of a hub are:

1. Prepare a list of the available tools - in a format the LLM API can consume directly.
2. Call one or more tools with arguments, and return the output - both input and output in a format the LLM API can feed/consume directly.

 A hub can be constructed with a standard or curated set of tools using a `toolhub.lib.registry::Registry`. At the moment, the standard tools include 10k+ RapidAPI endpoints, OpenAPI endpoints for select APIs, and select Python functions. A registry can also be constructed simply with custom tools.

At the moment, ToolHub implements hubs for the OpenAI chat completions and assistant APIs (support for other LLM APIs/formats coming soon). Examples of how to a use hub are in `toolhub/demo/openai_chat.py` and `toolhub/demo/openai_assistant.py`.

## Initializing the Hub

### RapidAPI

1. Signup for an account at [rapidapi.com](http://rapidapi.com/), create an application (make sure to create a new App, use RapidAPI type), and get a key for it
2. For any APIs that you wish to use, from the API’s pricing page in RapidAPI, click Subscribe
3. Create a registry object with the set  of tools that you want to support. This can be filtered on  the URL of specific endpoints, or APIs in RapidAPI. Specify the RapidAPI key in the `AuthContext` used to initialize `Hub`: `AuthContext(rapidapi=RapidApiAuthContext(rapidapi_key=<your key>))`

```python
from toolhub.lib import auth
from toolhub.openai import openai_assistant_hub
from toolhub.lib import registry

# A collection of the tools that we want the registry to support.
# For example, this registry supports:
# 1. All Alpha Vantage endpoints, and
# 2. The Yelp business search endpoint.
registry_ = registry.Registry.standard(
	filter_rapidapi_api_hostnames=["https://alpha-vantage12.p.rapidapi.com/"],
  filter_rapidapi_endpoint_urls=["[https://yelp-reviews.p.rapidapi.com/business-search](https://yelp-reviews.p.rapidapi.com/business-search)"],
)

auth_ctx = auth.AuthContext(rapidapi=auth.RapidApiAuthContext(rapidapi_key=<YOUR_KEY>))

hub_ = openai_assistant_hub.OpenAIAssistantHub(
  registry_=registry_,
  auth_ctx=auth_ctx,
)
```

### Local Tools

1. Simply initialize the registry with the tools to be used and pass to the hub. Random is the only one supported today. 
    
    ```python
    from toolhub.lib import auth
    from toolhub.lib import registry
    from toolhub.openai import openai_assistant_hub
    
    hub_ = openai_assistant_hub.OpenAIAssistantHub(
      registry_=registry.Registry.standard(filter_collections=['random']),
    	auth_ctx=auth.AuthContext(),
    )
    ```
    

### OpenAPI

For now, our OSS implementation only supports crunchbase as an example. To use crunchbase,

1. Generate a Crunchbase API key at [https://data.crunchbase.com/docs/crunchbase-basic-getting-started#generating-a-basic-api-key](https://data.crunchbase.com/docs/crunchbase-basic-getting-started#generating-a-basic-api-key).
2. Specify the Crunchbase key in the `AuthContext` used to initialize `Hub`:

```python
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.openai import openai_assistant_hub

auth_ctx = auth.AuthContext(
  openapi=auth.OpenApiAuthContext(
    api_to_headers={
      "crunchbase": {"X-cb-user-key": <crunchbase_key>}
    }
  ),
)

hub_ = openai_assistant_hub.OpenAIAssistantHub(
  registry_=registry.Registry.standard(filter_collections='crunchbase'),
	auth_ctx=auth_ctx,
)
```

Note: the OpenAPI AuthContext above is provided by default in `toolhub/demo/utils.py`.

## Using the hub

From the command line:

```bash
export DYNACONF_OPENAI__API_KEY=<your OpenAI key> # or specify in toolhub/settings.yml:openai.api_key

# Make sure to specify your RapidAPI key (from initializing the hub above) in demo/utils.py

# Convert currencies using RapidAPI; use OpenAI assistant.
python3 toolhub/demo/openai_assistant.py \
--task="Can you convert 100 MXN to USD?" \
--rapidapi_api_hostnames="https://currency-converter18.p.rapidapi.com"

# Generate a random string using Python; use OpenAI chat completions.
# NOTE: this demonstration module supports only a single tool call.
python3 toolhub/demo/openai_chat.py \
--task="Could you generate a random password for me of 15 characters?" \
--collections="random"
```

As a Python library (refer to  toolhub/demo/openai_assistant.py):

```python
# Initialize registry and auth_ctx as above, and set up the Hub.
hub = openai_assistant_hub.OpenAIAssistantHub(
  registry_=registry_, auth_ctx=auth_ctx
)

# Initialize the Open API client and run
client = openai.OpenAI(api_key=settings.openai.api_key)
assistant = client.beta.assistants.create(
	name="ToolHub assistant",
	instructions="You are a helpful assistant who uses tools to perform tasks.",
	tools=hub.tools_spec(), # OpenAI currently supports upto 128 tools
	model="gpt-4-1106-preview",
)
run = client.beta.threads.runs.create(
	thread_id=thread.id,
	assistant_id=assistant.id,
)

...
# Set up any application logic here
...
if (
  run.status == _REQUIRES_ACTION_RUN_STATUS
  and (tool_calls := run.required_action.submit_tool_outputs.tool_calls)
):
  tool_outputs = []
  for tool_call_id, result in hub.call_tools({
      tc.id: tc for tc in tool_calls
	}).items():
    if isinstance(result, hub.ToolCallErrors):
      errors_fmt = "\\n".join(str(e) for e in result.errors)
      tool_outputs.append(
        openai_assistant_hub.ToolOutput(
          tool_call_id=tool_call_id,
          output=f"Failure:\\n{errors_fmt}",
        )
      )
    else:
      tool_outputs.append(result)
      client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run_id,
        tool_outputs=tool_outputs,
      )
```

# Limitations

- Try to restrict the number of functions that you’re providing - adding too many can overwhelm the LLM’s context, and lead to poor results.
    - Filter to only the collections/functions you’d like to use.
- Tools which provide a very large amount of output do not work well, since the model is unable to comprehend the results.
- Calling sequences of events can often fail - the model is sometime not able to perform planning without careful prompting.
- Currently, only RapidAPI GETs are supported - we are actively working on a framework for POSTs as well

Want to overcome these limitations? Check out our premium offering at [https://www.bloomerai.com/](https://www.bloomerai.com/)

# Extend and customize

**Add an OpenAPI API**

We support adding any API defined in the OpenAPI format. Follow these instructions, and please do contribute back!

1. Identify and download the OpenAPI JSON schema to build against.
    1. e.g. [https://api.swaggerhub.com/apis/Crunchbase/crunchbase-enterprise_api/1.0.3](https://api.swaggerhub.com/apis/Crunchbase/crunchbase-enterprise_api/1.0.3)
2. At `toolhub/integrations/openapi/apis/<new_api_name>` , add the JSON schema file and a corresponding Python loader module, e.g. `toolhub/integrations/openapi/apis/crunchbase/crunchbase_v4.json` and `toolhub/integrations/openapi/apis/crunchbase/crunchbase.py`
3. [if you need customization] In the Python loader module, implement a custom `MyParser(parser.Parser)` with `filter_endpoint` (to filter out certain functions) and/or `map_parameter` (to change certain parameters, e.g. updating descriptions).
4. Include the new Python loader module in `toolhub/registration/openapi.py`.
    1. We will revamp this to support easy registration without forking the ToolHub repo.
5. For local development, you could construct a custom `Provider`:
    
    ```python
    from toolhub.integrations.openapi import provider
    from toolhub.lib import registry
    
    # A simple API which doesn't require a custom Parser.
    _API = <new API's name>
    _SCHEMA_PATH = <new API's schema 
    
    _BASE_URL = <new API's base URL>
    simple_api_loader = provider.standard_api_loader(_API, _SCHEMA_PATH, _BASE_URL))
    
    # An API which requires a custom Parser.
    _API = <new API's name>
    _BASE_URL = <new API's base URL>
    custom_api_loader = provider.ApiLoader(
      _API,
      _BASE_URL,
      <custom Parser instance>,
    )
    
    openapi_provider = provider.Provider([
      simple_api_loader,
      custom_api_loader,
    ])
    registry_ = registry.Registry.standard(openapi=openapi_provider)
    ```
    
6. For contributions, add the new API to `toolhub.integrations.openapi.provider::Provider.standard`.
7. Test that the API works end-to-end by adding a tool call to `toolhub/demo/call_tools.py`.

This will enable your LLM to access any APIs, including internal ones.  

**Customize auth**

You can pass custom additional authentication headers via the `AuthContext`

```python
@dataclasses.dataclass
class OpenApiAuthContext:
    api_to_headers: dict[str, dict[str, str]] | None

@dataclasses.dataclass
class RapidApiAuthContext:
    rapidapi_key: str
    host_to_headers: dict[str, dict[str, str]] | None

@dataclasses.dataclass
class AuthContext:
    openapi: OpenApiAuthContext | None
    rapidapi: RapidApiAuthContext | None
```

Note: the `AuthContext` can be also configured without code via [dynaconf](https://www.dynaconf.com/configuration/) (e.g. with `toolhub/settings.yml`) - see `AuthContext.from_settings()`.

# Contributing

We welcome contributions of new functions! Our goal is to help everyone accelerate their AI development timeline. If you found this project helpful for an API that was not covered, pleas feel free to submit a PR and give back!

# Discord

Questions? Concerns? Join our Discord at https://discord.gg/jN5ePfvV