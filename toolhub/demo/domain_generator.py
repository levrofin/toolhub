import click

import openai

from toolhub.demo import openai_assistant
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider


_OPENAI_KEY = ""  # replace with your OpenAI API key"
_RAPIDAPI_KEY = ""  # Your RAPIDAPI_KEY


def _run(query: str):
    registry_ = registry.Registry(
        [
            openapi_provider.Provider.standard(),
            rapidapi_provider.Provider.standard(
                filter_rapidapi_endpoint_urls=[
                    "https://domain-checker7.p.rapidapi.com/whois",  # Domain checker,
                ],
            ),
        ],
    )
    agent = openai_assistant.Agent(
        registry_=registry_, openai_client=openai.OpenAI(api_key=_OPENAI_KEY)
    )
    auth_ctx = auth.StandardAuthContext(
        rapidapi=auth.RapidApiAuthContext(
            rapidapi_key=_RAPIDAPI_KEY,
        )
    )
    agent(auth_ctx, query)


@click.command()
@click.option("--task", required=False)
def run(task: str | None) -> None:
    if not task:
        task = "Generate 5 domain names for a startup that creates meal plans for exotic animals and check to see if they are available"
        _run(task)


if __name__ == "__main__":
    run()
