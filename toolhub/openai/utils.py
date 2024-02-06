import datetime
from dateutil import parser as dateutil_parser
import json
import pydantic
from typing import Any, get_args, get_origin, Type


from openai.types.shared_params.function_definition import FunctionDefinition

from toolhub.lib import auth
from toolhub.lib import function


_MAX_RESULT_LENGTH = 1024
_PRIMITIVE_TYPE_MAP = {
    None: "None",
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
}
_MAX_N_TOOLS = 127


def _map_type(type_: Type) -> dict[str, Any]:
    if mapped_type := _PRIMITIVE_TYPE_MAP.get(type_):
        return {"type": mapped_type}
    elif type_ == list or get_origin(type_) is list:
        type_json: dict[str, Any] = {"type": "array"}
        if arg_types := get_args(type_):
            (item_type,) = arg_types
            type_json["items"] = {"type": _map_type(item_type)}
        return type_json
    elif issubclass(type_, datetime.date):
        return {"type": "string", "format": "date"}
    elif issubclass(type_, datetime.datetime):
        return {"type": "string", "format": "date-time"}
    elif issubclass(type_, pydantic.BaseModel):
        return type_.model_json_schema()  # type: ignore[attr-defined] # https://docs.pydantic.dev/2.5/api/base_model/#pydantic.main.BaseModel.model_json_schema
    # TODO: if type is an enum, parameter["enum"] = type.values
    else:
        raise RuntimeError(f"Unsupported type {type_}")


def _cast(type_: Type, o: Any) -> Any:
    if type_ in _PRIMITIVE_TYPE_MAP:
        return type_(o)
    elif get_origin(type_) is list and get_args(type_) is not None:
        (item_type,) = get_args(type_)
        return [_cast(item_type, i) for i in o]
    elif issubclass(type_, datetime.date):
        d = dateutil_parser.parse(o)
        return d.date()
    elif issubclass(type_, datetime.datetime):
        return dateutil_parser.parse(json.loads(o))
    elif issubclass(type_, pydantic.BaseModel):
        return type_.parse_obj(o)

    # TODO: if type is an enum, parameter["enum"] = type.values
    else:
        raise RuntimeError(f"Unsupported type {type_}")


def _output_str(result: Any) -> str:
    if isinstance(result, pydantic.BaseModel):
        return result.model_dump_json()  # type: ignore[attr-defined] # https://docs.pydantic.dev/2.5/api/base_model/#pydantic.main.BaseModel.model_dump_json
    return str(result)


def _fn_spec_to_fn_def(fn_spec: function.FunctionSpec) -> FunctionDefinition:
    properties = {}
    required = []
    for p_spec in fn_spec.parameters:
        # TODO: leverage type translations in pydantic/json_schema.py.
        parameter = _map_type(p_spec.type_)

        if p_spec.description:
            parameter["description"] = p_spec.description + (
                ". This parameter is a required." if p_spec.required else ""
            )
        properties[p_spec.name] = parameter

        if p_spec.required:
            required.append(p_spec.name)
    parameters = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    description = fn_spec.description or ""
    description += (
        ". " if description else ""
    ) + f"Returns: {fn_spec.return_.description}"

    rv = FunctionDefinition(
        name=fn_spec.name,
        parameters=parameters,
        description=description,
    )
    return rv


def fns_to_fn_defs(fns: list[function.Function]) -> list[FunctionDefinition]:
    assert (
        len(fns) < _MAX_N_TOOLS
    ), f"OpenAI supports at most {_MAX_N_TOOLS} tools; please use a function filter"
    return [_fn_spec_to_fn_def(fn.spec) for fn in fns]


def call_fn_from_openai(
    auth_ctx: auth.AuthContext,
    fn: function.Function,
    arguments: str,
) -> str | list[Exception]:
    parameters = json.loads(arguments)

    typed_parameters = {}
    errors: list[Exception] = []
    for p in fn.spec.parameters:
        if p.name in parameters:
            try:
                typed_parameter = _cast(p.type_, parameters[p.name])
            except Exception as e:
                errors.append(
                    ValueError(f"parameter {p.name} expected type {p.type_}: {e}")
                )
                continue
            typed_parameters[p.name] = typed_parameter
        elif p.required:
            errors.append(ValueError(f"missing required parameter {p.name}"))
    if errors:
        return errors

    try:
        result = fn.callable_(auth_ctx)(**typed_parameters)
        output = _output_str(result)
    except Exception as e:
        return [e]

    if (n_extra := len(result) - _MAX_RESULT_LENGTH) > 0:
        output = output[:_MAX_RESULT_LENGTH] + f"... {n_extra} characters omitted"
    return output
