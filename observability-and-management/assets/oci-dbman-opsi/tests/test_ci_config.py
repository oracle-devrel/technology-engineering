import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_pyyaml_dependency_is_bounded_to_tested_major() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "PyYAML>=6.0.1,<7" in pyproject["project"]["dependencies"]


def test_ci_has_dependency_audit_job() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    deps = workflow["jobs"]["deps"]
    commands = "\n".join(
        step.get("run", "")
        for step in deps["steps"]
        if isinstance(step, dict)
    )

    assert "pip install pip-audit" in commands
    assert "pip-audit" in commands
