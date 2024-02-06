import click
import time
from datetime import date, timedelta

from toolhub.demo import utils
from toolhub.lib import auth
from toolhub.lib import hub
from toolhub.lib import registry
from toolhub.openai import assistant_utils
from toolhub.openai import openai_assistant_hub


_ASSISTANT_NAME = "Toolhub Example Assistant"
_GPT_MODEL = "gpt-4-1106-preview"
_INSTRUCTIONS = "You are a helpful assistant who uses tools to perform tasks."


_MAX_TOOL_ITERATIONS = 7

_TERMINAL_RUN_STATUSES = (
    "cancelled",
    "failed",
    "completed",
    "expired",
)
_REQUIRES_ACTION_RUN_STATUS = "requires_action"
_WAITING_RUN_STATUSES = (
    "queued",
    "in_progress",
    "cancelling",
)

_MAX_POLL_ITERATIONS = 5
_POLL_BASE_INTERVAL = timedelta(seconds=2)
_POLL_MULTIPLIER = 2


class Agent:
    def __init__(
        self,
        registry_: registry.Registry,
        assistant_id: str | None = None,
    ):
        self.hub = openai_assistant_hub.OpenAIAssistantHub(registry_=registry_)
        self.client = utils.openai_client()

        if assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id)
        elif assistant := assistant_utils.retrieve_by_name(
            self.client, _ASSISTANT_NAME
        ):
            self.assistant = assistant
        else:
            self.assistant = self.client.beta.assistants.create(
                name=_ASSISTANT_NAME,
                instructions=_INSTRUCTIONS,
                model=_GPT_MODEL,
            )

    def __call__(
        self,
        auth_ctx: auth.AuthContext,
        task: str,
    ) -> None:
        thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Today is {date.today()}",
        )
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=task,
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            tools=self.hub.tools_spec(),
        )
        run_id = run.id

        for _ in range(_MAX_TOOL_ITERATIONS):
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run_id
            )
            if run.status in _TERMINAL_RUN_STATUSES:
                break
            if run.status == _REQUIRES_ACTION_RUN_STATUS and (
                tool_calls := run.required_action.submit_tool_outputs.tool_calls
            ):
                tool_outputs = []
                print_str = "tool calls:\n"
                for tc, result in zip(
                    tool_calls, self.hub.call_tools(auth_ctx, tool_calls)
                ):
                    if isinstance(result, hub.ToolCallErrors):
                        errors_fmt = "\n".join(str(e) for e in result.errors)
                        output = openai_assistant_hub.ToolOutput(
                            tool_call_id=tc.id,
                            output=f"Failure:\n{errors_fmt}",
                        )
                    else:
                        output = result
                    tool_outputs.append(output)
                    print_str += f"{tc.function}\n>\t{repr(output['output'])}\n"

                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run_id,
                    tool_outputs=tool_outputs,
                )
                print(print_str)
            else:
                assert run.status in _WAITING_RUN_STATUSES
                for p in range(_MAX_POLL_ITERATIONS):
                    time.sleep(_POLL_BASE_INTERVAL.seconds * _POLL_MULTIPLIER**p)
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run_id
                    )
                    if run.status not in _WAITING_RUN_STATUSES:
                        break

        print(
            "\n".join(
                str(m)
                for m in reversed(
                    list(self.client.beta.threads.messages.list(thread_id=thread.id))
                )
            )
        )


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
