import click

import openai

from toolhub.demo import openai_assistant
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.rapidapi import provider as rapidapi_provider


_OPENAI_KEY = ''  # replace with your OpenAI API key"
_RAPIDAPI_KEY = "" # Your RAPIDAPI_KEY

def _run(query: str):
    registry_ = registry.Registry([
            rapidapi_provider.Provider.standard(
                filter_rapidapi_endpoint_urls=[
                    "https://local-business-data.p.rapidapi.com/business-details",
                    'https://local-business-data.p.rapidapi.com/search',
                ],
            ),
        ],
    )
    agent = openai_assistant.Agent(registry_=registry_, openai_client=openai.OpenAI(api_key=_OPENAI_KEY))
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
        task = "Can you find 10 dentists in San Francisco, and give me the contact details of the most highly rated one?"
        _run(task)


if __name__ == "__main__":
    run()
