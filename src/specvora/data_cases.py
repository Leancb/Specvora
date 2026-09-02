from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from specvora.models import Operation

FORMAT_EXAMPLES = {
    "date": "2026-01-01",
    "date-time": "2026-01-01T00:00:00Z",
    "email": "qa@example.com",
    "hostname": "example.test",
    "ipv4": "192.0.2.1",
    "uri": "https://example.test/resource",
    "uuid": "00000000-0000-4000-8000-000000000001",
}


class RequestCase(BaseModel):
    case_id: str
    operation_id: str
    kind: Literal["valid", "missing_required", "invalid_boundary"]
    parameters: dict[str, Any] = Field(default_factory=dict)
    body: Any = None
    mutation: str | None = None


def generate_request_cases(operation: Operation) -> list[RequestCase]:
    parameters = {item.name: example_value(item.schema_definition) for item in operation.parameters}
    body = example_value(operation.request_schema) if operation.request_schema else None
    cases = [
        RequestCase(
            case_id=f"{operation.operation_id}-valid",
            operation_id=operation.operation_id,
            kind="valid",
            parameters=parameters,
            body=body,
        )
    ]
    for item in operation.parameters:
        if item.required:
            missing = dict(parameters)
            missing.pop(item.name, None)
            cases.append(
                RequestCase(
                    case_id=f"{operation.operation_id}-missing-{item.name}",
                    operation_id=operation.operation_id,
                    kind="missing_required",
                    parameters=missing,
                    body=body,
                    mutation=f"omit required parameter {item.name}",
                )
            )
    if operation.request_schema:
        for name in operation.request_schema.get("required", []):
            if isinstance(body, dict) and name in body:
                invalid = dict(body)
                invalid.pop(name)
                cases.append(
                    RequestCase(
                        case_id=f"{operation.operation_id}-missing-body-{name}",
                        operation_id=operation.operation_id,
                        kind="missing_required",
                        parameters=parameters,
                        body=invalid,
                        mutation=f"omit required body property {name}",
                    )
                )
        boundary = _first_invalid_boundary(operation.request_schema)
        if boundary and isinstance(body, dict):
            name, value = boundary
            invalid = dict(body)
            invalid[name] = value
            cases.append(
                RequestCase(
                    case_id=f"{operation.operation_id}-boundary-{name}",
                    operation_id=operation.operation_id,
                    kind="invalid_boundary",
                    parameters=parameters,
                    body=invalid,
                    mutation=f"violate boundary for {name}",
                )
            )
    return cases


def example_value(schema: dict[str, Any] | None) -> Any:
    if not schema:
        return None
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if schema.get("enum"):
        return schema["enum"][0]
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            name: example_value(value)
            for name, value in sorted(schema.get("properties", {}).items())
            if name in schema.get("required", [])
        }
    if schema_type == "array":
        return [example_value(schema.get("items", {}))]
    if schema_type == "integer":
        return int(schema.get("minimum", 1))
    if schema_type == "number":
        return float(schema.get("minimum", 1.0))
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        if schema.get("format") in FORMAT_EXAMPLES:
            return FORMAT_EXAMPLES[schema["format"]]
        minimum = max(int(schema.get("minLength", 1)), 1)
        return "x" * minimum
    return None


def _first_invalid_boundary(schema: dict[str, Any]) -> tuple[str, Any] | None:
    for name, definition in sorted(schema.get("properties", {}).items()):
        if "minLength" in definition:
            return name, "x" * max(int(definition["minLength"]) - 1, 0)
        if "minimum" in definition:
            return name, definition["minimum"] - 1
        if definition.get("enum"):
            return name, "__invalid_enum_value__"
    return None
