from __future__ import annotations

from toolhub.lib import function
from toolhub.lib import provider

from toolhub.integrations.rapidapi import loader


class Provider(provider.Provider):
    def __init__(self):
        self._functions, self._collections = loader.load_functions_collections()

    def functions(self) -> list[function.Function]:
        return self._functions

    def collections(self) -> list[function.FunctionCollection]:
        return self._collections

    @classmethod
    def standard(cls) -> Provider:
        return cls()
