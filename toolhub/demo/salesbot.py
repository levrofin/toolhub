import click

from toolhub.demo import openai_assistant
from toolhub.lib import registry, auth

_ENDPOINT_URLS = [
    "https://email-checker.p.rapidapi.com/verify/v1",  # Email verifier,
    "https://apollo-io1.p.rapidapi.com/search_people",  # People Search,
]

_COLLECTIONS = ["crunchbase"]

_RAPIDAPI_KEY = ""  # Your RAPIDAPI_KEY
_CRUNCHBASE_KEY = ""  # Your CRUNCHBASE_KEY


def _run(query: str):
    openapi = auth.OpenApiAuthContext(
        api_to_headers={"crunchbase": {"X-cb-user-key": _CRUNCHBASE_KEY}}
    )
    auth_ctx = auth.StandardAuthContext(
        rapidapi=auth.RapidApiAuthContext(rapidapi_key=_RAPIDAPI_KEY), openapi=openapi
    )
    registry_ = registry.Registry.standard(
        filter_collections=_COLLECTIONS,
        filter_rapidapi_api_hostnames=_ENDPOINT_URLS,
    )
    agent = openai_assistant.Agent(registry_=registry_)
    agent(auth_ctx, query)


@click.command()
@click.option("--query", required=False)
def run(
    query: str | None,
) -> None:
    if not query:
        query = "Using function calls, can you get me a list of emails for CFOs at 3 5000+ employee companies in the US? Make sure their emails are valid"
        _run(query)


if __name__ == "__main__":
    run()
