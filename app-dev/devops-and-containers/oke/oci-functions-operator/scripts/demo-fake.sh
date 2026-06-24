#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-default}"
FUNCTION_NAME="${FUNCTION_NAME:-existing-hello}"
JOB_NAME="${JOB_NAME:-hello-job}"
WATCH_SECONDS="${WATCH_SECONDS:-60}"
MODE="${INVOKER_MODE:-fake}"
DEMO_LABEL_VALUE="oci-functions-operator-fake"

if [[ "$MODE" != "fake" ]]; then
  echo "error: scripts/demo-fake.sh is for fake mode. Set INVOKER_MODE=fake or unset it." >&2
  exit 1
fi

"$ROOT_DIR/scripts/check-demo-prereqs.sh"

guard_demo_resource() {
  local kind="$1"
  local name="$2"
  local label

  if ! kubectl get "$kind" "$name" -n "$NAMESPACE" >/dev/null 2>&1; then
    return
  fi

  label="$(kubectl get "$kind" "$name" -n "$NAMESPACE" -o jsonpath='{.metadata.labels.demo}' 2>/dev/null || true)"
  if [[ "$label" != "$DEMO_LABEL_VALUE" ]]; then
    echo "error: $kind/$name already exists in namespace $NAMESPACE and is not labeled demo=$DEMO_LABEL_VALUE." >&2
    echo "Refusing to overwrite an unrelated resource." >&2
    exit 1
  fi
}

guard_demo_resource function "$FUNCTION_NAME"
guard_demo_resource functionjob "$JOB_NAME"

echo "Applying fake-mode sample resources in namespace $NAMESPACE..."
echo "Fake mode does not contact OCI, create OCI resources, or validate function runtime images."
kubectl apply -n "$NAMESPACE" -f "$ROOT_DIR/config/samples/functions_v1alpha1_function_existing.yaml"
kubectl apply -n "$NAMESPACE" -f "$ROOT_DIR/config/samples/functions_v1alpha1_functionjob.yaml"

echo "Watching FunctionJob/$JOB_NAME for up to ${WATCH_SECONDS}s..."
deadline=$((SECONDS + WATCH_SECONDS))

while true; do
  phase="$(kubectl get functionjob "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  succeeded="$(kubectl get functionjob "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.succeeded}' 2>/dev/null || true)"
  failed="$(kubectl get functionjob "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.failed}' 2>/dev/null || true)"
  last_error="$(kubectl get functionjob "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.lastError}' 2>/dev/null || true)"

  printf 'phase=%s succeeded=%s failed=%s' "${phase:-<pending>}" "${succeeded:-0}" "${failed:-0}"
  if [[ -n "$last_error" ]]; then
    printf ' lastError=%s' "$last_error"
  fi
  printf '\n'

  if [[ "$phase" == "Succeeded" || "$phase" == "Failed" ]]; then
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for FunctionJob/$JOB_NAME to reach Succeeded or Failed." >&2
    break
  fi
  sleep 2
done

echo
echo "Describe output for FunctionJob/$JOB_NAME:"
kubectl describe functionjob "$JOB_NAME" -n "$NAMESPACE"
