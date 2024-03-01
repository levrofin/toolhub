import jsonpickle
import os

from typing import Any
from toolhub.lib import auth
from toolhub.lib import function

# TODO: use package resources.
_PARENT_DIR = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
FUNCTIONS_FILE = os.path.join(_PARENT_DIR, "functions.json")


def load_functions_collections() -> (
    tuple[
        list[function.Function[Any, Any, auth.StandardAuthContext]],
        list[function.FunctionCollection],
    ]
):
    with open(FUNCTIONS_FILE, "r") as f:
        category_to_api_to_functions = jsonpickle.decode(f.read())

    functions = []
    collections = []
    for category, api_to_functions in category_to_api_to_functions.items():
        for api, fns in api_to_functions.items():
            functions += fns
            collections.append(
                function.FunctionCollection(
                    name=f"{category}.{api}",
                    description=None,
                    function_names={fn.spec.name for fn in fns},
                )
            )
    return functions, collections
