#!/bin/bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "${SKILL_DIR}/../../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

echo "Checking Terraform formatting"
terraform fmt -check -recursive

echo "Validating Terraform configuration"
terraform validate

echo "Running regression tests"
if ! "$PYTHON_BIN" -c "import yaml" 2>/dev/null; then
  echo "PyYAML is required by the regression tests; set PYTHON_BIN to a Python environment that provides it." >&2
  exit 1
fi
"$PYTHON_BIN" -m unittest discover -s tests

echo "Checking shell syntax"
while IFS= read -r -d '' script_path; do
  bash -n "$script_path"
done < <(find repos/pipelines/script repos/cluster-admin/script script -type f -name '*.sh' -print0 2>/dev/null)

echo "Linting generated Helm charts"
while IFS= read -r chart_file; do
  helm lint "$(dirname "$chart_file")"
done < <(find repos/generated/charts -type f -name Chart.yaml -print 2>/dev/null | sort)

echo "Maintainer validation succeeded"
