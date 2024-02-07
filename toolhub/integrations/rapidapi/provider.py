from __future__ import annotations

from collections import defaultdict
import re

from toolhub.lib import function
from toolhub.lib import provider

from toolhub.integrations.rapidapi import function as rapidapi_function
from toolhub.integrations.rapidapi import loader
from toolhub.integrations.rapidapi import utils as rapidapi_utils


def _match_f_string(f_string: str, string: str) -> bool:
    pattern = re.sub(r"{[^{}]*}", "(.*)", f_string)
    return bool(re.fullmatch(pattern, string))


class Provider(provider.Provider):
    def __init__(
        self,
        filter_rapidapi_api_hostnames: list[str] | str | None = None,
        filter_rapidapi_endpoint_urls: list[str] | str | None = None,
    ):
        functions, collections = loader.load_functions_collections()

        if isinstance(filter_rapidapi_api_hostnames, str):
            filter_rapidapi_api_hostnames = [filter_rapidapi_api_hostnames]
        if isinstance(filter_rapidapi_endpoint_urls, str):
            filter_rapidapi_endpoint_urls = [filter_rapidapi_endpoint_urls]

        rapidapi_api_hostnames = None
        if filter_rapidapi_api_hostnames:
            rapidapi_api_hostnames = {
                rapidapi_utils.url_hostname(url)
                for url in filter_rapidapi_api_hostnames
            }

        rapidapi_hostname_to_function_urls = None
        if filter_rapidapi_endpoint_urls:
            rapidapi_hostname_to_function_urls = defaultdict(list)
            for url in (
                rapidapi_utils.sanitize_url(url)
                for url in filter_rapidapi_endpoint_urls
            ):
                rapidapi_hostname_to_function_urls[
                    rapidapi_utils.url_hostname(url)
                ].append(url)

        name_to_fn = {
            fn.spec.name: fn
            for fn in functions
            if (
                not (filter_rapidapi_api_hostnames or filter_rapidapi_endpoint_urls)
                or (
                    rapidapi_api_hostnames
                    and isinstance(fn, rapidapi_function.RapidAPIFunction)
                    and (fn.root_url in rapidapi_api_hostnames)
                )
                or (
                    rapidapi_hostname_to_function_urls
                    and isinstance(fn, rapidapi_function.RapidAPIFunction)
                    and (
                        urls := rapidapi_hostname_to_function_urls.get(fn.root_url, [])
                    )
                    and any(_match_f_string(fn.url_f_string, url) for url in urls)
                )
            )
        }

        self._functions = list(name_to_fn.values())
        self._collections = [
            c
            for c in (
                function.FunctionCollection(
                    name=c.name,
                    description=c.description,
                    function_names=(c.function_names & name_to_fn.keys()),
                )
                for c in collections
            )
            if c.function_names
        ]

    def functions(self) -> list[function.Function]:
        return self._functions

    def collections(self) -> list[function.FunctionCollection]:
        return self._collections

    @classmethod
    def standard(
        cls,
        filter_rapidapi_api_hostnames: list[str] | str | None = None,
        filter_rapidapi_endpoint_urls: list[str] | str | None = None,
    ) -> Provider:
        return cls(
            filter_rapidapi_api_hostnames=filter_rapidapi_api_hostnames,
            filter_rapidapi_endpoint_urls=filter_rapidapi_endpoint_urls,
        )
