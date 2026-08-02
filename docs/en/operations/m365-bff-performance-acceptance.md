# M365 BFF Performance Acceptance

Status: planned documentation and JSON contract slice; no live runner is
implemented by this change.

This standard defines a capacity-gated acceptance lane for the activated M365
BFF read endpoint. The machine-readable source is
[m365-bff-performance-acceptance.contract.json](../../../workflows/contracts/m365-bff-performance-acceptance.contract.json),
with its verification harness in
[m365-bff-performance-acceptance.verification.json](../../../workflows/verification-contracts/m365-bff-performance-acceptance.verification.json).

## Fixed Route

The business target is immutable:

| Field | Exact value |
| --- | --- |
| Scheme | `https` |
| Host | `func-nac-bff-test-funktion8.azurewebsites.net` |
| Method | `GET` |
| Workspace | `notary_team_01` |
| Matter | `NAC-SYN-MATTER-001` |
| Path | `/v1/workspaces/notary_team_01/matters/NAC-SYN-MATTER-001/workbench-snapshot` |
| Query | `purpose=view_synthetic_matter_workspace` |
| Wire schema | `nac.workbench.snapshot/v1` |

Redirects, alternate targets, cleartext HTTP and cache-busting changes are
forbidden. Every dispatched response must be exactly HTTP `200`, validate as
`nac.workbench.snapshot/v1` and be no larger than `1 MiB`. Bodies are validated
in memory and never retained.

## Capacity Preflight

Live execution is `BLOCKED` unless current authoritative evidence identifies
the tenant's SharePoint service tier and verifies both its request allowance
and resource-unit allowance. Estimates, defaults and inferred tiers are not
authoritative evidence.

The preflight also measures baseline tenant request and RU load and derives the
test allocation from a conservative RU-per-request upper bound. Baseline plus
planned test load must stay at or below `50%` of both verified allowances in
every allowance window defined by the authoritative tier. The lower resulting
rate controls every phase. Evidence older than 24 hours, evidence bound to
another tenant/workspace, or an unavailable allowance leaves status `BLOCKED`.

The Azure preflight reads Azure Monitor and requires:

- `AlwaysReadyUnits=0`
- projected and observed acceptance execution units at or below the inclusive
  cap of `120,000 GB-s`
- continued monitor availability during and after the run

These are read-only checks. They do not permit a capacity, permission,
configuration or infrastructure change.

## Global Dispatch Budget

Exactly one inclusive global ceiling applies across all phases:

```text
maximum target dispatches = 50,000
```

This is a ceiling, not a required request count. A successful safe plan may use
fewer requests. Every target attempt counts, including attempts that time out,
fail authentication, redirect, throttle or trigger an abort. A sequence is
reserved atomically before network dispatch. No request is sent when the next
sequence would exceed `50,000`.

Client retries and automatic redirect following are disabled. There is no
unconditional 50,000-request phase and no unconditional requirement to finish
50,000 requests within two hours.

## Phases

The owner-bound phase planner allocates all phase budgets in advance. Their sum
must be at most `50,000`, and every rate is capped by the verified 50% request
and RU allowances.

| Phase | Safety-bound behavior |
| --- | --- |
| `idle_cold_start_assessment` | Observe 20 minutes of runner idle time, then dispatch exactly one request; do not restart infrastructure. |
| `capacity_bounded_volume` | Use a dynamic owner-bound allocation for at most two active hours; there is no unconditional request count. |
| `sustained_2h` | Run for at most two active hours at the lower of 4 requests/second and the capacity-preflight rate. |
| `soak_24h` | Run for at most 24 active hours, no faster than one request/minute and at most 1,440 dispatches. |

Accepted error rate is `0%`. Every request has a `10,000 ms` latency ceiling.
Volume and sustained phases require p95 at or below `1,000 ms` and p99 at or
below `2,000 ms`; soak requires p95 at or below `1,500 ms` and p99 at or below
`3,000 ms`. These metrics remain aggregate-only.

Phases are sequential and do not use catch-up bursts. A restart-safe state
persists the global sequence, consumed allocation and all contract, activation,
target, capacity and phase-plan hashes. Resume cannot lower counters, reuse a
sequence or increase an approved allocation.

## Cold-Start Classification

The 20-minute idle observation alone does not prove a platform cold start.
`cold_start_classification` is `VERIFIED` only when authoritative server
telemetry proves that the server instance or server start epoch changed between
the bound baseline and the measured request.

When that change is absent, unchanged, unavailable or unprovable, the only
allowed classification is `INCONCLUSIVE`. Raw instance and start-epoch values
are never retained. Infrastructure is never restarted to force a result.

## Abort Behavior

The lane aborts without retry on:

- authentication failure or challenge
- any redirect response or `Location` signal
- any throttle status or throttle signal
- scheme, host, port, path, query, DNS, certificate or target-binding drift
- non-`200` status, schema failure or response above `1 MiB`
- request or aggregate phase-latency threshold breach
- exhaustion of the global dispatch, verified request/RU or Azure execution-unit budget
- stale or unavailable capacity or Azure Monitor evidence
- state corruption or evidence-redaction failure

An abort does not trigger rollback, deletion, permission or credential changes,
infrastructure restart, scaling or reconfiguration.

## Aggregate Evidence

Evidence is redacted JSON plus semantically matching Markdown and contains
aggregates only: phase counts and metrics, global dispatch count, verified
allowance fractions used, Azure execution units, Always Ready units, cold-start
classification, the instance/epoch-change boolean, hash bindings and an abort
reason code.

Evidence stores no per-request record, raw header, body, body hash, URL, path,
host, query, token, cookie, credential, tenant ID, user ID, server instance ID,
start epoch, provider response or Azure Monitor response. Unknown evidence
fields reject the artifact.

## Activation And Owner Gate

A future live command remains bound to redacted activation evidence whose final
status is exactly `PASSED`. The owner approval binds the activation, contract,
fixed target, capacity preflight, phase plan and correlation ID. The planned
command name is:

```text
nac m365 teams-sharepoint bff-performance-acceptance
```

It is not implemented by this documentation slice. Missing or mismatched
activation, owner, capacity or target bindings block before target dispatch.
