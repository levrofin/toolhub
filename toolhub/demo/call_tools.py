from openai.types.beta.threads.required_action_function_tool_call import (
    Function,
    RequiredActionFunctionToolCall,
)

from toolhub.demo import utils
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider
from toolhub.standard_providers import random_provider
from toolhub.lib import hub
from toolhub.lib import registry
from toolhub.openai import openai_assistant_hub


if __name__ == "__main__":
    # NOTE: specify credentials in toolhub/demo/utils.py.
    hub_ = openai_assistant_hub.OpenAIAssistantHub(
        registry_=registry.Registry(
            [
                random_provider.Provider(),
                openapi_provider.Provider.standard(),
                rapidapi_provider.Provider.standard(
                    filter_rapidapi_api_hostnames=[
                        "https://currency-converter18.p.rapidapi.com"
                    ],
                    filter_rapidapi_endpoint_urls=[
                        "https://currency-converter18.p.rapidapi.com/api/v1/convert"
                    ],
                ),
            ],
            filter_collections=[
                "random",
                "crunchbase",
                "Financial.currency_converter_v2",
            ],
        )
    )
    tool_calls = [
        RequiredActionFunctionToolCall(
            id="tool_call_1",
            type="function",
            function=Function(
                name="random_string",
                arguments='{"length":"15","charset":"abcdef"}',
            ),
        ),
        RequiredActionFunctionToolCall(
            id="tool_call_2",
            type="function",
            function=Function(
                name="crunchbase_autocompletes_get",
                arguments='{"query": "Levro"}',
            ),
        ),
        RequiredActionFunctionToolCall(
            id="tool_call_3",
            type="function",
            function=Function(
                name="Financial-currency_converter_v2-convert",
                arguments='{"from":"MXN","amount":100,"to":"USD"}',
            ),
        ),
    ]
    for tc, output in zip(tool_calls, hub_.call_tools(utils.auth_ctx(), tool_calls)):
        print(
            f"{tc.id}:"
            "\n"
            f"{output.errors if isinstance(output, hub.ToolCallErrors) else output['output']}"
            "\n"
        )
