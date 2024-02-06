import random
import string
from typing import Any

from toolhub.lib import auth
from toolhub.lib import function
from toolhub.lib import provider


def _random_string(length: int, charset: str | None = None) -> str:
    charset = charset or (string.ascii_lowercase + string.digits)
    return "".join(random.choices(charset, k=length))


_random_string_spec: function.FunctionSpec = function.FunctionSpec(
    name="random_string",
    parameters=[
        function.ParameterSpec(
            name="length",
            type_=int,
            description="Length of the generated string.",
            required=True,
        ),
        function.ParameterSpec(
            name="charset",
            type_=str,
            description="Set of characters used to generate the string.",
            required=False,
        ),
    ],
    return_=function.ReturnSpec(
        type_=str,
        description="A random string.",
    ),
    description=None,
)
_random_string_fn: function.Function[Any, Any, auth.AuthContext] = function.Function(
    spec=_random_string_spec, callable_=auth.no_auth(_random_string)
)


class Provider(provider.Provider[auth.AuthContext]):
    _functions: list[function.Function[Any, Any, auth.AuthContext]] = [
        _random_string_fn,
    ]
    _collections: list[function.FunctionCollection] = [
        function.FunctionCollection(
            name="random",
            description="functions that generate random outputs",
            function_names={_random_string_spec.name},
        ),
    ]

    def functions(self) -> list[function.Function[Any, Any, auth.AuthContext]]:
        return self._functions

    def collections(self) -> list[function.FunctionCollection]:
        return self._collections
