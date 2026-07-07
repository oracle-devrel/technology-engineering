"""Configuration model and YAML/JSON serialization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Literal, get_args

import yaml

from dbman_opsi.redact import redact_data

TargetKind = Literal["dbcs", "autonomous", "exadata", "external-db", "external-exadata"]

# The three observability/security/management pillars a target can opt into.
# "dbm" = Database Management, "opsi" = Operations Insights, "datasafe" = Data Safe.
Service = Literal["dbm", "opsi", "datasafe"]
DEFAULT_SERVICES: tuple[Service, ...] = ("dbm", "opsi")
ALLOWED_TARGET_KINDS = frozenset(get_args(TargetKind))
ALLOWED_SERVICES = frozenset(get_args(Service))
OCID_PREFIX_RE = re.compile(r"^ocid1\.[a-z0-9]+\.oc[0-9]\.")
REGION_RE = re.compile(r"^[a-z]+-[a-z]+-[0-9]+$")
MAX_OCID_LENGTH = 255


class ConfigError(ValueError):
    """Raised when loaded config fails boundary validation."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        message = "Invalid config:\n- " + "\n- ".join(problems)
        super().__init__(message)


@dataclass(frozen=True)
class NetworkSelection:
    vcn_id: str | None = None
    subnet_id: str | None = None
    create_test_network: bool = False
    cidr_block: str = "10.44.0.0/16"
    subnet_cidr_block: str = "10.44.10.0/24"


@dataclass(frozen=True)
class VaultSelection:
    vault_id: str | None = None
    key_id: str | None = None
    create_vault: bool = False


@dataclass(frozen=True)
class Target:
    kind: TargetKind
    name: str
    compartment_id: str | None = None
    resource_id: str | None = None
    service_name: str | None = None
    monitoring_user: str | None = None
    password_secret_id: str | None = None
    wallet_secret_id: str | None = None
    private_endpoint_id: str | None = None
    opsi_private_endpoint_id: str | None = None
    opsi_database_insight_id: str | None = None
    opsi_connection_details_file: str | None = None
    opsi_credential_details_file: str | None = None
    management_agent_id: str | None = None
    deployment_type: Literal["VIRTUAL_MACHINE", "BARE_METAL", "EXACC", "EXACS"] = "VIRTUAL_MACHINE"
    database_resource_type: str = "database"
    database_role: Literal["CDB", "PDB", "NON_CDB"] = "CDB"
    parent_cdb_id: str | None = None
    management_type: Literal["BASIC", "ADVANCED"] = "ADVANCED"
    provision: bool = False
    external_host: str | None = None
    external_os: Literal["linux", "windows", "solaris", "aix"] | None = None
    # Parent DB system OCID (Base DB / Exadata). Data Safe's DATABASE_CLOUD_SERVICE
    # registration keys off the DB system + service name rather than the DB OCID.
    db_system_id: str | None = None
    # Data Safe: the registered target-database is a separate resource keyed back
    # to this DB; its Data Safe private endpoint lives in the DB subnet.
    data_safe_target_id: str | None = None
    data_safe_private_endpoint_id: str | None = None
    # Which pillars to enable for this target. Defaults to DBM + OPSI so existing
    # configs (which omit the field) keep their prior behavior; Data Safe is opt-in.
    services: tuple[Service, ...] = DEFAULT_SERVICES
    # Optional override for targets that live outside the config home region.
    # Appended to preserve the positional dataclass argument order used by older
    # callers.
    region: str | None = None

    def wants(self, service: Service) -> bool:
        return service in self.services


@dataclass(frozen=True)
class EnablementConfig:
    profile: str
    region: str
    monitoring_regions: tuple[str, ...] = ()
    tenancy_id: str | None = None
    compartment_id: str | None = None
    network: NetworkSelection = field(default_factory=NetworkSelection)
    vault: VaultSelection = field(default_factory=VaultSelection)
    targets: tuple[Target, ...] = ()
    policy_group_name: str = "dbman-opsi-admins"
    dry_run: bool = True
    terraform_dir: str = "terraform/examples/zero-start-poc"

    def sanitized(self) -> dict[str, Any]:
        return redact_data(to_dict(self))


def _network_from_dict(value: dict[str, Any] | None) -> NetworkSelection:
    return NetworkSelection(**(value or {}))


def _vault_from_dict(value: dict[str, Any] | None) -> VaultSelection:
    return VaultSelection(**(value or {}))


def _target_from_dict(value: dict[str, Any]) -> Target:
    data = dict(value)
    if "services" in data and data["services"] is not None:
        data["services"] = tuple(data["services"])
    return Target(**data)


def _target_to_dict(target: Target) -> dict[str, Any]:
    # YAML safe_dump cannot represent tuples, so normalize services to a list.
    data = dict(target.__dict__)
    data["services"] = list(target.services)
    return data


