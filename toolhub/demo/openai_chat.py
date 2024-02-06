import click
from datetime import date
from tenacity import retry, wait_random_exponential, stop_after_attempt

from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import (
    ChatCompletionMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from toolhub.demo import utils
from toolhub.lib import auth
from toolhub.lib import hub
from toolhub.lib import registry
from toolhub.openai import openai_chat_hub


_GPT_MODEL = "gpt-4-1106-preview"
_TEMPERATURE = 0.1

_SYSTEM_MESSAGE = f"You are a helpful assistant.\nToday is {date.today()}"


class Agent:
    def __init__(
        self,
        registry_: registry.Registry,
    ):
        self.hub = openai_chat_hub.OpenAIChatHub(registry_=registry_)
        self.tools = self.hub.tools_spec()

        self.client = utils.openai_client()

        self.messages: list[ChatCompletionMessageParam] = []

    @retry(
        wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(2)
    )
    def _create_chat_completion(self) -> ChatCompletionMessage:
        r = self.client.chat.completions.create(
            model=_GPT_MODEL,
            messages=self.messages,
            tools=self.tools,
            temperature=_TEMPERATURE,
        )
        return r.choices[0].message

    def __call__(
        self,
        auth_ctx: auth.AuthContext,
        task: str,
    ) -> None:
        self.messages += [
            ChatCompletionSystemMessageParam(role="system", content=_SYSTEM_MESSAGE),
            ChatCompletionUserMessageParam(role="user", content=task),
        ]

        assistant_message = self._create_chat_completion()
        assert assistant_message.role == "assistant"
        assert assistant_message.tool_calls, RuntimeError(
            f"chat completion included no tool calls: {assistant_message}"
        )
        self.messages.append(
            ChatCompletionAssistantMessageParam(
                role=assistant_message.role,
                content=assistant_message.content,
                tool_calls=assistant_message.tool_calls,
            )
        )

        tool_calls = assistant_message.tool_calls
        for tc, result in zip(tool_calls, self.hub.call_tools(auth_ctx, tool_calls)):
            if isinstance(result, hub.ToolCallErrors):
                errors_fmt = "\n".join(str(e) for e in result.errors)
                raise RuntimeError(f"Tool call {tc.id} failed: {errors_fmt}")
            self.messages.append(result)

        assistant_message = self._create_chat_completion()
        assert assistant_message.role == "assistant"
        assert not assistant_message.tool_calls, RuntimeError(
            f"chat completion included subsequent tool calls: {assistant_message}"
        )
        self.messages.append(
            ChatCompletionAssistantMessageParam(
                role=assistant_message.role,
                content=assistant_message.content,
            )
        )

        print("\n".join(str(m) for m in self.messages))


@click.command()
@click.option("--task", required=True)
@click.option("--collections", required=False)
@click.option("--rapidapi_api_hostnames", required=False)
@click.option("--rapidapi_endpoint_urls", required=False)
def run(
    task: str,
    collections: str | None,
    rapidapi_api_hostnames: str | None,
    rapidapi_endpoint_urls: str | None,
) -> None:
    # NOTE: specify credentials in toolhub/demo/utils.py.
    Agent(utils.registry_(collections, rapidapi_api_hostnames, rapidapi_endpoint_urls))(
        utils.auth_ctx(), task
    )


if __name__ == "__main__":
    run()
