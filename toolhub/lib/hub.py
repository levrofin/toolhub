import abc
import dataclasses
from typing import Generic, TypeVar

from toolhub.lib import auth
from toolhub.lib import registry

AuthContext = TypeVar("AuthContext", bound=auth.AuthContext)
ToolsSpec = TypeVar("ToolsSpec")
ToolCall = TypeVar("ToolCall")
ToolOutput = TypeVar("ToolOutput")


@dataclasses.dataclass
class ToolCallErrors:
    errors: list[Exception]


class Hub(abc.ABC, Generic[AuthContext, ToolsSpec, ToolCall, ToolOutput]):
    registry_: registry.Registry[AuthContext]

    def __init__(
        self,
        registry_: registry.Registry[AuthContext],
    ):
        self.registry_ = registry_

    @abc.abstractmethod
    def tools_spec(self) -> ToolsSpec:
        raise NotImplementedError()

    @abc.abstractmethod
    def call_tools(
        self,
        auth_ctx: AuthContext,
        calls: list[ToolCall],
    ) -> list[ToolOutput | ToolCallErrors]:
        """Returns: output or errors corresponding to each call, in order."""
        raise NotImplementedError()
