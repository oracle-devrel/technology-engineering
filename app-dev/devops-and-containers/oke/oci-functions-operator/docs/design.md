# OCI Functions Operator Design

## Problem Statement

OKE users often want Kubernetes-native workflows around OCI Functions: declare a function target, submit invocation work, track progress, and inspect failures through `kubectl`. Without an operator, teams must wire ad hoc scripts, CI jobs, or application-specific controllers that duplicate OCI authentication, invocation retry behavior, and status reporting.

The OCI Functions Operator provides a small Kubernetes API for managing and invoking OCI Functions while keeping the OCI SDK details behind narrow internal boundaries.

## Why CRDs And An Operator

CRDs let users describe function invocation work with normal Kubernetes resources, RBAC, audit trails, and status. An operator can reconcile those resources idempotently, aggregate per-payload state, emit Kubernetes events, and make progress visible through `kubectl get` and `kubectl describe`.

This is intentionally not modeled as Pods or Kubernetes Jobs. OCI Functions are external serverless resources, so the operator tracks invocation intent and observed outcomes instead of pretending each invocation is a pod lifecycle.

## MVP Scope

The operator currently exposes four namespaced resources in `functions.oci.oracle.com/v1alpha1`:

- `Function`: either references an existing OCI Function by `spec.functionId` and `spec.invokeEndpoint`, or manages an OCI Functions application/function from desired config.
- `FunctionJob`: references a `Function`, carries inline JSON payloads, controls per-reconcile parallelism, applies retry limits, and records status aggregation.
- `FunctionEventTrigger`: routes an OCI Events Rule event type or Kubernetes-native `functionevent.*` event type to a referenced `Function`.
- `FunctionEvent`: Kubernetes-native event object matched against `FunctionEventTrigger.spec.condition.eventType`.

Implemented invoker modes:

- `fake`: deterministic local success path for development and demos.
- `oci`: OCI Go SDK-backed lifecycle, invocation, and OCI Events rule management.

## Non-Goals

- Cron scheduling.
- DAG/workflow orchestration.
- Kubernetes resource watch triggers.
- Native Kubernetes Job compatibility.
- Pod templates, volumes, sidecars, init containers, GPUs, or privileged execution.
- Image publishing, function source builds, or deployment packaging.
- Deleting OCI Functions or applications.
- Long-running durable queue semantics for large batches.

## Architecture

The controller manager runs four reconcilers:

- `FunctionReconciler` resolves a `Function` into a ready, pending, or error status. Existing function references validate required fields; managed functions ensure an OCI Functions application and function.
- `FunctionJobReconciler` resolves the referenced `Function`, initializes per-payload status, invokes runnable payloads through `invoker.Interface`, aggregates status, and emits events.
- `FunctionEventTriggerReconciler` creates or updates OCI Events Rules for OCI event types and treats `functionevent.*` triggers as Kubernetes-native routes.
- `FunctionEventReconciler` matches `FunctionEvent.spec.eventType` against same-namespace FunctionEventTriggers and invokes the referenced Functions through `invoker.Interface`.

OCI SDK usage is isolated under `internal/invoker`, `internal/lifecycle`, and `internal/eventtrigger`. Controllers depend only on small internal interfaces:

```go
type Interface interface {
    Invoke(ctx context.Context, request Request) (Response, error)
}

type Manager interface {
    EnsureFunction(ctx context.Context, desired DesiredFunction) (FunctionState, error)
}

type EventTriggerManager interface {
    EnsureRule(ctx context.Context, desired DesiredRule) (RuleState, error)
    DeleteRule(ctx context.Context, ruleID string) (RuleState, error)
}
```

An optional `FunctionIDRequirement` capability lets OCI mode tell the job controller that the referenced `Function` must resolve an OCI Function OCID. This keeps controllers independent of OCI SDK concrete types while still validating OCI-mode requirements early.

## Function Lifecycle

`Function.spec.mode` can be `Existing` or `Managed`. When omitted, the controller infers mode from existing references or `spec.config`.

When existing mode is used:

- `status.phase` becomes `Ready`.
- `status.functionId`, `status.functionOcid`, and `status.invokeEndpoint` are populated from spec.
- the `Ready` condition is set to true.
- missing `spec.functionId` or missing `spec.invokeEndpoint` makes the Function `Error`.

When managed mode is used:

