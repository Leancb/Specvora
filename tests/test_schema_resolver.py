import pytest

from specvora.schema_resolver import SchemaResolutionError, resolve_document


def test_resolves_internal_reference_and_allof_composition() -> None:
    document = {
        "components": {
            "schemas": {
                "Identity": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {"id": {"type": "integer", "minimum": 1}},
                },
                "User": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Identity"},
                        {
                            "type": "object",
                            "required": ["name"],
                            "properties": {"name": {"type": "string", "minLength": 2}},
                        },
                    ]
                },
            }
        },
        "schema": {"$ref": "#/components/schemas/User"},
    }
    schema = resolve_document(document)["schema"]
    assert schema["required"] == ["id", "name"]
    assert set(schema["properties"]) == {"id", "name"}


def test_preserves_all_union_variants_for_case_generation() -> None:
    document = {"schema": {"oneOf": [{"type": "string", "enum": ["basic"]}, {"type": "integer"}]}}
    schema = resolve_document(document)["schema"]
    assert [choice["type"] for choice in schema["oneOf"]] == ["string", "integer"]
    assert schema["x-specvora-union-policy"] == "all-variants"


@pytest.mark.parametrize(
    "reference",
    ["https://example.com/schema.json", "schemas/user.yaml#/User", "file:///tmp/schema.json"],
)
def test_rejects_non_internal_references(reference: str) -> None:
    with pytest.raises(SchemaResolutionError, match="Only internal"):
        resolve_document({"schema": {"$ref": reference}})


def test_rejects_missing_and_circular_references() -> None:
    with pytest.raises(SchemaResolutionError, match="not found"):
        resolve_document({"schema": {"$ref": "#/components/schemas/Missing"}})
    circular = {
        "components": {
            "schemas": {
                "A": {"$ref": "#/components/schemas/B"},
                "B": {"$ref": "#/components/schemas/A"},
            }
        },
        "schema": {"$ref": "#/components/schemas/A"},
    }
    with pytest.raises(SchemaResolutionError, match="Circular"):
        resolve_document(circular)
