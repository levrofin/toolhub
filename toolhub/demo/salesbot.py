import click

import openai

from toolhub.demo import openai_assistant
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider

_ENDPOINT_URLS = [
  'https://email-checker.p.rapidapi.com/verify/v1', # Email verifier,
  'https://apollo-io1.p.rapidapi.com/search_people', # People Search,
]

_COLLECTIONS = ['crunchbase']

_OPENAI_KEY = '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'  # replace with your OpenAI API key"
_RAPIDAPI_KEY = "60fb5f82ffmsh9e37b31665092afp190901jsn136fc839ec0a" # Your RAPIDAPI_KEY
_CRUNCHBASE_KEY = "2b25cbc765971f2b362adaf8ae79e1fa" # Your CRUNCHBASE_KEY


def _run(query: str):
    registry_ = registry.Registry(
        [
            openapi_provider.Provider.standard(),
            rapidapi_provider.Provider.standard(
                filter_rapidapi_endpoint_urls=[
                    "https://local-business-data.p.rapidapi.com/business-details",  # Email verifier,
                    'https://local-business-data.p.rapidapi.com/search', # SendGrid,
                ],
            ),
        ],
        # filter_collections=["crunchbase"],
    )
    agent = openai_assistant.Agent(registry_=registry_, openai_client=openai.OpenAI(api_key=_OPENAI_KEY))
    auth_ctx = auth.StandardAuthContext(
        openapi=auth.OpenApiAuthContext(
            api_to_headers={"crunchbase": {"X-cb-user-key": _CRUNCHBASE_KEY}}
        ),
        rapidapi=auth.RapidApiAuthContext(
            rapidapi_key=_RAPIDAPI_KEY,
        ))
    agent(auth_ctx, query)


@click.command()
@click.option("--task", required=False)
def run(task: str | None) -> None:
    if not task:
        task = "Can you find the email address for 5 web design agencies in New York City?"
        _run(task)


if __name__ == "__main__":
    run()
