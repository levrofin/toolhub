import dataclasses
import functools
from typing import Callable

from toolhub.integrations.rapidapi import execute
from toolhub.lib import auth
from toolhub.lib import function


def _callable(
    auth_ctx: auth.AuthContext,
    method: str,
    root_url: str,
    url_f_string: str,
    required_params: set[str],
    conditional_params: set[str],
) -> Callable:
    # NOTE: separate parameter namespace for execute.execute and the endpoint.
    def _impl(**params):
        return execute.execute(
            method=method,
            root_url=root_url,
            url_f_string=url_f_string,
            required_params=required_params,
            conditional_params=conditional_params,
            auth_ctx=auth_ctx,
            params=params,
        )

    return _impl


@dataclasses.dataclass
class RapidAPIFunction(function.Function):
    category: str
    api: str
    endpoint: str
    method: str

    root_url: str
    url_f_string: str
    required_params: set[str]
    conditional_params: set[str]

    def __init__(
        self,
        spec: function.FunctionSpec,
        category: str,
        api: str,
        endpoint: str,
        method: str,
        root_url: str,
        url_f_string: str,
        required_params: set[str],
        conditional_params: set[str],
    ):
        super().__init__(
            spec=spec,
            callable_=functools.partial(
                _callable,
                method=method,
                root_url=root_url,
                url_f_string=url_f_string,
                required_params=required_params,
                conditional_params=conditional_params,
            ),
        )

        self.category = category
        self.api = api
        self.endpoint = endpoint
        self.method = method

        self.root_url = root_url
        self.url_f_string = url_f_string
        self.required_params = required_params
        self.conditional_params = conditional_params

    def __eq__(self, other):
        if not isinstance(other, RapidAPIFunction):
            return NotImplemented
        return (
            self.category,
            self.api,
            self.endpoint,
            self.method,
        ) == (
            other.category,
            other.api,
            other.endpoint,
            other.method,
        )

    def __hash__(self):
        return hash((self.category, self.api, self.endpoint, self.method))
