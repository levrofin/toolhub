from __future__ import annotations

import dataclasses
import pathlib

from toolhub.lib import function
from toolhub.lib import provider

from toolhub.integrations.openapi import parser
from toolhub.integrations.openapi.function import make_function
from toolhub.integrations.openapi.apis.crunchbase import crunchbase


@dataclasses.dataclass
class ApiLoader:
    api: str
    base_url: str
    parser_: parser.Parser


def standard_api_loader(
    api: str, schema_path: pathlib.Path, base_url: str
) -> ApiLoader:
    return ApiLoader(api, base_url, parser.Parser(api=api, path=schema_path))


class Provider(provider.Provider):
    def __init__(self, api_loaders: list[ApiLoader]):
        self._functions = []
        self._collections = []
        for api_loader in api_loaders:
            fns = [
                make_function(spec, api_loader.base_url)
                for spec in api_loader.parser_.fn_specs()
            ]

            self._functions += fns

            collection = function.FunctionCollection(
                name=api_loader.api,
                description=None,
                function_names={fn.spec.name for fn in fns},
            )
            self._collections.append(collection)

    def functions(self) -> list[function.Function]:
        return self._functions

    def collections(self) -> list[function.FunctionCollection]:
        return self._collections

    @classmethod
    def standard(cls) -> Provider:
        return cls(
            [
                standard_api_loader(api, schema_path, base_url)
                for api, schema_path, base_url in (
                    (crunchbase.API, crunchbase.SCHEMA_PATH, crunchbase.BASE_URL),
                    # NOTE: add new standard OpenAPI APIs here.
                )
            ]
        )
