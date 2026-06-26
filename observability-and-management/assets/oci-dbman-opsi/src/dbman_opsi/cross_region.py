"""OPSI cross-region monitoring planning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from dbman_opsi.config import EnablementConfig


@dataclass(frozen=True)
class CrossRegionPlan:
    home_region: str
    monitoring_regions: tuple[str, ...]
    target_regions: tuple[str, ...]
    targets_by_region: tuple[tuple[str, tuple[str, ...]], ...]
    warnings: tuple[str, ...] = ()

    @property
    def enabled(self) -> bool:
        return len(self.monitoring_regions) > 1


def parse_regions(value: str) -> tuple[str, ...]:
    """Parse a comma-separated region list while preserving order."""

    return tuple(region.strip() for region in value.split(",") if region.strip())


def cross_region_plan(config: EnablementConfig) -> CrossRegionPlan:
    """Build the display model for the OPSI multi-region console workflow."""

    monitoring_regions = config.monitoring_regions or (config.region,)
    target_region_order = _ordered_unique(target.region or config.region for target in config.targets)
    targets_by_region = tuple(
        (
            region,
            tuple(
                target.name
                for target in config.targets
                if (target.region or config.region) == region and target.wants("opsi")
            ),
        )
        for region in _ordered_unique((*monitoring_regions, *target_region_order))
    )
    missing_target_regions = tuple(region for region in target_region_order if region not in monitoring_regions)
    warnings = tuple(
        f"{region} has OPSI targets but is not selected in monitoring_regions"
        for region in missing_target_regions
    )
    return CrossRegionPlan(
        home_region=config.region,
        monitoring_regions=monitoring_regions,
        target_regions=target_region_order,
        targets_by_region=targets_by_region,
        warnings=warnings,
    )


def format_cross_region_plan(plan: CrossRegionPlan) -> str:
    """Render a concise operator-facing summary."""

    lines = [
        f"OPSI cross-region monitoring: {'enabled' if plan.enabled else 'single-region'}",
        f"Home region: {plan.home_region}",
        "Selected monitoring regions:",
    ]
    lines.extend(f"- {region}" for region in plan.monitoring_regions)
    lines.append("OPSI targets by region:")
    for region, targets in plan.targets_by_region:
        target_list = ", ".join(targets) if targets else "none configured"
        lines.append(f"- {region}: {target_list}")
    if plan.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in plan.warnings)
    lines.extend(
        [
            "Console POC:",
            "- Ops Insights > Data Object Explorer: use the region selector and choose the selected monitoring regions.",
            "- Verify result rows include region context before drilling into SQL or resource metrics.",
            "- Ops Insights dashboards: use the same regions on Configuration and Capacity dashboards.",
        ]
    )
    return "\n".join(lines)


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
