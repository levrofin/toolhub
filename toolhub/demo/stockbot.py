import click

import openai

from toolhub.demo import openai_assistant
from toolhub.lib import auth
from toolhub.lib import registry
from toolhub.integrations.openapi import provider as openapi_provider


_OPENAI_KEY = ''  # replace with your OpenAI API key"
_RAPIDAPI_KEY = "" # Your RAPIDAPI_KEY
_ALPACA_KEY_ID = ""
_ALPACA_SECRET_KEY = ""


def _run(query: str):
    registry_ = registry.Registry([
            openapi_provider.Provider.standard(filter_function_names=["alpaca_v2_orders_post"]),
        ],
    )
    agent = openai_assistant.Agent(registry_=registry_, openai_client=openai.OpenAI(api_key=_OPENAI_KEY))
    auth_ctx = auth.StandardAuthContext(
        rapidapi=auth.RapidApiAuthContext(
            rapidapi_key=_RAPIDAPI_KEY,
        ),
            openapi = auth.OpenApiAuthContext(
        api_to_headers={"alpaca": {"APCA-API-KEY-ID": _ALPACA_KEY_ID, "APCA-API-SECRET-KEY": _ALPACA_SECRET_KEY}},
        ),
    )
    agent(auth_ctx, query)


@click.command()
@click.option("--task", required=False)
def run(task: str | None) -> None:
    if not task:
        task = "Can you place an order for 5 shares of AAPL at the market price?"
        _run(task)


if __name__ == "__main__":
    run()
