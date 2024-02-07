from __future__ import annotations

import re
from typing import Any, Generic, TypeVar

from toolhub.lib import auth
from toolhub.lib import function
from toolhub.lib import provider

ToolName = str
AuthContext = TypeVar("AuthContext", bound=auth.AuthContext)


def _match_f_string(f_string: str, string: str) -> bool:
    pattern = re.sub(r"{[^{}]*}", "(.*)", f_string)
    return bool(re.fullmatch(pattern, string))


class Registry(Generic[AuthContext]):
    _name_to_fn: dict[str, function.Function[Any, Any, AuthContext]]

    def __init__(
        self,
        providers: list[provider.Provider],
        filter_collections: list[str] | str | None = None,
    ):
        functions = {
            fn.spec.name: fn for provider in providers for fn in provider.functions()
        }
        collections = {
            col.name: col for provider in providers for col in provider.collections()
        }

        if isinstance(filter_collections, str):
            filter_collections = [filter_collections]

        self._name_to_fn = {
            fn_name: fn
            for fn_name, fn in functions.items()
            if (
                not filter_collections
                or (
                    filter_collections
                    and any(
                        (fn_name in collections[collection_name].function_names)
                        for collection_name in filter_collections
                    )
                )
            )
        }

    def list_(self) -> list[function.Function[Any, Any, AuthContext]]:
        return list(self._name_to_fn.values())

    def get(self, name: ToolName) -> function.Function[Any, Any, AuthContext]:
        return self._name_to_fn[name]
