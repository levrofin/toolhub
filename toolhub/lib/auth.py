from __future__ import annotations

import abc
import dataclasses
from typing import Callable, ParamSpec, TypeVar

from toolhub.config import settings

P = ParamSpec("P")
R = TypeVar("R")


class AuthContext(abc.ABC):
    pass


@dataclasses.dataclass
class OpenApiAuthContext:
    api_to_headers: dict[str, dict[str, str]] | None = None


@dataclasses.dataclass
class RapidApiAuthContext:
    rapidapi_key: str
    host_to_headers: dict[str, dict[str, str]] | None = None


@dataclasses.dataclass
class StandardAuthContext(AuthContext):
    openapi: OpenApiAuthContext | None = None
    rapidapi: RapidApiAuthContext | None = None

    @classmethod
    def from_settings(cls) -> AuthContext:
        openapi = None
        if settings.auth.openapi:
            openapi = OpenApiAuthContext(
                api_to_headers={
                    api: headers
                    for api, headers in settings.auth.openapi.api_to_headers.items()
                },
            )
        rapidapi = None
        if settings.auth.rapidapi:
            rapidapi = RapidApiAuthContext(
                rapidapi_key=settings.auth.rapidapi.rapidapi_key,
                host_to_headers={
                    name: headers
                    for name, headers in settings.auth.rapidapi.host_to_headers.items()
                },
            )
        return StandardAuthContext(openapi=openapi, rapidapi=rapidapi)


A = TypeVar("A", bound=AuthContext)


def no_auth(callable_: Callable[P, R]) -> Callable[A, Callable[P, R]]:
    def _impl(_auth_ctx: A) -> Callable[P, R]:
        return callable_

    return _impl
