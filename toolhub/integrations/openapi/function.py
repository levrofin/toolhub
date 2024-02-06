import dataclasses
import functools
import re
from typing import Callable

from toolhub.lib import auth
from toolhub.lib import function
from toolhub.integrations.openapi import client


@dataclasses.dataclass
class OpenAPIFunctionSpec(function.FunctionSpec):
    api: str
    endpoint: str
    method: str

    def __init__(
        self,
        parameters: list[function.ParameterSpec],
        return_: function.ReturnSpec,
        description: str | None,
        api: str,
        endpoint: str,
        method: str,
    ):
        # OpenAI validates against ^[a-zA-Z0-9_-]{1,64}$
        # Replace non-matching characters with "-".
        s = method
        for p in reversed(endpoint.split("/")):
            if not p:
                break
            if (new_s := re.sub(r"[^a-zA-Z0-9_-]+", "", p) + "_" + s) and len(
                new_s
            ) > 63 - len(api):
                break
            s = new_s
        name = api + "_" + s

        super().__init__(
            name=name,
            parameters=parameters,
            return_=return_,
            description=description,
        )
        self.api = api
        self.endpoint = endpoint
        self.method = method


def _callable(
    auth_ctx: auth.StandardAuthContext,
    api: str,
    base_url: str,
    endpoint: str,
    method: str,
) -> Callable:
    # NOTE: separate parameter namespace for client.request and the endpoint.
    def _impl(**params):
        return client.request(
            api=api,
            base_url=base_url,
            endpoint=endpoint,
            method=method,
            auth_ctx=auth_ctx,
            params=params,
        )

    return _impl


def make_function(spec: OpenAPIFunctionSpec, base_url: str) -> function.Function:
    return function.Function(
        spec=spec,
        callable_=functools.partial(
            _callable,
            api=spec.api,
            base_url=base_url,
            endpoint=spec.endpoint,
            method=spec.method,
        ),
    )
