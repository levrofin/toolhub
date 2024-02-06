from __future__ import annotations


from collections import defaultdict
import re
from typing import Any, Generic, TypeVar

from toolhub.lib import auth
from toolhub.lib import function
from toolhub.lib import provider
from toolhub.integrations.openapi import provider as openapi_provider
from toolhub.integrations.rapidapi import provider as rapidapi_provider
from toolhub.integrations.rapidapi import function as rapidapi_function
from toolhub.integrations.rapidapi import utils as rapidapi_utils
from toolhub.standard_providers import random_provider

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
        filter_rapidapi_api_hostnames: list[str] | str | None = None,
        filter_rapidapi_endpoint_urls: list[str] | str | None = None,
    ):
        functions = {
            fn.spec.name: fn for provider in providers for fn in provider.functions()
        }
        collections = {
            col.name: col for provider in providers for col in provider.collections()
        }

        if isinstance(filter_collections, str):
            filter_collections = [filter_collections]
        if isinstance(filter_rapidapi_api_hostnames, str):
            filter_rapidapi_api_hostnames = [filter_rapidapi_api_hostnames]
        if isinstance(filter_rapidapi_endpoint_urls, str):
            filter_rapidapi_endpoint_urls = [filter_rapidapi_endpoint_urls]

        name_to_fn = {}

        rapidapi_api_hostnames = set()
        if filter_rapidapi_api_hostnames:
            rapidapi_api_hostnames = {
                rapidapi_utils.url_hostname(url)
                for url in filter_rapidapi_api_hostnames
            }

        rapidapi_hostname_to_function_urls: dict[str, list[str]] = defaultdict(list)
        if filter_rapidapi_endpoint_urls:
            for url in (
                rapidapi_utils.sanitize_url(url)
                for url in filter_rapidapi_endpoint_urls
            ):
                rapidapi_hostname_to_function_urls[
                    rapidapi_utils.url_hostname(url)
                ].append(url)

        for fn_name, fn in functions.items():
            if not (
                filter_collections
                or rapidapi_api_hostnames
                or rapidapi_hostname_to_function_urls
            ):
                name_to_fn[fn_name] = fn
            elif filter_collections and any(
                (fn_name in collections[collection_name].function_names)
                for collection_name in filter_collections
            ):
                name_to_fn[fn_name] = fn
            elif (
                rapidapi_api_hostnames
                and isinstance(fn, rapidapi_function.RapidAPIFunction)
                and (fn.root_url in rapidapi_api_hostnames)
            ):
                name_to_fn[fn_name] = fn
            elif (
                rapidapi_hostname_to_function_urls
                and isinstance(fn, rapidapi_function.RapidAPIFunction)
                and (urls := rapidapi_hostname_to_function_urls.get(fn.root_url, []))
                and any(_match_f_string(fn.url_f_string, url) for url in urls)
            ):
                name_to_fn[fn_name] = fn
            self._name_to_fn = name_to_fn

    def list_(self) -> list[function.Function[Any, Any, AuthContext]]:
        return list(self._name_to_fn.values())

    def get(self, name: ToolName) -> function.Function[Any, Any, AuthContext]:
        return self._name_to_fn[name]

    @classmethod
    def standard(
        cls,
        openapi: openapi_provider.Provider | None = None,
        rapidapi: rapidapi_provider.Provider | None = None,
        filter_collections: list[str] | None = None,
        filter_rapidapi_api_hostnames: list[str] | None = None,
        filter_rapidapi_endpoint_urls: list[str] | None = None,
    ) -> Registry:
        return cls(
            [
                random_provider.Provider(),
                openapi or openapi_provider.Provider.standard(),
                rapidapi or rapidapi_provider.Provider.standard(),
            ],
            filter_collections=filter_collections,
            filter_rapidapi_api_hostnames=filter_rapidapi_api_hostnames,
            filter_rapidapi_endpoint_urls=filter_rapidapi_endpoint_urls,
        )
