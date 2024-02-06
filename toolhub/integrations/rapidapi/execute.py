import json
import os
from typing import Any

import click
import httpx

from toolhub.lib import auth
from toolhub.lib.utils import not_none


def execute(
    method: str,
    root_url: str,
    url_f_string: str,
    required_params: set[str],
    conditional_params: set[str],
    auth_ctx: auth.AuthContext,
    params: dict[str, Any],
) -> Any:
    url = url_f_string.format(**params)

    assert isinstance(auth_ctx, auth.StandardAuthContext)
    rapidapi_auth: auth.RapidApiAuthContext = not_none(
        auth_ctx.rapidapi, "auth_ctx.rapidapi"
    )
    headers = {
        "X-RapidAPI-Key": rapidapi_auth.rapidapi_key,
        "X-RapidAPI-Host": root_url,
        **(rapidapi_auth.host_to_headers or {}).get(root_url, {}),
    }

    params = {
        k: v
        for k, v in params.items()
        if ((k in required_params) or (v and k in conditional_params))
    }

    response = httpx.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        verify=True,
        cookies={},
    )

    if (code := response.status_code) and (code // 100 != 2):
        raise RuntimeError(f"error({code}) {response.text}")
    try:
        return response.json()
    except Exception:
        return response.text
