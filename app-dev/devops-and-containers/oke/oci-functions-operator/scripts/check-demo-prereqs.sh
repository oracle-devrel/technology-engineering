#!/usr/bin/env bash
set -euo pipefail

MODE="${INVOKER_MODE:-fake}"
OCI_MODE_AUTH="${OCI_AUTH_MODE:-workload}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Checking demo prerequisites..."

if ! command -v kubectl >/dev/null 2>&1; then
  echo "error: kubectl is not available on PATH" >&2
  exit 1
fi

echo "kubectl: $(kubectl version --client=true --short 2>/dev/null || kubectl version --client=true)"

if ! kubectl get crd functions.functions.oci.oracle.com >/dev/null 2>&1; then
  echo "error: Function CRD is not installed. Run: make manifests && kubectl apply -k config/crd" >&2
  exit 1
fi

if ! kubectl get crd functionjobs.functions.oci.oracle.com >/dev/null 2>&1; then
  echo "error: FunctionJob CRD is not installed. Run: make manifests && kubectl apply -k config/crd" >&2
  exit 1
fi

case "$MODE" in
  fake)
    if [[ -z "${INVOKER_MODE:-}" ]]; then
      echo "INVOKER_MODE is not set; manager defaults to fake."
    else
      echo "INVOKER_MODE=fake"
    fi
    echo "Fake mode requires no OCI auth, creates no OCI resources, and does not validate OCI Functions image compatibility or network egress."
    ;;
  oci)
    echo "INVOKER_MODE=oci"
    echo "No global OCI_FUNCTIONS_INVOKE_ENDPOINT is required."
    echo "Existing-mode Function resources must set spec.invokeEndpoint; managed Functions discover status.invokeEndpoint."
    case "$OCI_MODE_AUTH" in
      workload)
        if [[ -z "${OCI_AUTH_MODE:-}" ]]; then
          echo "OCI_AUTH_MODE is not set; OCI mode defaults to workload."
        else
          echo "OCI_AUTH_MODE=workload"
        fi
        echo "OKE Workload Identity is expected; no OCI config file, PEM key, or credential Secret is required."
        echo "For managed Functions, verify subnet routing and any application NSG egress allow TCP 443 to Oracle Services Network/OCIR."
        ;;
      config)
        echo "OCI_AUTH_MODE=config"
        CONFIG_FILE="${OCI_CONFIG_FILE:-$HOME/.oci/config}"
        if [[ ! -f "$CONFIG_FILE" ]]; then
          echo "error: OCI config file not found at $CONFIG_FILE" >&2
          exit 1
        fi
        echo "OCI_CONFIG_FILE=$CONFIG_FILE"
        echo "OCI_CONFIG_PROFILE=${OCI_CONFIG_PROFILE:-DEFAULT}"
        echo "Config auth is for local existing-function demos and local development only."
        ;;
      *)
        echo "error: unsupported OCI_AUTH_MODE=$OCI_MODE_AUTH. Supported values: workload, config" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    echo "error: unsupported INVOKER_MODE=$MODE. Supported values: fake, oci" >&2
    exit 1
    ;;
esac

MANAGED_SAMPLE="$ROOT_DIR/config/samples/functions_v1alpha1_function_managed.yaml"
if [[ -f "$MANAGED_SAMPLE" ]]; then
  if grep -Eq 'image:[[:space:]]*ghcr\.io/' "$MANAGED_SAMPLE"; then
    echo "warning: managed sample function image points at GHCR. OCI Functions runtime images should use same-region OCIR." >&2
  fi
  if grep -Eq 'image:[[:space:]]*me-jeddah-1\.ocir\.io/' "$MANAGED_SAMPLE"; then
    echo "warning: Jeddah OCIR image references should use jed.ocir.io, not me-jeddah-1.ocir.io." >&2
  fi
fi

echo "Demo prerequisites look good."
