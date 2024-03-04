from __future__ import annotations
from typing import Optional, List

import dataclasses
import pathlib

from toolhub.lib import function
from toolhub.lib import provider

from toolhub.integrations.openapi import parser
from toolhub.integrations.openapi.function import make_function
from toolhub.integrations.openapi.apis.alpaca import alpaca
from toolhub.integrations.openapi.apis.crunchbase import crunchbase


@dataclasses.dataclass
class ApiLoader:
    api: str
    base_url: str
    parser_: parser.Parser


def standard_api_loader(
    api: str,
    schema_path: pathlib.Path,
    request_body_descriptions_path: Optional[pathlib.Path],
    base_url: str,
) -> ApiLoader:
    return ApiLoader(
        api,
        base_url,
        parser.Parser(
            api=api,
            schema_path=schema_path,
            request_body_descriptions_path=request_body_descriptions_path,
        ),
    )


class Provider(provider.Provider):
    def __init__(self, api_loaders: list[ApiLoader], filter_function_names: Optional[List[str]] = None):
        self._functions = []
        self._collections = []
        for api_loader in api_loaders:
            fns = []
            for spec in api_loader.parser_.fn_specs():
                fn = make_function(spec, api_loader.base_url)
                if filter_function_names is None or fn.spec.name in filter_function_names:
                    fns.append(fn)

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
    def standard(cls, filter_function_names: Optional[List[str]] = None) -> Provider:
        return cls(
            [
                standard_api_loader(
                    api,
                    schema_path,
                    request_body_descriptions_path,
                    base_url,
                )
                for api, schema_path, request_body_descriptions_path, base_url in (
                    (
                        crunchbase.API,
                        crunchbase.SCHEMA_PATH,
                        crunchbase.REQUEST_BODY_DESCRIPTIONS_PATH,
                        crunchbase.BASE_URL,
                    ),
                    (
                        alpaca.API,
                        alpaca.SCHEMA_PATH,
                        alpaca.REQUEST_BODY_DESCRIPTIONS_PATH,
                        alpaca.BASE_URL,
                    ),
                    # NOTE: add new standard OpenAPI APIs here.
                )
            ], filter_function_names

        )