def from_dict(value: dict[str, Any]) -> EnablementConfig:
    """Create an immutable config object from raw dict data."""

    return EnablementConfig(
        profile=value["profile"],
        region=value["region"],
        monitoring_regions=tuple(value.get("monitoring_regions") or ()),
        tenancy_id=value.get("tenancy_id"),
        compartment_id=value.get("compartment_id"),
        network=_network_from_dict(value.get("network")),
        vault=_vault_from_dict(value.get("vault")),
        targets=tuple(_target_from_dict(item) for item in value.get("targets", [])),
        policy_group_name=value.get("policy_group_name", "dbman-opsi-admins"),
        dry_run=bool(value.get("dry_run", True)),
        terraform_dir=value.get("terraform_dir", "terraform/examples/zero-start-poc"),
    )


def validate_config(config: EnablementConfig) -> list[str]:
    """Return all config validation problems without mutating config."""

    problems = _validate_config_ocid_fields(config)
    problems.extend(_validate_regions("monitoring_regions", config.monitoring_regions))
    for index, target in enumerate(config.targets):
        target_label = f"targets[{index}] {target.name}"
        problems.extend(_validate_target(target, target_label))
    return problems


def _validate_target(target: Target, label: str) -> list[str]:
    problems: list[str] = []
    problems.extend(_validate_target_ocid_fields(target, label))
    if target.kind not in ALLOWED_TARGET_KINDS:
        expected = ", ".join(sorted(ALLOWED_TARGET_KINDS))
        problems.append(f"{label}: kind must be one of {expected}")
    if target.region and not _looks_like_region(target.region):
        problems.append(f"{label}: region must look like an OCI region identifier")
    invalid_services = sorted(service for service in target.services if service not in ALLOWED_SERVICES)
    if invalid_services:
        values = ", ".join(str(service) for service in invalid_services)
        problems.append(f"{label}: services contains unsupported values: {values}")
    if target.kind != "autonomous" and not target.provision and not target.service_name:
        problems.append(f"{label}: service_name is required for {target.kind} targets")
    return problems


def _validate_regions(label: str, regions: tuple[str, ...]) -> list[str]:
    invalid = [region for region in regions if not _looks_like_region(region)]
    if invalid:
        return [f"{label} contains invalid OCI region identifiers: {', '.join(invalid)}"]
    duplicates = sorted({region for region in regions if regions.count(region) > 1})
    if duplicates:
        return [f"{label} contains duplicate regions: {', '.join(duplicates)}"]
    return []


def _validate_config_ocid_fields(config: EnablementConfig) -> list[str]:
    return _validate_ocid_fields("config", config, excluded_fields=frozenset({"targets"}))


def _validate_target_ocid_fields(target: Target, label: str) -> list[str]:
    problems: list[str] = []
    for field_name, field_value in _iter_direct_ocid_values(target):
        if _invalid_ocid_value(field_value):
            problems.append(f"{label}: {field_name} must look like an OCI OCID")
    return problems


def _validate_ocid_fields(label: str, value: object, *, excluded_fields: frozenset[str]) -> list[str]:
    problems: list[str] = []
    for field_path, field_value in _iter_ocid_values(label, value, excluded_fields=excluded_fields):
        if _invalid_ocid_value(field_value):
            problems.append(f"{field_path} must look like an OCI OCID")
    return problems


def _iter_direct_ocid_values(value: object) -> list[tuple[str, object]]:
    if not is_dataclass(value):
        return []
    return [
        (item.name, getattr(value, item.name))
        for item in fields(value)
        if item.name.endswith(("_id", "_ocid"))
    ]


def _iter_ocid_values(
    label: str,
    value: object,
    *,
    excluded_fields: frozenset[str],
) -> list[tuple[str, object]]:
    if not is_dataclass(value):
        return []
    matches: list[tuple[str, object]] = []
    for item in fields(value):
        if item.name in excluded_fields:
            continue
        item_value = getattr(value, item.name)
        item_path = f"{label}.{item.name}"
        if item.name.endswith(("_id", "_ocid")):
            matches.append((item_path, item_value))
        elif is_dataclass(item_value):
            matches.extend(_iter_ocid_values(item_path, item_value, excluded_fields=frozenset()))
    return matches


def _invalid_ocid_value(value: object) -> bool:
    return value is not None and value != "" and not _looks_like_ocid(value)


def _looks_like_ocid(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= MAX_OCID_LENGTH
        and OCID_PREFIX_RE.match(value) is not None
    )


def _looks_like_region(value: object) -> bool:
    return isinstance(value, str) and REGION_RE.match(value) is not None


def to_dict(config: EnablementConfig) -> dict[str, Any]:
    return {
        "profile": config.profile,
        "region": config.region,
        "monitoring_regions": list(config.monitoring_regions),
        "tenancy_id": config.tenancy_id,
        "compartment_id": config.compartment_id,
        "network": config.network.__dict__,
        "vault": config.vault.__dict__,
        "targets": [_target_to_dict(target) for target in config.targets],
        "policy_group_name": config.policy_group_name,
        "dry_run": config.dry_run,
        "terraform_dir": config.terraform_dir,
    }


def load_config(path: str | Path) -> EnablementConfig:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw) if str(path).endswith(".json") else yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")
    config = from_dict(data)
    problems = validate_config(config)
    if problems:
        raise ConfigError(problems)
    return config


def save_config(path: str | Path, config: EnablementConfig) -> None:
    destination = Path(path)
    data = to_dict(config)
    if destination.suffix == ".json":
        destination.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return
    destination.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
