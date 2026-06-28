#!/usr/bin/env python3
"""Validate generated synthetic datasets against explicit schema contracts.

This does not prove 100 percent production fidelity by itself. It validates
what the repo can measure locally:

- required top-level and nested fields
- field regex patterns
- required enumerated values
- provider-specific conditional patterns
- optional comparison against captured sample files when those exist
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from oci_config import PROJECT_DIR, TEST_DATA_DIR
from query_artifacts import is_generated_query_artifact

CONTRACT_PATH = Path(PROJECT_DIR) / "config" / "synthetic_log_contracts.json"


def load_contracts(path: Path = CONTRACT_PATH) -> dict[str, dict[str, Any]]:
    with path.open() as f:
        return json.load(f)


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open() as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}: invalid JSON on line {idx}: {exc}") from exc
    return records


def get_nested(record: dict[str, Any], dotted_path: str) -> Any:
    current: Any = record
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise KeyError(dotted_path)
        current = current[key]
    return current


def _sample_union_keys(sample_dir: Path) -> set[str]:
    keys: set[str] = set()
    for path in sorted(sample_dir.glob("*.jsonl")):
        for record in iter_jsonl(path):
            if isinstance(record, dict):
                keys.update(record.keys())
    return keys


def validate_contract(dataset_path: Path, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    records = iter_jsonl(dataset_path)
    if not records:
        return [f"{dataset_path.name}: dataset is empty"]

    minimum_events = contract.get("minimum_events")
    if minimum_events is not None and len(records) < minimum_events:
        errors.append(
            f"{dataset_path.name}: expected at least {minimum_events} events, found {len(records)}"
        )

    required_fields = contract.get("required_fields", [])
    required_nested_fields = contract.get("required_nested_fields", [])
    field_patterns = {
        field: re.compile(pattern)
        for field, pattern in contract.get("field_patterns", {}).items()
    }
    conditional_patterns = contract.get("conditional_patterns", [])
    required_values = contract.get("required_values", {})

    seen_values: dict[str, set[Any]] = {field: set() for field in required_values}

    for idx, record in enumerate(records, start=1):
        for field in required_fields:
            if field not in record:
                errors.append(f"{dataset_path.name}:{idx} missing field '{field}'")

        for dotted_field in required_nested_fields:
            try:
                get_nested(record, dotted_field)
            except KeyError:
                errors.append(f"{dataset_path.name}:{idx} missing nested field '{dotted_field}'")

        for field, pattern in field_patterns.items():
            if field in record and not pattern.search(str(record[field])):
                errors.append(
                    f"{dataset_path.name}:{idx} field '{field}' does not match pattern {pattern.pattern!r}"
                )

        for field in required_values:
            if field in record:
                seen_values[field].add(record[field])

        for condition in conditional_patterns:
            when = condition.get("when", {})
            if all(record.get(field) == expected for field, expected in when.items()):
                for field, regex in condition.get("field_patterns", {}).items():
                    if field not in record or not re.search(regex, str(record[field])):
                        errors.append(
                            f"{dataset_path.name}:{idx} field '{field}' failed conditional pattern {regex!r}"
                        )

    for field, expected_values in required_values.items():
        missing = sorted(set(expected_values) - seen_values[field])
        if missing:
            errors.append(f"{dataset_path.name}: missing required values for '{field}': {missing}")

    sample_dir_value = contract.get("sample_dir")
    if sample_dir_value:
        sample_dir = Path(PROJECT_DIR) / sample_dir_value
        if sample_dir.exists():
            sample_keys = _sample_union_keys(sample_dir)
            generated_keys = {key for record in records if isinstance(record, dict) for key in record.keys()}
            missing_keys = sorted(sample_keys - generated_keys)
            if missing_keys:
                errors.append(
                    f"{dataset_path.name}: generated keys missing from captured samples: {missing_keys}"
                )

    return errors


def validate_contract_filename(filename: str) -> str | None:
    """Return an error when a contract key is not a generated JSONL dataset."""
    if is_generated_query_artifact(filename):
        return f"{filename}: generated support artifact is not a synthetic JSONL dataset"
    if Path(filename).suffix != ".jsonl":
        return f"{filename}: contract filename must target a .jsonl dataset"
    return None


def find_uncovered_datasets(test_data_dir: Path, contracts: dict[str, Any]) -> list[str]:
    """Return ``test_data/*.jsonl`` files that have no registered contract.

    Ingestion-time guard: a synthetic dataset that ships without a schema
    contract is silently unvalidated, so a shape regression in it would reach
    the parser/dashboard unchecked. Generated support artifacts (manifest,
    plans, etc.) are intentionally not datasets and are skipped.
    """
    if not test_data_dir.exists():
        return []
    covered = set(contracts.keys())
    uncovered = []
    for path in sorted(test_data_dir.glob("*.jsonl")):
        if is_generated_query_artifact(path.name):
            continue
        if path.name not in covered:
            uncovered.append(path.name)
    return uncovered


def validate_all(test_data_dir: Path = Path(TEST_DATA_DIR), contracts_path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contracts = load_contracts(contracts_path)
    results = {}
    total_errors = 0

    for filename, contract in contracts.items():
        filename_error = validate_contract_filename(filename)
        if filename_error:
            results[filename] = {"ok": False, "errors": [filename_error]}
            total_errors += 1
            continue

        dataset_path = test_data_dir / filename
        if not dataset_path.exists():
            # Optional datasets (e.g. the Octo APM workshop bundle) come from a
            # separate generator and are not part of the core run; skip them when
            # absent instead of failing. Core datasets must be present.
            if contract.get("optional"):
                results[filename] = {"ok": True, "errors": [], "skipped": "dataset not present (optional)"}
                continue
            results[filename] = {"ok": False, "errors": [f"{filename}: dataset not found"]}
            total_errors += 1
            continue

        errors = validate_contract(dataset_path, contract)
        results[filename] = {"ok": not errors, "errors": errors}
        total_errors += len(errors)

    # Coverage gate: every present .jsonl dataset must have a contract.
    uncovered = find_uncovered_datasets(test_data_dir, contracts)
    for filename in uncovered:
        results[filename] = {
            "ok": False,
            "errors": [f"{filename}: dataset present in test_data/ but has no schema contract"],
        }
        total_errors += 1

    return {
        "ok": total_errors == 0,
        "total_errors": total_errors,
        "uncovered_datasets": uncovered,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate synthetic datasets against schema contracts")
    parser.add_argument("--contracts", default=str(CONTRACT_PATH), help="Path to contract JSON")
    parser.add_argument("--test-data-dir", default=str(TEST_DATA_DIR), help="Directory containing generated JSONL files")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    args = parser.parse_args()

    report = validate_all(
        test_data_dir=Path(args.test_data_dir),
        contracts_path=Path(args.contracts),
    )

    if args.json:
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["ok"] else 1)

    print("=" * 60)
    print("Synthetic Log Contract Validation")
    print("=" * 60)
    for filename, result in report["results"].items():
        status = "OK" if result["ok"] else "FAIL"
        print(f"[{status:4s}] {filename}")
        for error in result["errors"][:5]:
            print(f"  - {error}")
        if len(result["errors"]) > 5:
            print(f"  - ... {len(result['errors']) - 5} more")

    print(f"\nTotal contract errors: {report['total_errors']}")
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
