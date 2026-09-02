from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class GotoStep(BaseModel):
    action: Literal["goto"]
    path: str = Field(min_length=1, max_length=500, pattern=r"^/")

    @field_validator("path")
    @classmethod
    def relative_path_only(cls, value: str) -> str:
        if value.startswith("//"):
            raise ValueError("goto path must not be protocol-relative")
        return value


class ClickStep(BaseModel):
    action: Literal["click"]
    selector: str = Field(min_length=1, max_length=500)


class FillStep(BaseModel):
    action: Literal["fill"]
    selector: str = Field(min_length=1, max_length=500)
    value: str = Field(max_length=2000)


class AssertVisibleStep(BaseModel):
    action: Literal["assert_visible"]
    selector: str = Field(min_length=1, max_length=500)


JourneyStep = GotoStep | ClickStep | FillStep | AssertVisibleStep


class WebJourney(BaseModel):
    journey_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    title: str = Field(min_length=1, max_length=200)
    steps: list[JourneyStep] = Field(min_length=1, max_length=50)


class ProjectInput(BaseModel):
    project_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    requirements: list[str] = Field(min_length=1)
    openapi_path: str
    base_url: HttpUrl
    allowed_hosts: list[str] = Field(min_length=1)
    web_base_url: HttpUrl | None = None
    web_journeys: list[WebJourney] = Field(default_factory=list)

    @field_validator("requirements")
    @classmethod
    def non_empty_requirements(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("requirements cannot be blank")
        return values

    @model_validator(mode="after")
    def validate_web_target(self) -> ProjectInput:
        if bool(self.web_base_url) != bool(self.web_journeys):
            raise ValueError("web_base_url and web_journeys must be provided together")
        if self.web_base_url:
            allowed = {host.strip().lower() for host in self.allowed_hosts}
            if (self.web_base_url.host or "").lower() not in allowed:
                raise ValueError("web_base_url host must be explicitly allowlisted")
        return self


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
