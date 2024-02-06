import openai

from toolhub.config import settings
from toolhub.lib import auth
from toolhub.lib import registry


def openai_client() -> openai.OpenAI:
    try:
        openai_key = settings.openai.api_key
    except (AttributeError, KeyError):
        openai_key = None  # replace with your OpenAI API key

    assert openai_key, f"Please define your OpenAI API key in {__file__}."
    return openai.OpenAI(api_key=openai_key)


def registry_(
    collections: str | None,
    rapidapi_api_hostnames: str | None,
    rapidapi_endpoint_urls: str | None,
) -> registry.Registry:
    return registry.Registry.standard(
        filter_collections=(collections.split(",") if collections else None),
        filter_rapidapi_api_hostnames=(
            rapidapi_api_hostnames.split(",") if rapidapi_api_hostnames else None
        ),
        filter_rapidapi_endpoint_urls=(
            rapidapi_endpoint_urls.split(",") if rapidapi_endpoint_urls else None
        ),
    )


def auth_ctx() -> auth.AuthContext:
    try:
        return auth.StandardAuthContext.from_settings()
    except (AttributeError, KeyError):
        pass

    rapidapi_key = None  # required: replace with your RapidAPI API key
    assert rapidapi_key, f"Please define your RapidAPI API key in {__file__}."

    crunchbase_key = None  # optional: replace with your Crunchbase API key

    return auth.StandardAuthContext(
        openapi=auth.OpenApiAuthContext(
            api_to_headers={"crunchbase": {"X-cb-user-key": crunchbase_key}}
        ),
        rapidapi=auth.RapidApiAuthContext(
            rapidapi_key=rapidapi_key,
            host_to_headers=None,
        ),
    )
