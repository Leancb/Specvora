from specvora.data_cases import example_value, generate_request_cases
from specvora.models import Operation, ParameterDefinition


def test_example_value_is_deterministic_for_supported_schema_types() -> None:
    schema = {
        "type": "object",
        "required": ["active", "age", "name", "roles"],
        "properties": {
            "name": {"type": "string", "minLength": 3},
            "age": {"type": "integer", "minimum": 18},
            "active": {"type": "boolean"},
            "roles": {"type": "array", "items": {"type": "string", "enum": ["reader", "writer"]}},
            "ignored": {"type": "string"},
        },
    }
    assert example_value(schema) == {"active": True, "age": 18, "name": "xxx", "roles": ["reader"]}


def test_cases_include_valid_missing_and_boundary_variants() -> None:
    operation = Operation(
        operation_id="createUser",
        method="POST",
        path="/users",
        success_statuses=[201],
        required_parameters=["tenant"],
        parameters=[
            ParameterDefinition(
                name="tenant",
                location="header",
                required=True,
                schema_definition={"type": "string", "example": "qa"},
            )
        ],
        request_schema={
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string", "minLength": 3},
                "age": {"type": "integer", "minimum": 18},
            },
        },
    )
    cases = generate_request_cases(operation)
    assert [case.kind for case in cases] == [
        "valid",
        "missing_required",
        "missing_required",
        "missing_required",
        "invalid_boundary",
    ]
    assert cases[0].parameters == {"tenant": "qa"}
    assert cases[0].body == {"age": 18, "name": "xxx"}
    assert cases[-1].body["age"] == 17


def test_optional_operation_still_has_one_valid_case() -> None:
    operation = Operation(
        operation_id="health", method="GET", path="/health", success_statuses=[200]
    )
    assert [case.kind for case in generate_request_cases(operation)] == ["valid"]


def test_generates_cases_for_every_oneof_variant() -> None:
    operation = Operation(
        operation_id="createPayment",
        method="POST",
        path="/payments",
        success_statuses=[201],
        request_schema={
            "oneOf": [
                {
                    "type": "object",
                    "required": ["card"],
                    "properties": {"card": {"type": "string", "minLength": 4}},
                },
                {
                    "type": "object",
                    "required": ["pix"],
                    "properties": {"pix": {"type": "string", "format": "email"}},
                },
            ],
            "x-specvora-union-policy": "all-variants",
        },
    )
    cases = generate_request_cases(operation)
    valid = [case for case in cases if case.kind == "valid"]
    assert [case.case_id for case in valid] == [
        "createPayment-valid-oneOf-1",
        "createPayment-valid-oneOf-2",
    ]
    assert [case.body for case in valid] == [{"card": "xxxx"}, {"pix": "qa@example.com"}]
    assert {case.case_id for case in cases if case.kind == "missing_required"} == {
        "createPayment-missing-body-card-oneOf-1",
        "createPayment-missing-body-pix-oneOf-2",
    }


def test_generates_additional_upper_and_array_boundaries() -> None:
    schema = {
        "type": "object",
        "required": ["code", "roles"],
        "properties": {
            "code": {"type": "string", "maxLength": 2},
            "roles": {"type": "array", "minItems": 2, "items": {"type": "string"}},
        },
    }
    operation = Operation(
        operation_id="createRole",
        method="POST",
        path="/roles",
        success_statuses=[201],
        request_schema=schema,
    )
    cases = generate_request_cases(operation)
    assert cases[0].body == {"code": "x", "roles": ["x", "x"]}
    boundary = next(case for case in cases if case.kind == "invalid_boundary")
    assert boundary.body["code"] == "xxx"
