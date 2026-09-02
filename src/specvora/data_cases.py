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
    variants = _schema_variants(operation.request_schema)
    first_body = example_value(variants[0][1]) if variants else None
    cases: list[RequestCase] = []
    body_case_groups: list[list[RequestCase]] = []
    if variants:
        for label, schema in variants:
            suffix = f"-{label}" if label else ""
            body_case_groups.append(_body_cases(operation, parameters, schema, suffix))
        cases = [group[0] for group in body_case_groups]
    else:
        cases.append(
            RequestCase(
                case_id=f"{operation.operation_id}-valid",
                operation_id=operation.operation_id,
                kind="valid",
                parameters=parameters,
            )
        )
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
                    body=first_body,
                    mutation=f"omit required parameter {item.name}",
                )
            )
    cases.extend(case for group in body_case_groups for case in group[1:])
    return cases


def _body_cases(
    operation: Operation,
    parameters: dict[str, Any],
    schema: dict[str, Any],
    suffix: str,
) -> list[RequestCase]:
    body = example_value(schema)
    cases = [
        RequestCase(
            case_id=f"{operation.operation_id}-valid{suffix}",
            operation_id=operation.operation_id,
            kind="valid",
            parameters=parameters,
            body=body,
            mutation=f"select schema variant {suffix[1:]}" if suffix else None,
        )
    ]
    for name in schema.get("required", []):
        if isinstance(body, dict) and name in body:
            invalid = dict(body)
            invalid.pop(name)
            cases.append(
                RequestCase(
                    case_id=f"{operation.operation_id}-missing-body-{name}{suffix}",
                    operation_id=operation.operation_id,
                    kind="missing_required",
                    parameters=parameters,
                    body=invalid,
                    mutation=f"omit required body property {name}{_variant_note(suffix)}",
                )
            )
    boundary = _first_invalid_boundary(schema)
    if boundary and isinstance(body, dict):
        name, value = boundary
        invalid = dict(body)
        invalid[name] = value
        cases.append(
            RequestCase(
                case_id=f"{operation.operation_id}-boundary-{name}{suffix}",
                operation_id=operation.operation_id,
                kind="invalid_boundary",
                parameters=parameters,
                body=invalid,
                mutation=f"violate boundary for {name}{_variant_note(suffix)}",
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
    for keyword in ("oneOf", "anyOf"):
        if schema.get(keyword):
            return example_value(_merge_metadata(schema[keyword][0], schema, keyword))
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            name: example_value(value)
            for name, value in sorted(schema.get("properties", {}).items())
            if name in schema.get("required", [])
        }
    if schema_type == "array":
        count = max(int(schema.get("minItems", 1)), 1)
        return [example_value(schema.get("items", {})) for _ in range(count)]
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
        if "maxLength" in definition:
            return name, "x" * (int(definition["maxLength"]) + 1)
        if "minimum" in definition:
            return name, definition["minimum"] - 1
        if "maximum" in definition:
            return name, definition["maximum"] + 1
        if "minItems" in definition:
            count = max(int(definition["minItems"]) - 1, 0)
            return name, [example_value(definition.get("items", {})) for _ in range(count)]
        if "maxItems" in definition:
            count = int(definition["maxItems"]) + 1
            return name, [example_value(definition.get("items", {})) for _ in range(count)]
        if definition.get("enum"):
            return name, "__invalid_enum_value__"
    return None


def _schema_variants(schema: dict[str, Any] | None) -> list[tuple[str, dict[str, Any]]]:
    if not schema:
        return []
    for keyword in ("oneOf", "anyOf"):
        if keyword in schema:
            return [
                (f"{keyword}-{index}", _merge_metadata(choice, schema, keyword))
                for index, choice in enumerate(schema[keyword], start=1)
            ]
    return [("", schema)]


def _merge_metadata(
    choice: dict[str, Any], schema: dict[str, Any], union_keyword: str
) -> dict[str, Any]:
    metadata = {
        key: value
        for key, value in schema.items()
        if key not in {"oneOf", "anyOf", "x-specvora-union-policy"}
    }
    merged = {**metadata, **choice}
    if "required" in metadata or "required" in choice:
        merged["required"] = sorted(
            set(metadata.get("required", [])) | set(choice.get("required", []))
        )
    merged["x-specvora-variant-of"] = union_keyword
    return merged


def _variant_note(suffix: str) -> str:
    return f" in schema variant {suffix[1:]}" if suffix else ""