- the controller ensures the OCI Functions application exists.
- the controller creates the application with requested subnet IDs and NSG IDs.
- the controller reconciles application NSG IDs when `spec.config.nsgIds` is set.
- the controller ensures the OCI Function exists.
- image, memory, timeout, and config are updated when they drift.
- `status.applicationId`, `status.functionId`, and `status.invokeEndpoint` are populated from OCI responses.
- `status.phase` remains `Pending` until the application/function metadata is usable and the function is active with an invoke endpoint.

Managed mode config includes region, compartment OCID, application name, subnet OCIDs, optional application NSG OCIDs, image, memory, timeout, and function config. Jeddah is represented with the OCI region identifier `me-jeddah-1`.

`spec.config.nsgIds` has deliberate reconciliation semantics:

- omitted: leave NSGs unmanaged on existing applications.
- empty list: explicitly clear all NSGs from the application.
- non-empty list: create new applications with those NSGs and reconcile existing applications to that desired set.

OCI Functions pulls the function runtime image during invocation, not as an operator pod. The Functions application subnet must route to Oracle Services Network/OCIR, and any NSGs attached through `spec.config.nsgIds` must allow egress TCP 443 to Oracle Services Network/OCIR. Missing NSG egress can present as `FunctionInvokeImageNotAvailable: Failed to pull function image`, even when the OCIR repository is public or otherwise accessible.

The function runtime image must be an OCI Functions-compatible Fn image in same-region OCIR. For Jeddah, that means `jed.ocir.io/...`. The operator/controller image is separate and may be hosted in GHCR or another registry OKE can pull.

## FunctionJob Lifecycle

A `FunctionJob` starts by resolving `spec.functionRef.name` in the same namespace.

If the `Function` is missing or not ready:

- a missing `Function` leaves the job `Pending`.
- a non-Ready `Function` fails the job clearly without invoking.
- conditions explain why no invocation has started.

When the `Function` is ready:

- inline payloads are normalized into ordered per-payload status entries.
- succeeded payloads are never invoked again.
- pending or retryable failed payloads are invoked up to `spec.parallelism` per reconcile.
- each payload gets attempts, phase, status code, invocation ID, OCI request ID, error, and completion time.

When all payloads succeed:

- `status.phase` becomes `Succeeded`.
- `Complete` is true.
- a normal completion event is emitted.

When one or more payloads exhaust retries:

- `status.phase` becomes `Failed`.
- `Failed` is true.
- `status.lastError` and the per-payload error carry the most useful bounded failure details.
- warning events are emitted.

## Fake Mode Vs OCI Mode

`INVOKER_MODE=fake` is the default. It returns deterministic successful responses and is intended for local demos, controller development, and CI-friendly tests. It does not contact OCI.

`INVOKER_MODE=oci` constructs an OCI Go SDK Functions invoke client. It requires:

- `OCI_AUTH_MODE=workload` for OKE Workload Identity, which is the default when `OCI_AUTH_MODE` is unset.
- `OCI_AUTH_MODE=config` only for local development with an OCI config file/profile.
- existing-mode `Function` resources to use `spec.functionId` and `spec.invokeEndpoint`.
- managed-mode `Function` resources to produce `status.functionId` and `status.invokeEndpoint` before jobs invoke.

OCI mode records `Fn-Call-Id` when available, otherwise `opc-request-id`, and stores the OCI request ID separately as `lastOciRequestId` and per-payload `ociRequestId`.

## Known Limitations

- Managed lifecycle currently reconciles application/function create, application NSG updates, and function update only; deletion and finalizers are not implemented.
- Existing mode requires the user to provide the invoke endpoint in `spec.invokeEndpoint`.
- Inline payloads are intended for small demos and operational jobs, not large queues.
- Large jobs should eventually use Object Storage, Queue, or Streaming payload sources instead of embedding all payloads in the CR.
- Retry behavior is local to reconciliation and status, not a durable external work queue.
- This is not a generic Kubernetes Job compatibility layer.
- The API intentionally does not expose `PodTemplateSpec`, volumes, sidecars, init containers, GPUs, or privileged execution.
- Function runtime images must be OCI Functions-compatible and stored in same-region OCIR.
- There is no admission webhook yet for cross-field validation beyond CRD CEL rules.
- Function response bodies are captured internally by the invoker response but are not surfaced in `FunctionJob` status.
- OCI mode currently supports OKE Workload Identity and local OCI config-file auth only.
