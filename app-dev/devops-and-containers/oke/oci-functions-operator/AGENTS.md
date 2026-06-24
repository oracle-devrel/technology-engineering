# OCI Functions Operator for OKE

## Goal

Build a Kubernetes operator that lets OKE users manage and invoke OCI Functions through Kubernetes-native CRDs.

## MVP

The MVP has two CRDs:

- Function
- FunctionJob

FunctionJob should support:
- functionRef
- inline JSON payloads
- parallelism
- retryLimit
- Kubernetes status aggregation

## Design principles

- Do not pretend OCI Functions are Kubernetes Pods.
- Do not support arbitrary PodTemplateSpec in v1alpha1.
- Prefer explicit validation errors over silent behavior.
- Keep OCI SDK access behind small interfaces.
- Make controllers idempotent.
- Make status useful from `kubectl get` and `kubectl describe`.
- Prefer small, testable packages.

## Out of scope for MVP

- Cron scheduling
- Event sources
- Native Kubernetes Job compatibility
- Volumes
- Sidecars
- Init containers
- GPU
- Privileged execution
- Full OCI Function lifecycle management before invocation spike works

## Build commands

Use:
- `make generate`
- `make manifests`
- `make test`

## Language

Go, Kubebuilder/controller-runtime.