import httpx
import string
from typing import Any

from toolhub.config import settings
from toolhub.lib import auth
from toolhub.lib.utils import not_none


# openapi-python-client doesn't yet support Basic auth, using workaround mentioned:
# https://github.com/openapi-generators/openapi-python-client/issues/525
def request(
    api: str,
    base_url: str,
    endpoint: str,
    method: str,
    auth_ctx: auth.StandardAuthContext,
    params: dict[str, Any],
) -> dict[str, Any]:
    url = f"{base_url}/{endpoint}"

    openapi_auth: auth.OpenApiAuthContext = not_none(
        auth_ctx.openapi, "auth_ctx.openapi"
    )
    headers = {
        **(openapi_auth.api_to_headers or {}).get(api, {}),
    }

    # some params are required in the URL itself.
    available_args = params.copy()
    f = string.Formatter()
    required_args = [name for _, name, _, _ in f.parse(url) if name]
    url = url.format(**{a: available_args.pop(a) for a in required_args})

    response = httpx.request(
        verify=True,
        method=method,
        headers=headers,
        cookies={},
        timeout=settings.openapi.timeout_s,
        params=params,
        url=url,
    )

    if (code := response.status_code) and (code // 100 != 2):
        raise RuntimeError(f"error({code}) {response.content}")
    content = response.json()
    return content
