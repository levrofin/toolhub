import click
import pathlib

import openai
import os

from toolhub.demo import openai_assistant
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider

_OPENAI_KEY = ""  # replace with your OpenAI API key"
_RAPIDAPI_KEY = ""  # Your RAPIDAPI_KEY
_ALPACA_KEY_ID = ""
_ALPACA_SECRET_KEY = ""


def _run(query: str):
    SCHEMA_PATH = pathlib.Path(
        os.path.join(os.path.dirname(__file__), "alpaca.yaml")
    )
    BASE_URL = 'https://paper-api.alpaca.markets'
    alpaca_api_loader = openapi_provider.standard_api_loader(
        api="alpaca",
        schema_path=SCHEMA_PATH,
        request_body_descriptions_path=None,
        base_url=BASE_URL,
    )
    registry_ = registry.Registry(
        [
            openapi_provider.Provider(
                api_loaders=[alpaca_api_loader],
                filter_function_names=["alpaca_v2_orders_post"]
            ),
            rapidapi_provider.Provider.standard(
                filter_rapidapi_endpoint_urls=[
                    'https://last10k-company-v1.p.rapidapi.com/v1/company/income',
                ],
            ),

        ],
    )

    auth_ctx = auth.StandardAuthContext(
        rapidapi=auth.RapidApiAuthContext(
            rapidapi_key=_RAPIDAPI_KEY,
        ),
        openapi=auth.OpenApiAuthContext(
            api_to_headers={
                "alpaca": {
                    "APCA-API-KEY-ID": _ALPACA_KEY_ID,
                    "APCA-API-SECRET-KEY": _ALPACA_SECRET_KEY,
                }
            },
        ),
    )
    agent = openai_assistant.Agent(
        registry_=registry_, openai_client=openai.OpenAI(api_key=_OPENAI_KEY)
    )
    agent(auth_ctx, query)


@click.command()
@click.option("--task", required=False)
def run(task: str | None) -> None:
    if not task:
        task = "Get the latest EPS for Google, and either buy or short 5 shares based on the sentiment"
        _run(task)


if __name__ == "__main__":
    run()
