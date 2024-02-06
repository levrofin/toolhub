import pathlib
import re
from typing import Any, Optional, Union


import openapi_python_client
from openapi_python_client import cli
from openapi_python_client.parser import properties
from openapi_python_client.parser.properties import model_property
from openapi_python_client.schema.openapi_schema_pydantic import reference
from openapi_python_client.schema.openapi_schema_pydantic import schema

from toolhub.lib import function
from toolhub.integrations.openapi import function as openapi_function

_MODEL_SPEC_RE = re.compile(r"^#?/components/schemas/(.*)")
_DESCRIBE_RESPONSE_MAX_ENUM_VALUES = 2
_DESCRIBE_RESPONSE_MAX_SCHEMA_FIELDS = 20
_DESCRIBE_RESPONSE_MAX_DEPTH = 7
_DESCRIBE_RESPONSE_MAX_LENGTH = 1024

_TEndpoint = dict[str, Union[schema.Schema, properties.EnumProperty]]


def _name_for_type(s: str) -> str:
    if m := _MODEL_SPEC_RE.match(s):
        return m[1]
    return s


def _name_for_property(ref: str) -> str:
    return ref.split(".")[-1]


class Parser:
    def __init__(
        self, api: str, url: Optional[str] = None, path: Optional[pathlib.Path] = None
    ):
        self.api = api

        project: openapi_python_client.Project = (
            openapi_python_client._get_project_for_url_or_path(
                config=cli._process_config(
                    url=url,
                    path=path,
                    config_path=None,
                    meta_type=openapi_python_client.MetaType.NONE,
                    file_encoding="utf-8",
                )
            )
        )
        self.models = {
            _name_for_type(model.name): model for model in project.openapi.models
        }
        self.enums = {_name_for_type(e.name): e for e in project.openapi.enums}
        self.endpoints = {
            (endpoint.path, endpoint.method): endpoint
            for _, tag in project.openapi.endpoint_collections_by_tag.items()
            for endpoint in tag.endpoints
        }

    def _filter_endpoint(
        self, endpoint: dict[str, Union[schema.Schema, properties.EnumProperty]]
    ) -> bool:
        # Default implementation: include all endpoints; subclass may override.
        return True

    def _map_parameter(
        self,
        endpoint: dict[str, Union[schema.Schema, properties.EnumProperty]],
        param: dict[str, Any],
    ) -> dict[str, Any] | None:
        # Default implementation: preserve parameter as-is; subclass may override.
        return param

    def _model_properties(
        self,
        model: model_property.ModelProperty,
    ) -> _TEndpoint | None:
        _properties = model.data.properties
        # If the results are an array, return the array type
        if "results" in _properties:
            name = _name_for_type(_properties["results"].items.ref)
            results_model = self.models[name]
            return self._model_properties(results_model)
        flattened_properties = {}
        for name, prop in _properties.items():
            if isinstance(prop, reference.Reference):
                ref = _name_for_type(prop.ref)
                ref_model = self.models.get(ref)
                if ref_model:
                    ref_properties = self._model_properties(ref_model)
                    for suffix, leaf_prop in ref_properties.items():
                        flattened_properties[f"{name}.{suffix}"] = leaf_prop
                enum_prop = self.enums.get(ref)
                if enum_prop:
                    # TODO: formal enum support.
                    name = f"{name}[{','.join(enum_prop.values)}]"
                    flattened_properties[name] = enum_prop
            else:
                flattened_properties[name] = prop
        return flattened_properties

    def _endpoint_properties(
        self, endpoint: _TEndpoint
    ) -> dict[str, schema.Schema] | None:
        return self._model_properties(endpoint.responses[0].prop)

    def _describe_for_response_helper(
        self,
        visited_enums: set[str],
        visited_models: set[str],
        remaining_depth: int,
        v: reference.Reference | schema.Schema,
    ) -> str:
        if remaining_depth == 0:
            return ""
        if isinstance(v, reference.Reference):
            ref = _name_for_type(v.ref)
            if ref_enum := self.enums.get(ref):
                name = _name_for_property(ref)
                if ref in visited_enums:
                    return name
                visited_enums.add(ref)
                values = list(ref_enum.values.values())
                values_description = ",".join(
                    values[:_DESCRIBE_RESPONSE_MAX_ENUM_VALUES]
                ) + (",..." if len(values) > _DESCRIBE_RESPONSE_MAX_ENUM_VALUES else "")
                return f"{name}[{values_description}]"
            if ref_model := self.models.get(ref):
                name = _name_for_property(ref)
                if ref in visited_models:
                    return name
                visited_models.add(ref)
                return name + self._describe_for_response_helper(
                    visited_enums, visited_models, remaining_depth - 1, ref_model.data
                )
            raise ValueError(f"unsupported reference: {ref}")

        elif isinstance(v, schema.Schema):
            if v.type == "array" and v.items:
                return (
                    "["
                    + self._describe_for_response_helper(
                        visited_enums, visited_models, remaining_depth - 1, v.items
                    )
                    + "]"
                )

            if v.type == "object" and v.properties:
                name_w_description = [
                    (
                        name,
                        self._describe_for_response_helper(
                            visited_enums, visited_models, remaining_depth - 1, s
                        ),
                    )
                    for name, s in v.properties.items()
                    if not (name.startswith("_") or "links" in name.lower())
                ]
                return (
                    "{"
                    + ", ".join(
                        name + (f":{description}" if description else "")
                        for name, description in name_w_description[
                            :_DESCRIBE_RESPONSE_MAX_SCHEMA_FIELDS
                        ]
                    )
                    + (
                        ", ..."
                        if len(name_w_description)
                        > _DESCRIBE_RESPONSE_MAX_SCHEMA_FIELDS
                        else ""
                    )
                    + "}"
                )

            return ""  # v.type.value # TODO: overcome OpenAI description length limits.

        raise ValueError(f"unsupported value: {v}")

    def _describe_for_response(
        self,
        visited_enums: set[str],
        visited_models: set[str],
        v: reference.Reference | schema.Schema,
    ) -> str:
        for depth in range(_DESCRIBE_RESPONSE_MAX_DEPTH, 1, -1):
            if (
                description := self._describe_for_response_helper(
                    visited_enums, visited_models, depth, v
                )
            ) and len(description) <= _DESCRIBE_RESPONSE_MAX_LENGTH:
                return description
        return description[:_DESCRIBE_RESPONSE_MAX_LENGTH] + "..."

    def _response_description(self, endpoint: _TEndpoint) -> str | None:
        if not endpoint.responses or not (r := endpoint.responses[0]) or not r.prop:
            return None
        if isinstance(r.prop, properties.ModelProperty):
            return self._describe_for_response(set(), set(), r.prop.data)
        if isinstance(r.prop, properties.ListProperty):
            return (
                "["
                + self._describe_for_response(set(), set(), r.prop.inner_property.data)
                + "]"
            )
        return r.prop.get_type_string(no_optional=True, json=True)

    def _fn_spec(self, endpoint: _TEndpoint) -> openapi_function.OpenAPIFunctionSpec:
        if not self._filter_endpoint(endpoint):
            return None

        parameters = []
        for name, p in (
            *endpoint.path_parameters.items(),
            *endpoint.query_parameters.items(),
        ):
            type_ = p.get_type_string(no_optional=True, json=True)
            if param := self._map_parameter(
                endpoint,
                {
                    "name": name,
                    "type": type_,
                    "description": p.description or name,
                    "required": p.required,
                },
            ):
                parameters.append(param)

        params = []
        for p in parameters:
            name = p["name"]
            type_ = eval(p["type"])  # TODO: improve type conversion
            params.append(
                function.ParameterSpec(
                    name=name,
                    type_=type_,
                    description=p.get("description") or name,
                    required=str(p.get("required", "")) == "True",
                )
            )

        return_ = function.ReturnSpec(
            type_=str, description=self._response_description(endpoint)
        )

        return openapi_function.OpenAPIFunctionSpec(
            api=self.api,
            endpoint=endpoint.path,
            method=endpoint.method,
            parameters=params,
            return_=return_,
            description=(endpoint.summary or endpoint.description),
        )

    def fn_specs(self) -> list[openapi_function.OpenAPIFunctionSpec]:
        fn_specs = []
        for endpoint in self.endpoints.values():
            if fn_spec := self._fn_spec(endpoint):
                fn_specs.append(fn_spec)
        return fn_specs
