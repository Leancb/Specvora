from specvora.models import AnalysisResult, Operation, ProjectInput, Scenario


def analyze(project: ProjectInput, operations: list[Operation]) -> AnalysisResult:
    scenarios: list[Scenario] = []
    traceability: list[dict[str, object]] = []
    for index, operation in enumerate(operations, start=1):
        positive = Scenario(
            scenario_id=f"SCN-{index:03d}-POS",
            operation_id=operation.operation_id,
            kind="positive",
            title=f"{operation.method} {operation.path} returns a documented success",
            expected_statuses=operation.success_statuses,
        )
        scenarios.append(positive)
        linked = [positive.scenario_id]
        if operation.required_parameters:
            negative = Scenario(
                scenario_id=f"SCN-{index:03d}-NEG",
                operation_id=operation.operation_id,
                kind="negative",
                title="Required input is rejected when omitted",
                expected_statuses=[400, 401, 403, 404, 422],
            )
            scenarios.append(negative)
            linked.append(negative.scenario_id)
        req_index = min(index - 1, len(project.requirements) - 1)
        traceability.append(
            {
                "requirement_id": f"REQ-{req_index + 1:03d}",
                "requirement": project.requirements[req_index],
                "operation_id": operation.operation_id,
                "scenario_ids": linked,
            }
        )
    return AnalysisResult(
        project=project, operations=operations, scenarios=scenarios, traceability=traceability
    )
