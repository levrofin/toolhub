import dataclasses

from typing import Callable, Generic, Type, TypeVar
from typing_extensions import ParamSpec

from toolhub.lib import auth

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")
AuthContext = TypeVar("AuthContext", bound=auth.AuthContext)


@dataclasses.dataclass
class ParameterSpec(Generic[T]):
    name: str
    type_: Type
    description: str | None
    required: bool


@dataclasses.dataclass
class ReturnSpec(Generic[R]):
    type_: Type
    description: str | None


@dataclasses.dataclass
class FunctionSpec(Generic[P, R]):
    name: str
    parameters: list[ParameterSpec]
    return_: ReturnSpec[R]
    description: str | None


@dataclasses.dataclass
class Function(Generic[P, R, AuthContext]):
    spec: FunctionSpec[P, R]
    callable_: Callable[AuthContext, Callable[P, R]]

    def __repr__(self):
        return self.spec.name


@dataclasses.dataclass
class FunctionCollection:
    name: str
    description: str | None
    function_names: set[str]
