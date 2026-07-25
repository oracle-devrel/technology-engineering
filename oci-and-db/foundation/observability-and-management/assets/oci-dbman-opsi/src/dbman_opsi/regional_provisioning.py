"""Region-specific provisioning config generation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from shutil import copy2

from dbman_opsi.config import EnablementConfig, NetworkSelection, Target

CHICAGO_REGION = "us-chicago-1"
DEFAULT_CHICAGO_DBCS_NAME = "dbman-opsi-chicago-dbcs"
DEFAULT_CHICAGO_ADB_NAME = "dbman-opsi-chicago-adb"


@dataclass(frozen=True)
class RegionalProvisioningRequest:
    region: str = CHICAGO_REGION
    target_kind: str = "dbcs"
    target_name: str | None = None
    terraform_dir: str | None = None
    vcn_id: str | None = None
    subnet_id: str | None = None


def default_regional_output(region: str) -> str:
    return f"dbman-opsi.{region}.local.yaml"


def default_target_name(target_kind: str, region: str) -> str:
    if region == CHICAGO_REGION and target_kind == "autonomous":
        return DEFAULT_CHICAGO_ADB_NAME
    if region == CHICAGO_REGION:
        return DEFAULT_CHICAGO_DBCS_NAME
    suffix = region.replace("-", "")
    return f"dbman-opsi-{suffix}-{target_kind}"


def build_regional_provisioning_config(
    base: EnablementConfig,
    request: RegionalProvisioningRequest,
) -> EnablementConfig:
    """Create a region-specific config suitable for the existing Terraform stack."""

    if (request.vcn_id and not request.subnet_id) or (request.subnet_id and not request.vcn_id):
        raise ValueError("--vcn-id and --subnet-id must be supplied together")
    region_targets = tuple(
        target for target in base.targets if (target.region or base.region) == request.region
    )
    requested_target_name = request.target_name or default_target_name(request.target_kind, request.region)
    targets = _upsert_provisioning_target(
        region_targets,
        Target(
            kind=request.target_kind,  # type: ignore[arg-type]
            name=requested_target_name,
            provision=True,
            services=("dbm", "opsi"),
            region=request.region,
        ),
    )
    network = _regional_network(base.network, request)
    monitoring_regions = _append_region(base.monitoring_regions or (base.region,), request.region)
    return replace(
        base,
        region=request.region,
        monitoring_regions=monitoring_regions,
        network=network,
        targets=targets,
        terraform_dir=request.terraform_dir or _regional_terraform_dir(base.terraform_dir, request.region),
    )


def _upsert_provisioning_target(targets: tuple[Target, ...], requested: Target) -> tuple[Target, ...]:
    next_targets: list[Target] = []
    matched = False
    for target in targets:
        if target.name == requested.name:
            next_targets.append(replace(target, provision=True, region=requested.region))
            matched = True
            continue
        next_targets.append(target)
    if not matched:
        next_targets.append(requested)
    return tuple(next_targets)


def _regional_network(
    network: NetworkSelection,
    request: RegionalProvisioningRequest,
) -> NetworkSelection:
    if request.vcn_id and request.subnet_id:
        return replace(
            network,
            vcn_id=request.vcn_id,
            subnet_id=request.subnet_id,
            create_test_network=False,
        )
    return NetworkSelection(
        create_test_network=True,
        cidr_block=network.cidr_block,
        subnet_cidr_block=network.subnet_cidr_block,
    )


def _regional_terraform_dir(terraform_dir: str, region: str) -> str:
    source = Path(terraform_dir)
    return str(source.with_name(f"{source.name}-{region}"))


def _append_region(regions: tuple[str, ...], region: str) -> tuple[str, ...]:
    if region in regions:
        return regions
    return (*regions, region)


def prepare_regional_terraform_dir(source_dir: str | Path, destination_dir: str | Path) -> tuple[Path, ...]:
    """Create a sibling Terraform workdir with the zero-start stack files."""

    source = Path(source_dir)
    destination = Path(destination_dir)
    if source.resolve() == destination.resolve():
        return ()
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for path in sorted(source.iterdir()):
        if path.suffix != ".tf" and path.name != "schema.yaml":
            continue
        target = destination / path.name
        if target.exists():
            continue
        copy2(path, target)
        copied.append(target)
    return tuple(copied)
