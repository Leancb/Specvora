from __future__ import annotations

from copy import deepcopy
from typing import Any


class SchemaResolutionError(ValueError):
    pass


def resolve_document(document: dict[str, Any]) -> dict[str, Any]:
    root = deepcopy(document)
    return _resolve_node(root, root, ())


def _resolve_node(node: Any, root: dict[str, Any], stack: tuple[str, ...]) -> Any:
    if isinstance(node, list):
        return [_resolve_node(item, root, stack) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        reference = node["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise SchemaResolutionError("Only internal OpenAPI references are allowed")
        if reference in stack:
            chain = " -> ".join([*stack, reference])
            raise SchemaResolutionError(f"Circular OpenAPI reference: {chain}")
        resolved = _resolve_node(_lookup(root, reference), root, (*stack, reference))
        siblings = {key: value for key, value in node.items() if key != "$ref"}
        if siblings:
            if not isinstance(resolved, dict):
                raise SchemaResolutionError("Referenced value cannot be extended")
            resolved = _merge_schema(resolved, _resolve_node(siblings, root, stack))
        return resolved
    resolved_node = {key: _resolve_node(value, root, stack) for key, value in node.items()}
    if "allOf" in resolved_node:
        base = {key: value for key, value in resolved_node.items() if key != "allOf"}
        for part in resolved_node["allOf"]:
            if not isinstance(part, dict):
                raise SchemaResolutionError("allOf entries must be schemas")
            base = _merge_schema(base, part)
        resolved_node = base
    for keyword in ("oneOf", "anyOf"):
        if keyword in resolved_node:
            choices = resolved_node[keyword]
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise SchemaResolutionError(f"{keyword} must contain at least one schema")
            metadata = {key: value for key, value in resolved_node.items() if key != keyword}
            resolved_node = _merge_schema(choices[0], metadata)
            resolved_node[f"x-specvora-selected-{keyword}"] = 0
    return resolved_node


def _lookup(root: dict[str, Any], reference: str) -> Any:
    current: Any = root
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise SchemaResolutionError(f"OpenAPI reference not found: {reference}")
        current = current[part]
    return deepcopy(current)


def _merge_schema(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(left)
    for key, value in right.items():
        if key == "required":
            merged[key] = sorted(set(merged.get(key, [])) | set(value))
        elif key == "properties" and isinstance(value, dict):
            merged[key] = {**merged.get(key, {}), **deepcopy(value)}
        elif key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_schema(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
