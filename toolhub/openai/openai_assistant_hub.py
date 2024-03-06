from typing import Generic

from openai.types.beta.threads.required_action_function_tool_call import (
    RequiredActionFunctionToolCall,
)
from openai.types.beta.threads.run_submit_tool_outputs_params import (
    ToolOutput,
)
from openai.types.beta.assistant_create_params import ToolAssistantToolsFunction

from toolhub.lib import hub
from toolhub.openai import utils


class OpenAIAssistantHub(
    Generic[hub.AuthContext],
    hub.Hub[
        hub.AuthContext,
        list[ToolAssistantToolsFunction],
        RequiredActionFunctionToolCall,
        ToolOutput,
    ],
):
    def tools_spec(self) -> list[ToolAssistantToolsFunction]:
        return [
            dict(type="function", function=fn_def)
            for fn_def in utils.fns_to_fn_defs(self.registry_.list_())
        ]

    def call_tools(
        self,
        auth_ctx: hub.AuthContext,
        calls: list[RequiredActionFunctionToolCall],
    ) -> list[ToolOutput | hub.ToolCallErrors]:
        typed_results = []
        for call in calls:
            fn = self.registry_.get(call.function.name)
            result = utils.call_fn_from_openai(auth_ctx, fn, call.function.arguments)
            if isinstance(result, str):
                typed_result = ToolOutput(tool_call_id=call.id, output=result)
            else:
                assert isinstance(result, list)
                for e in result:
                    assert isinstance(e, Exception)
                typed_result = hub.ToolCallErrors(result)
            typed_results.append(typed_result)
        return typed_results
