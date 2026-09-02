from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ProjectInput(BaseModel):
    project_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    requirements: list[str] = Field(min_length=1)
    openapi_path: str
    base_url: HttpUrl
    allowed_hosts: list[str] = Field(min_length=1)

    @field_validator("requirements")
    @classmethod
    def non_empty_requirements(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("requirements cannot be blank")
        return values


class ParameterDefinition(BaseModel):
    name: str
    location: Literal["path", "query", "header", "cookie"]
    required: bool = False
    schema_definition: dict[str, Any] = Field(default_factory=dict)


class Operation(BaseModel):
    operation_id: str
    method: str
    path: str
    success_statuses: list[int]
    required_parameters: list[str] = Field(default_factory=list)
    parameters: list[ParameterDefinition] = Field(default_factory=list)
    request_schema: dict[str, Any] | None = None


class Scenario(BaseModel):
    scenario_id: str
    operation_id: str
    kind: Literal["positive", "negative"]
    title: str
    expected_statuses: list[int]


class AnalysisResult(BaseModel):
    project: ProjectInput
    operations: list[Operation]
    scenarios: list[Scenario]
    traceability: list[dict[str, Any]]
