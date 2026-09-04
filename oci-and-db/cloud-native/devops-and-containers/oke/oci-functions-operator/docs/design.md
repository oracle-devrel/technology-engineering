# OCI Functions Operator Design

## Problem Statement

OKE users often want Kubernetes-native workflows around OCI Functions: declare a function target, submit invocation work, track progress, and inspect failures through `kubectl`. Without an operator, teams must wire ad hoc scripts, CI jobs, or application-specific controllers that duplicate OCI authentication, invocation retry behavior, and status reporting.

The OCI Functions Operator provides a small Kubernetes API for managing and invoking OCI Functions while keeping the OCI SDK details behind narrow internal boundaries.

## Why CRDs And An Operator

CRDs let users describe function invocation work with normal Kubernetes resources, RBAC, audit trails, and status. An operator can reconcile those resources idempotently, aggregate per-payload state, emit Kubernetes events, and make progress visible through `kubectl get` and `kubectl describe`.

This is intentionally not modeled as Pods or Kubernetes Jobs. OCI Functions are external serverless resources, so the operator tracks invocation intent and observed outcomes instead of pretending each invocation is a pod lifecycle.

## Current Scope

The operator currently exposes five namespaced resources in `functions.oci.oracle.com/v1alpha1`:

- `FunctionApplication`: creates, updates, or resolves an OCI Functions Application, including compartment, region, subnet IDs, NSG IDs, and application-level config.
- `Function`: either references an existing OCI Function by `spec.functionId` and `spec.invokeEndpoint`, or manages an OCI Function inside a referenced `FunctionApplication`. Legacy one-object managed config remains supported.
- `FunctionJob`: references a `Function`, carries inline JSON payloads, controls per-reconcile parallelism, applies retry limits, and records status aggregation.
- `FunctionEventTrigger`: routes an OCI Events Rule event type or Kubernetes-native `functionevent.*` event type to a referenced `Function`.
- `FunctionEvent`: Kubernetes-native event object matched against `FunctionEventTrigger.spec.condition.eventType`.

Implemented invoker modes:

- `fake`: deterministic local success path for development and tests.
- `oci`: OCI Go SDK-backed lifecycle, invocation, and OCI Events rule management.

## Non-Goals

- Cron scheduling.
- DAG/workflow orchestration.
- Kubernetes resource watch triggers.
- Native Kubernetes Job compatibility.
- Pod templates, volumes, sidecars, init containers, GPUs, or privileged execution.
- Image publishing, function source builds, or deployment packaging.
- Force-deleting OCI Functions applications that still contain functions.
- Long-running durable queue semantics for large batches.

## Architecture

The controller manager runs five reconcilers:

- `FunctionApplicationReconciler` resolves or reconciles the OCI Functions Application and records its OCID/readiness.
- `FunctionReconciler` resolves a `Function` into a ready, pending, or error status. Existing function references validate required fields; managed functions wait for any referenced `FunctionApplication` and then ensure an OCI Function.
- `FunctionJobReconciler` resolves the referenced `Function`, initializes per-payload status, invokes runnable payloads through `invoker.Interface`, aggregates status, and emits events.
- `FunctionEventTriggerReconciler` creates or updates OCI Events Rules for OCI event types and treats `functionevent.*` triggers as Kubernetes-native routes.
- `FunctionEventReconciler` matches `FunctionEvent.spec.eventType` against same-namespace FunctionEventTriggers and invokes the referenced Functions through `invoker.Interface`.

OCI SDK usage is isolated under `internal/invoker`, `internal/lifecycle`, and `internal/eventtrigger`. Controllers depend only on small internal interfaces:

```go
type Interface interface {
    Invoke(ctx context.Context, request Request) (Response, error)
}

type Manager interface {
    EnsureApplication(ctx context.Context, desired DesiredApplication) (ApplicationState, error)
    EnsureFunction(ctx context.Context, desired DesiredFunction) (FunctionState, error)
    EnsureFunctionInApplication(ctx context.Context, desired DesiredFunctionInApplication) (FunctionState, error)
    DeleteManagedFunction(ctx context.Context, target ManagedFunctionDeleteTarget) (FunctionDeletionState, error)
    DeleteApplication(ctx context.Context, target ApplicationDeleteTarget) (ApplicationDeletionState, error)
}

type EventTriggerManager interface {
    EnsureRule(ctx context.Context, desired DesiredRule) (RuleState, error)
    DeleteRule(ctx context.Context, ruleID string) (RuleState, error)
}
```

An optional `FunctionIDRequirement` capability lets OCI mode tell the job controller that the referenced `Function` must resolve an OCI Function OCID. This keeps controllers independent of OCI SDK concrete types while still validating OCI-mode requirements early.

## FunctionApplication Lifecycle

`FunctionApplication` maps directly to an OCI Functions Application. It is the preferred place for application-scoped settings:

- `spec.region`
- `spec.compartmentId`
- `spec.displayName`
- `spec.subnetIds`
- `spec.nsgIds`
- `spec.config`
- `spec.logging.invocationLogs`

Managed applications are created if missing and have mutable NSG IDs and application config reconciled. OCI Functions does not expose subnet mutation through the update API, so subnet drift is reported clearly instead of silently ignored.

