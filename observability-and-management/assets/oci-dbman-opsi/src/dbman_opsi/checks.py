"""Structured results for preflight and configure decisioning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CheckStatus = Literal["pass", "fail", "warn", "manual", "skip"]

# Statuses that do not block an --apply enablement run.
_NON_BLOCKING: frozenset[CheckStatus] = frozenset({"pass", "warn", "manual", "skip"})


@dataclass(frozen=True)
class CheckResult:
    """One read-only prerequisite check."""

    name: str
    status: CheckStatus
    detail: str
    remediation: str | None = None

    @property
    def blocking(self) -> bool:
        return self.status not in _NON_BLOCKING

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "remediation": self.remediation,
        }


def ok(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "pass", detail)


def fail(name: str, detail: str, remediation: str) -> CheckResult:
    return CheckResult(name, "fail", detail, remediation)


def warn(name: str, detail: str, remediation: str | None = None) -> CheckResult:
    return CheckResult(name, "warn", detail, remediation)


def manual(name: str, detail: str, remediation: str | None = None) -> CheckResult:
    return CheckResult(name, "manual", detail, remediation)


def skip(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "skip", detail)


@dataclass(frozen=True)
class TargetReport:
    """Preflight results for one configured target."""

    name: str
    kind: str
    location: Literal["oci-native", "management-agent"]
    checks: tuple[CheckResult, ...] = ()

    @property
    def blocking_failures(self) -> tuple[CheckResult, ...]:
        return tuple(check for check in self.checks if check.blocking)

    @property
    def ok(self) -> bool:
        return not self.blocking_failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "location": self.location,
            "ok": self.ok,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True)
class PreflightReport:
    """Tenancy-wide and per-target prerequisite results."""

    tenancy_checks: tuple[CheckResult, ...] = ()
    network_checks: tuple[CheckResult, ...] = ()
    targets: tuple[TargetReport, ...] = field(default_factory=tuple)

    @property
    def shared_checks(self) -> tuple[CheckResult, ...]:
        return self.tenancy_checks + self.network_checks

    @property
    def ok(self) -> bool:
        shared_ok = not any(check.blocking for check in self.shared_checks)
        return shared_ok and all(target.ok for target in self.targets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tenancy_checks": [check.to_dict() for check in self.tenancy_checks],
            "network_checks": [check.to_dict() for check in self.network_checks],
            "targets": [target.to_dict() for target in self.targets],
        }
