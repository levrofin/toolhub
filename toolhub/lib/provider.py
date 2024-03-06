import abc
from typing import Any, Generic, TypeVar

from toolhub.lib import auth
from toolhub.lib import function

AuthContext = TypeVar("AuthContext", bound=auth.AuthContext)


class Provider(abc.ABC, Generic[AuthContext]):
    @abc.abstractmethod
    def functions(self) -> list[function.Function[Any, Any, AuthContext]]:
        raise NotImplementedError()

    @abc.abstractmethod
    def collections(self) -> list[function.FunctionCollection]:
        raise NotImplementedError()
