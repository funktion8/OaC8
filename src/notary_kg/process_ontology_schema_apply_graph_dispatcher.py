from __future__ import annotations

import hashlib
import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .process_ontology_schema_apply_live_runner import (
    build_process_ontology_sharepoint_schema_apply_live_runner,
)
from .process_ontology_schema_apply_plan import build_process_ontology_sharepoint_schema_apply_plan
from .process_ontology_schema_apply_readiness import build_process_ontology_sharepoint_schema_apply_readiness


SCHEMA_VERSION = "nac.process-ontology-sharepoint-schema-apply-graph-dispatcher/v0.1"
CONTRACT_ID = "notarial.process_ontology_sharepoint_schema_apply_graph_dispatcher"
DEFAULT_GRAPH_DISPATCHER_JSON = Path("out/notary-kg/process-ontology-schema-apply-graph-dispatcher.redacted.json")
DEFAULT_GRAPH_DISPATCHER_MARKDOWN = Path("out/notary-kg/process-ontology-schema-apply-graph-dispatcher.redacted.md")


class ProcessOntologySchemaApplyGraphClient(Protocol):
    def get(self, path: str) -> dict[str, Any]:
        ...

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def patch(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class ProcessOntologySchemaApplyGraphDispatcherValidation:
    status: str
    errors: tuple[str, ...]


def run_process_ontology_sharepoint_schema_apply_graph_dispatcher(
    client: ProcessOntologySchemaApplyGraphClient,
    repo_root: Path,
    *,
    live_readiness_gate: Path,
    correlation_id: str,
    owner_approved: bool,
    execute_live_schema_apply: bool,
    write_redacted_evidence: bool,
    max_steps: int | None = None,
) -> dict[str, Any]:
    if not owner_approved:
        raise ValueError("process ontology schema apply Graph dispatcher requires owner_approved")
    if not execute_live_schema_apply:
        raise ValueError("process ontology schema apply Graph dispatcher requires execute_live_schema_apply")
    if not write_redacted_evidence:
        raise ValueError("process ontology schema apply Graph dispatcher requires write_redacted_evidence")
    if not correlation_id:
        raise ValueError("process ontology schema apply Graph dispatcher requires correlation_id")

    live_runner = build_process_ontology_sharepoint_schema_apply_live_runner(
        repo_root,
        live_readiness_gate=live_readiness_gate,
        correlation_id=correlation_id,
        owner_approved=owner_approved,
        execute_live_schema_apply=execute_live_schema_apply,
        write_redacted_evidence=write_redacted_evidence,
        ensure_default_artifacts=False,
    )
    if live_runner["status"] != "READY_FOR_GRAPH_REST_DISPATCH":
        raise ValueError("process ontology schema apply live runner is not ready for Graph REST dispatch")

    readiness = build_process_ontology_sharepoint_schema_apply_readiness(repo_root)
    apply_plan = build_process_ontology_sharepoint_schema_apply_plan(repo_root)
    plan_by_id = {step["id"]: step for step in apply_plan["steps"]}
    steps = [
        (workspace, unit, plan_by_id[unit["source_step_id"]])
        for workspace in readiness["workspaces"]
        for unit in workspace["apply_units"]
    ]
    if max_steps is not None:
        steps = steps[:max_steps]

    dispatch_steps: list[dict[str, Any]] = []
    stopped = False
    stop_reason = ""
    for sequence, (workspace, unit, plan_step) in enumerate(steps, start=1):
        try:
            result = _dispatch_step(client, workspace, unit, plan_step, sequence)
        except Exception as exc:  # pragma: no cover - validated through payload stop status
            result = _failed_step(workspace, unit, plan_step, sequence, str(exc))
            stopped = True
            stop_reason = f"{unit['id']}: {exc}"
        dispatch_steps.append(result)
        if stopped:
            break

    failed_steps = [step for step in dispatch_steps if step["status"] != "PASSED"]
    mutation_count = sum(1 for step in dispatch_steps if step["mutationExecuted"] is True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "PASSED" if not failed_steps else "FAILED",
        "mode": "owner_gated_graph_rest_dispatcher",
        "source": {
            "live_runner_schema": live_runner["schema_version"],
            "live_runner_status": live_runner["status"],
            "apply_readiness_schema": readiness["schema_version"],
            "apply_readiness_status": readiness["status"],
            "apply_plan_schema": apply_plan["schema_version"],
            "apply_plan_status": apply_plan["status"],
            "graph_base_url": readiness["source"]["graph_base_url"],
            "graph_rest_only": True,
            "legacy_sharepoint_api_allowed": False,
            "graph_sdk_allowed": False,
        },
        "summary": {
            "correlation_id": correlation_id,
            "planned_step_count": readiness["summary"]["workspace_apply_unit_count"],
            "dispatched_step_count": len(dispatch_steps),
            "passed_step_count": sum(1 for step in dispatch_steps if step["status"] == "PASSED"),
            "failed_step_count": len(failed_steps),
            "mutation_request_count": mutation_count,
            "skipped_mutation_count": sum(1 for step in dispatch_steps if step["skippedBecauseAlreadyExists"] is True),
            "executed_graph_requests": bool(dispatch_steps),
            "executed_graph_writes": mutation_count > 0,
            "writes_sharepoint": mutation_count > 0,
            "changes_sharepoint_schema": mutation_count > 0,
            "stopped_on_first_failure": stopped,
            "stop_reason": stop_reason,
        },
        "dispatch_steps": dispatch_steps,
        "privacy": {
            "storesRawGraphPath": False,
            "storesRawGraphResponse": False,
            "storesRawMutationPayload": False,
            "storesTokensOrSecrets": False,
            "storesMatterData": False,
            "readsSharePointFileContent": False,
        },
        "guardrails": {
            "owner_gated": True,
            "graph_rest_only": True,
            "executes_graph_requests": bool(dispatch_steps),
            "executes_graph_writes": mutation_count > 0,
            "writes_sharepoint": mutation_count > 0,
            "changes_sharepoint_schema": mutation_count > 0,
            "stores_tokens_or_secrets": False,
            "stores_matter_instance_values": False,
            "stores_document_full_text": False,
            "legacy_sharepoint_api_allowed": False,
            "graph_sdk_allowed": False,
            "raw_graph_path_stored": False,
            "raw_graph_response_stored": False,
            "raw_mutation_payload_stored": False,
        },
        "errors": [step["error"] for step in failed_steps if step.get("error")],
    }
    validation = validate_process_ontology_sharepoint_schema_apply_graph_dispatcher(payload)
    if validation.errors:
        payload["status"] = "FAILED"
        payload["errors"] = [*payload["errors"], *validation.errors]
    return payload


def validate_process_ontology_sharepoint_schema_apply_graph_dispatcher(
    payload: dict[str, Any],
) -> ProcessOntologySchemaApplyGraphDispatcherValidation:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("unexpected graph dispatcher schema_version")
    if payload.get("contract_id") != CONTRACT_ID:
        errors.append("unexpected graph dispatcher contract_id")
    if payload.get("mode") != "owner_gated_graph_rest_dispatcher":
        errors.append("graph dispatcher must be owner-gated")
    source = payload.get("source", {})
    if source.get("graph_base_url") != "https://graph.microsoft.com/v1.0":
        errors.append("graph dispatcher must use Microsoft Graph v1.0")
    if source.get("graph_rest_only") is not True:
        errors.append("graph dispatcher must remain Graph REST only")
    if source.get("legacy_sharepoint_api_allowed") is not False:
        errors.append("legacy SharePoint API must remain blocked")
    if source.get("graph_sdk_allowed") is not False:
        errors.append("Graph SDK must remain blocked")

    summary = payload.get("summary", {})
    if summary.get("dispatched_step_count", 0) < 1:
        errors.append("graph dispatcher must dispatch at least one step")
    if summary.get("passed_step_count") != summary.get("dispatched_step_count"):
        errors.append("graph dispatcher smoke must pass all dispatched steps")
    if summary.get("executed_graph_requests") is not True:
        errors.append("graph dispatcher must execute Graph requests")
    if summary.get("mutation_request_count", 0) < 1:
        errors.append("graph dispatcher must execute at least one schema mutation")

    for step in payload.get("dispatch_steps", []):
        step_id = step.get("id", "<unknown>")
        if step.get("status") != "PASSED":
            errors.append(f"{step_id}: dispatch step did not pass")
        if step.get("ownerGateRequired") is not True:
            errors.append(f"{step_id}: owner gate must be required")
        if step.get("graphRestOnly") is not True:
            errors.append(f"{step_id}: step must be Graph REST only")
        for raw_key in ("rawGraphPathStored", "rawGraphResponseStored", "rawMutationPayloadStored"):
            if step.get(raw_key) is not False:
                errors.append(f"{step_id}: {raw_key} must be false")

    privacy = payload.get("privacy", {})
    for key in (
        "storesRawGraphPath",
        "storesRawGraphResponse",
        "storesRawMutationPayload",
        "storesTokensOrSecrets",
        "storesMatterData",
        "readsSharePointFileContent",
    ):
        if privacy.get(key) is not False:
            errors.append(f"privacy must keep {key} false")

    guardrails = payload.get("guardrails", {})
    for key in ("owner_gated", "graph_rest_only", "executes_graph_requests", "executes_graph_writes"):
        if guardrails.get(key) is not True:
            errors.append(f"guardrail must be true: {key}")
    for key in (
        "stores_tokens_or_secrets",
        "stores_matter_instance_values",
        "stores_document_full_text",
        "legacy_sharepoint_api_allowed",
        "graph_sdk_allowed",
        "raw_graph_path_stored",
        "raw_graph_response_stored",
        "raw_mutation_payload_stored",
    ):
        if guardrails.get(key) is not False:
            errors.append(f"guardrail must be false: {key}")
    return ProcessOntologySchemaApplyGraphDispatcherValidation(
        status="PASSED" if not errors else "FAILED",
        errors=tuple(errors),
    )


def write_process_ontology_sharepoint_schema_apply_graph_dispatcher_artifact(
    client: ProcessOntologySchemaApplyGraphClient,
    repo_root: Path,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
    *,
    live_readiness_gate: Path,
    correlation_id: str,
    owner_approved: bool,
    execute_live_schema_apply: bool,
    write_redacted_evidence: bool,
    max_steps: int | None = None,
) -> dict[str, Any]:
    payload = run_process_ontology_sharepoint_schema_apply_graph_dispatcher(
        client,
        repo_root,
        live_readiness_gate=live_readiness_gate,
        correlation_id=correlation_id,
        owner_approved=owner_approved,
        execute_live_schema_apply=execute_live_schema_apply,
        write_redacted_evidence=write_redacted_evidence,
        max_steps=max_steps,
    )
    json_path = _resolve_output_path(repo_root, json_output or DEFAULT_GRAPH_DISPATCHER_JSON)
    markdown_path = _resolve_output_path(repo_root, markdown_output or DEFAULT_GRAPH_DISPATCHER_MARKDOWN)
    payload["artifact_paths"] = {
        "json": _relative_path(repo_root, json_path),
        "markdown": _relative_path(repo_root, markdown_path),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_dispatcher_markdown(payload), encoding="utf-8")
    return payload


def _dispatch_step(
    client: ProcessOntologySchemaApplyGraphClient,
    workspace: dict[str, Any],
    unit: dict[str, Any],
    plan_step: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    operation = unit["operation"]
    if operation == "extend_choice_column":
        return _dispatch_extend_choice_step(client, workspace, unit, plan_step, sequence)
    return _dispatch_create_step(client, workspace, unit, plan_step, sequence)


def _dispatch_create_step(
    client: ProcessOntologySchemaApplyGraphClient,
    workspace: dict[str, Any],
    unit: dict[str, Any],
    plan_step: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    replacements = _base_replacements(workspace, unit, plan_step)
    preflight_path = _render_path(unit["preflight_idempotency_check"]["path_template"], replacements)
    preflight = client.get(preflight_path)
    exists = _value_count(preflight) > 0
    mutation_path = _render_path(plan_step["request"]["path_template"], replacements)
    mutation_executed = False
    mutation_shape: dict[str, Any] = {}
    if not exists:
        body = plan_step["request"]["body"]
        if plan_step["request"]["method"] == "POST":
            mutation_shape = client.post(mutation_path, body)
        else:
            mutation_shape = client.patch(mutation_path, body)
        mutation_executed = True
    readback_path = preflight_path
    readback = client.get(readback_path)
    readback_count = _value_count(readback)
    if readback_count < 1:
        raise RuntimeError("readback did not find created or existing schema object")
    return _redacted_dispatch_step(
        workspace=workspace,
        unit=unit,
        plan_step=plan_step,
        sequence=sequence,
        preflight_path=preflight_path,
        mutation_path=mutation_path,
        readback_path=readback_path,
        mutation_executed=mutation_executed,
        skipped=exists,
        readback_count=readback_count,
        mutation_shape=mutation_shape,
    )


def _dispatch_extend_choice_step(
    client: ProcessOntologySchemaApplyGraphClient,
    workspace: dict[str, Any],
    unit: dict[str, Any],
    plan_step: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    replacements = _base_replacements(workspace, unit, plan_step)
    resolution_path = _render_path(
        "/sites/{site-id}/lists/{list-id}/columns?$filter=name eq '{column-name}'",
        replacements,
    )
    resolution = client.get(resolution_path)
    column_id = _first_value_id(resolution)
    if not column_id:
        raise RuntimeError("choice column id could not be resolved")
    replacements["column-id"] = column_id
    preflight_path = _render_path(unit["preflight_idempotency_check"]["path_template"], replacements)
    preflight = client.get(preflight_path)
    required_choices = unit["preflight_idempotency_check"].get("required_choice_values", [])
    current_choices = _choice_values(preflight)
    exists = all(choice in current_choices for choice in required_choices)
    mutation_path = _render_path(plan_step["request"]["path_template"], replacements)
    mutation_executed = False
    mutation_shape: dict[str, Any] = {}
    if not exists:
        mutation_shape = client.patch(mutation_path, plan_step["request"]["body"])
        mutation_executed = True
    readback = client.get(preflight_path)
    readback_choices = _choice_values(readback)
    if not all(choice in readback_choices for choice in required_choices):
        raise RuntimeError("choice readback did not contain all required values")
    return _redacted_dispatch_step(
        workspace=workspace,
        unit=unit,
        plan_step=plan_step,
        sequence=sequence,
        preflight_path=preflight_path,
        mutation_path=mutation_path,
        readback_path=preflight_path,
        mutation_executed=mutation_executed,
        skipped=exists,
        readback_count=1,
        mutation_shape=mutation_shape,
    )


def _failed_step(
    workspace: dict[str, Any],
    unit: dict[str, Any],
    plan_step: dict[str, Any],
    sequence: int,
    error: str,
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "id": unit["id"],
        "workspaceId": workspace["workspace_id"],
        "operation": unit["operation"],
        "target": unit["target"],
        "status": "FAILED",
        "error": error,
        "method": plan_step["request"]["method"],
        "ownerGateRequired": True,
        "graphRestOnly": True,
        "mutationExecuted": False,
        "skippedBecauseAlreadyExists": False,
        "rawGraphPathStored": False,
        "rawGraphResponseStored": False,
        "rawMutationPayloadStored": False,
    }


def _redacted_dispatch_step(
    *,
    workspace: dict[str, Any],
    unit: dict[str, Any],
    plan_step: dict[str, Any],
    sequence: int,
    preflight_path: str,
    mutation_path: str,
    readback_path: str,
    mutation_executed: bool,
    skipped: bool,
    readback_count: int,
    mutation_shape: dict[str, Any],
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "id": unit["id"],
        "workspaceId": workspace["workspace_id"],
        "operation": unit["operation"],
        "target": unit["target"],
        "status": "PASSED",
        "method": plan_step["request"]["method"],
        "ownerGateRequired": True,
        "graphRestOnly": True,
        "preflightPathSha256": _sha256(preflight_path),
        "mutationPathSha256": _sha256(mutation_path),
        "readbackPathSha256": _sha256(readback_path),
        "mutationExecuted": mutation_executed,
        "skippedBecauseAlreadyExists": skipped,
        "readbackValueCount": readback_count,
        "mutationResponseShapeKeys": sorted(mutation_shape) if mutation_shape else [],
        "bodyShapeKeys": sorted(plan_step["request"]["body"]),
        "rawGraphPathStored": False,
        "rawGraphResponseStored": False,
        "rawMutationPayloadStored": False,
    }


def _base_replacements(workspace: dict[str, Any], unit: dict[str, Any], plan_step: dict[str, Any]) -> dict[str, str]:
    body = plan_step["request"]["body"]
    column_name = str(body.get("name") or unit["preflight_idempotency_check"].get("match", {}).get("name") or "")
    return {
        "site-id": str(workspace["site_id"]),
        "list-id": str(unit.get("target_list_or_library_id") or ""),
        "target-display-name": str(unit["target"]),
        "column-name": column_name,
    }


def _render_path(template: str, replacements: dict[str, str]) -> str:
    path = template
    for key, value in replacements.items():
        safe = "," if key == "site-id" else ""
        if key in {"target-display-name", "column-name"}:
            safe = ""
        path = path.replace("{" + key + "}", urllib.parse.quote(value.replace("'", "''"), safe=safe))
    if not path.startswith("/"):
        raise RuntimeError("Graph REST path must start with /")
    if path.startswith("/_api") or "/_api/" in path:
        raise RuntimeError("legacy SharePoint REST path is blocked")
    return path


def _value_count(response: dict[str, Any]) -> int:
    value = response.get("value")
    return len(value) if isinstance(value, list) else (1 if response else 0)


def _first_value_id(response: dict[str, Any]) -> str:
    value = response.get("value")
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return str(value[0].get("id") or "")
    return ""


def _choice_values(response: dict[str, Any]) -> list[str]:
    if "choice" in response and isinstance(response["choice"], dict):
        choices = response["choice"].get("choices")
        return [str(choice) for choice in choices] if isinstance(choices, list) else []
    value = response.get("value")
    if isinstance(value, list) and value and isinstance(value[0], dict):
        choice = value[0].get("choice")
        if isinstance(choice, dict) and isinstance(choice.get("choices"), list):
            return [str(choice) for choice in choice["choices"]]
    return []


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dispatcher_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Process Ontology SharePoint Schema Apply Graph Dispatcher",
        "",
        f"- Status: `{payload['status']}`",
        f"- Schema: `{payload['schema_version']}`",
        f"- Correlation ID: `{summary['correlation_id']}`",
        f"- Dispatched steps: `{summary['dispatched_step_count']}`",
        f"- Mutations executed: `{summary['mutation_request_count']}`",
        f"- Executed Graph requests: `{summary['executed_graph_requests']}`",
        f"- Executed Graph writes: `{summary['executed_graph_writes']}`",
        f"- Stopped on first failure: `{summary['stopped_on_first_failure']}`",
        "",
        "## Guardrails",
        "",
    ]
    for key, value in payload["guardrails"].items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def _resolve_output_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _relative_path(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root) if path.is_relative_to(repo_root) else path)
