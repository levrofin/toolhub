import click

from toolhub.demo import openai_assistant
from toolhub.demo import utils
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider


def _run(query: str):
    registry_ = registry.Registry(
        [
            openapi_provider.Provider.standard(),
            rapidapi_provider.Provider.standard(
                filter_rapidapi_endpoint_urls=[
                    "https://email-checker.p.rapidapi.com/verify/v1",  # Email verifier,
                    "https://apollo-io1.p.rapidapi.com/search_people",  # People Search,
                ],
            ),
        ],
        filter_collections=["crunchbase"],
    )
    agent = openai_assistant.Agent(registry_=registry_)
    agent(utils.auth_ctx(), query)


@click.command()
@click.option("--task", required=False)
def run(task: str | None) -> None:
    if not task:
        task = (
            "Please make a list of emails for CFOs at three 5000+ employee companies in the US.\n"
            "Make sure their emails are valid."
        )
        _run(task)


if __name__ == "__main__":
    run()
