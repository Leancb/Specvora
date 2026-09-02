from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from specvora.models import Operation

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def load_openapi(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"OpenAPI file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        document = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Invalid OpenAPI document: {exc}") from exc
    if not isinstance(document, dict) or not str(document.get("openapi", "")).startswith("3."):
        raise ValueError("Only OpenAPI 3.x documents are supported")
    if not isinstance(document.get("paths"), dict) or not document["paths"]:
        raise ValueError("OpenAPI document must define at least one path")
    return document


def extract_operations(document: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    for path, path_item in sorted(document["paths"].items()):
        if not isinstance(path_item, dict):
            continue
        shared = path_item.get("parameters", [])
        for method, definition in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(definition, dict):
                continue
            parameters = [*shared, *definition.get("parameters", [])]
            required = sorted(
                {
                    str(item["name"])
                    for item in parameters
                    if isinstance(item, dict) and item.get("required") and item.get("name")
                }
            )
            statuses = sorted(
                int(code)
                for code in definition.get("responses", {})
                if str(code).isdigit() and 200 <= int(code) < 300
            ) or [200]
            operations.append(
                Operation(
                    operation_id=str(definition.get("operationId") or _fallback_id(method, path)),
                    method=method.upper(),
                    path=str(path),
                    success_statuses=statuses,
                    required_parameters=required,
                )
            )
    if not operations:
        raise ValueError("OpenAPI document contains no supported HTTP operations")
    return operations


def _fallback_id(method: str, path: str) -> str:
    return "_".join([method.lower(), *[part.strip("{}") for part in path.split("/") if part]])
