from collections import defaultdict
import hashlib
import json
import jsonpickle
import os
import re
from typing import Any, Optional

import pandas as pd

from toolhub.config import settings
from toolhub.integrations.rapidapi import loader
from toolhub.integrations.rapidapi import function as rapidapi_function
from toolhub.lib import function

_PARENT_DIR = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
_FUNCTION_INFOS_FILE = os.path.join(_PARENT_DIR, "function_infos.json")


def standardize_category(category: str) -> str:
    save_category = category.replace(" ", "_").replace(",", "_").replace("/", "_")
    while " " in save_category or "," in save_category:
        save_category = save_category.replace(" ", "_").replace(",", "_")
    save_category = save_category.replace("__", "_")
    return save_category


def standardize(string: str) -> str:
    res = re.compile("[^\\u4e00-\\u9fa5^a-z^A-Z^0-9^_]")
    string = res.sub("_", string)
    string = re.sub(r"(_)\1+", "_", string).lower()
    while True:
        if len(string) == 0:
            return string
        if string[0] == "_":
            string = string[1:]
        else:
            break
    while True:
        if len(string) == 0:
            return string
        if string[-1] == "_":
            string = string[:-1]
        else:
            break
    if string[0].isdigit():
        string = "get_" + string
    return string


def change_name(name: str) -> str:
    change_list = ["from", "class", "return", "false", "true", "id", "and"]
    if name in change_list:
        name = "is_" + name
    return name


_TYPE_MAP = {
    "BOOLEAN": bool,
    "NUMBER": float,
    "STRING": str,
    "ARRAY": list,
    "DATE (YYYY-MM-DD)": str,
    "ENUM": str,
}


def _parse_parameter(
    param: dict[str, Any], required: bool
) -> Optional[function.ParameterSpec]:
    description = param["description"]
    param_type = param["type"]
    # Filter out parameter types that are not supported
    if param_type in [
        None,
        "BINARY",
        "GEOPOINT (latitude, longitude)",
        "TIME (24-hour HH:MM)",
        "OBJECT",  # TODO: construct Pydantic model.
    ]:
        return None
    if param_type == "DATE (YYYY-MM-DD)":
        description += "Format: YYYY-MM-DD"
    if param.get("default"):
        description += f"ex: {param['default']}"
    if len(description) > 1024:
        description = description[:1024]
    return function.ParameterSpec(
        name=param["name"],
        # TODO: Fix this mapping
        type_=_TYPE_MAP[param["type"].upper()],
        description=description,
        required=required,
    )


def load_function_documents():
    documents_df = pd.read_csv(settings.rapidapi.toolbench_data_path, sep="\t")
    return documents_df["document_content"].apply(json.loads)


def load_function_infos() -> dict[str, dict[str, dict[str, Any]]]:
    with open(_FUNCTION_INFOS_FILE, "r") as f:
        return json.load(f)


def create_function_spec(
    category: str,
    api: str,
    endpoint: str,
    description: str,
    required_parameters: list[dict[str, Any]],
    optional_parameters: list[dict[str, Any]],
) -> Optional[function.FunctionSpec]:
    name = f"{category}-{api}-{endpoint}"
    if len(name) > 64:
        hasher = hashlib.blake2b(digest_size=8)  # 8 bytes = 16 hex chars
        hasher.update(name.encode())
        hash_string = hasher.hexdigest()
        name = name[:47] + "_" + hash_string[:16]

    parameters = []
    if len(description) > 1024:
        description = description[:1024]
    for param in required_parameters:
        parsed = _parse_parameter(param, True)
        if not parsed:
            return None
        else:
            parameters.append(parsed)
    for param in optional_parameters:
        parsed = _parse_parameter(param, False)
        if not parsed:
            return None
        else:
            parameters.append(parsed)
    return function.FunctionSpec(
        name=name,
        parameters=parameters,
        return_=function.ReturnSpec(
            type_=str,
            description="List of function names",
        ),  # TODO: Parse template_response when present
        description=description if description else name,
    )


def build_functions() -> dict[tuple[str, str], set[rapidapi_function.RapidAPIFunction]]:
    function_documents = load_function_documents()
    function_infos = load_function_infos()

    category_to_api_to_functions = defaultdict(lambda: defaultdict(set))
    for doc in function_documents:
        category = str(doc["category_name"])
        api = str(doc["tool_name"])
        endpoint = str(doc["api_name"])
        description = str(doc["api_description"])
        required_parameters = list(doc["required_parameters"])
        optional_parameters = list(doc["optional_parameters"])
        method = str(doc["method"])

        category = standardize_category(category)
        api = standardize(api)
        endpoint = change_name(standardize(endpoint))

        info = function_infos[f"{category}.{api}"].get(endpoint)
        if not info:
            continue

        root_url = info["rootUrl"]
        url_f_string = info["urlFstring"]
        required_params = info["requiredParams"]
        conditional_params = info["conditionalParams"]

        function_spec = create_function_spec(
            category,
            api,
            endpoint,
            description,
            required_parameters,
            optional_parameters,
        )
        if not function_spec:
            continue
        rapid_api_function = rapidapi_function.RapidAPIFunction(
            spec=function_spec,
            category=category,
            api=api,
            endpoint=endpoint,
            method=method,
            root_url=root_url,
            url_f_string=url_f_string,
            required_params=required_params,
            conditional_params=conditional_params,
        )
        category_to_api_to_functions[category][api].add(rapid_api_function)
    return {
        category: dict(api_to_functions)
        for category, api_to_functions in category_to_api_to_functions.items()
    }


def build_and_save_function_collections():
    functions = build_functions()
    functions_json = jsonpickle.encode(functions)
    with open(loader.FUNCTIONS_FILE, "w") as f:
        f.write(functions_json)


def run() -> None:
    build_and_save_function_collections()


if __name__ == "__main__":
    run()

    # functions = []
    # collections = []
    #
    # for category, category_specs in function_specs.items():
    #     names = set()
    #     for s in category_specs:
    #         if not s:
    #             continue
    #         functions.append(rapid_api_functions[s.name])
    #         names.add(s.name)
    #     collections.append(
    #         function.FunctionCollection(name=category,
    #                                     description=None,
    #                                     function_names=names))
    # return functions, collections

# _JSON_TYPE_MAP = {
#         str: 'str',
#         float: 'float',
#         bool: 'bool',
#         list: 'list',
#         dict: 'dict',
# }
#
# _INVESTER_JSON_TYPE_MAP = {v: k for k, v in _JSON_TYPE_MAP.items()}
# def build_and_seralize():
#     _fns, _cols = build_function_collections()
#     class EnhancedJSONEncoder(json.JSONEncoder):
#         def default(self, o):
#             if dataclasses.is_dataclass(o):
#                 return dataclasses.asdict(o)
#             if isinstance(o, set):
#                 return list(o)
#             if isinstance(o, Type):
#                 return _JSON_TYPE_MAP[o]
#             return super().default(o)
#
#     with open('fn_info', 'w') as fp:
#         json.dump(_fns, fp, cls=EnhancedJSONEncoder)
#
#
# def deserialize():
#     class EnhancedJSONDecoder(json.JSONDecoder):
#         def object_hook(self, obj):
#             if "type_" in obj:
#                 obj["type_"] = _INVESTER_JSON_TYPE_MAP[obj["type_"]]
#             return obj
#
#
#     with open('fn_info', 'r') as fp:
#         fns = json.load(fp)
#     return fns