Existing applications are resolved by `spec.existingApplicationId` or by display name, compartment, and region. Existing mode never deletes OCI resources.

`spec.nsgIds` has deliberate reconciliation semantics:

- omitted: leave NSGs unmanaged on existing/adopted applications.
- empty list: explicitly clear all NSGs from the application.
- non-empty list: create new applications with those NSGs and reconcile existing applications to that desired set.

`FunctionApplication.spec.deletionPolicy` defaults to `Retain`. `Delete` is honored only for managed applications and only when no functions remain in the OCI Application; otherwise deletion is blocked with status/events and retried.

`FunctionApplication.spec.logging.invocationLogs` configures OCI Functions application invocation log settings and ensures an OCI Logging service log in the existing `logGroupId`. The operator creates or updates the service log for the resolved Functions application and sets the Functions application log line format.

## Function Lifecycle

`Function.spec.mode` can be `Existing` or `Managed`. When omitted, the controller infers mode from existing references or `spec.config`.

When existing mode is used:

- `status.phase` becomes `Ready`.
- `status.functionId`, `status.functionOcid`, and `status.invokeEndpoint` are populated from spec.
- the `Ready` condition is set to true.
- missing `spec.functionId` or missing `spec.invokeEndpoint` makes the Function `Error`.

When managed mode is used:

- with `spec.applicationRef.name`, the controller waits for the referenced `FunctionApplication` to be Ready and uses its `status.applicationId`.
- without `spec.applicationRef.name`, the controller preserves the legacy behavior of ensuring the OCI Functions application from `spec.config`.
- the controller ensures the OCI Function exists.
- image, memory, timeout, and config are updated when they drift.
- `status.applicationId`, `status.functionId`, and `status.invokeEndpoint` are populated from OCI responses.
- `status.phase` remains `Pending` until the application/function metadata is usable and the function is active with an invoke endpoint.

Preferred managed mode keeps only function-level settings in `Function.spec.config`: display name, image, memory, timeout, and function config. Legacy managed mode still accepts region, compartment OCID, application name, subnet OCIDs, and optional application NSG OCIDs under `Function.spec.config` for backward compatibility. Jeddah is represented with the OCI region identifier `me-jeddah-1`.

OCI Functions pulls the function runtime image during invocation, not as an operator pod. The Functions application subnet must route to Oracle Services Network/OCIR, and any NSGs attached through `FunctionApplication.spec.nsgIds` or legacy `Function.spec.config.nsgIds` must allow egress TCP 443 to Oracle Services Network/OCIR. Missing NSG egress can present as `FunctionInvokeImageNotAvailable: Failed to pull function image`, even when the OCIR repository is public or otherwise accessible.

The function runtime image must be an OCI Functions-compatible Fn image in same-region OCIR. For Jeddah, that means `jed.ocir.io/...`. The operator/controller image is separate and may be hosted in GHCR or another registry OKE can pull.

Managed `Function` deletion is opt-in through `spec.deletionPolicy: Delete`. The default `Retain` policy leaves OCI resources untouched. In Delete mode the controller uses a finalizer, deletes the managed OCI Function, and treats already-missing OCI Functions as successful cleanup. Application cleanup is controlled separately by `FunctionApplication.spec.deletionPolicy`. Existing-mode Functions never delete OCI resources.

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

`INVOKER_MODE=fake` is the default. It returns deterministic successful responses and is intended for local controller development and CI-friendly tests. It does not contact OCI.

`INVOKER_MODE=oci` constructs an OCI Go SDK Functions invoke client. It requires:

- `OCI_AUTH_MODE=workload` for OKE Workload Identity, which is the default when `OCI_AUTH_MODE` is unset.
- `OCI_AUTH_MODE=config` only for local development with an OCI config file/profile.
- existing-mode `Function` resources to use `spec.functionId` and `spec.invokeEndpoint`.
- managed-mode `Function` resources to produce `status.functionId` and `status.invokeEndpoint` before jobs invoke.

OCI mode records `Fn-Call-Id` when available, otherwise `opc-request-id`, and stores the OCI request ID separately as `lastOciRequestId` and per-payload `ociRequestId`.

## Known Limitations

- Managed lifecycle reconciles FunctionApplication create/adopt/update, application NSG/config updates, Function create/update, opt-in OCI Function deletion, and opt-in empty OCI Application deletion.
- Existing mode requires the user to provide the invoke endpoint in `spec.invokeEndpoint`.
- Inline payloads are intended for small operational jobs, not large queues.
- Large jobs should eventually use Object Storage, Queue, or Streaming payload sources instead of embedding all payloads in the CR.
- Retry behavior is local to reconciliation and status, not a durable external work queue.
- This is not a generic Kubernetes Job compatibility layer.
- The API intentionally does not expose `PodTemplateSpec`, volumes, sidecars, init containers, GPUs, or privileged execution.
- Function runtime images must be OCI Functions-compatible and stored in same-region OCIR.
- There is no admission webhook yet for cross-field validation beyond CRD CEL rules.
- Function response bodies are captured internally by the invoker response but are not surfaced in `FunctionJob` status.
- OCI mode currently supports OKE Workload Identity and local OCI config-file auth only.
