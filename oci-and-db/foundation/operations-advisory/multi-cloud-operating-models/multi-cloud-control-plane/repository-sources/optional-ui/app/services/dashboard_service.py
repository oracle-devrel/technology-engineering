"""Dashboard service - stats and resource inventory."""
import asyncio
import logging

from glom import Coalesce, SKIP, glom

from app.services.git_service import GitService, RepositoryStateError

logger = logging.getLogger(__name__)


class DashboardService:
    """Generate dashboard stats from repo structure."""

    RESOURCE_KEYS = (
        "autonomous_databases",
        "gcp_autonomous_databases_configuration",
        "gcp_virtual_machines_configuration",
        "compute_instances",
        "instances",
        "vcns",
        "subnets",
        "virtual_machines",
        "databases",
        "oracle_autonomous_databases",
        "network_security_groups",
        "resource_groups",
    )

    def __init__(self, git_service: GitService):
        self.git = git_service

    async def get_dashboard_stats(self, strict: bool = False):
        """Get basic dashboard statistics based on actual resources."""
        try:
            inventory = await self.get_resource_inventory(strict=strict)
            summary = inventory.get("summary", {})
            clouds = inventory.get("clouds", [])

            total_regions = 0
            for cloud in clouds:
                total_regions += len(cloud.get("regions", []))

            return {
                "total_resources": summary.get("total_resources", 0),
                "total_clouds": len(summary.get("by_cloud", {})),
                "total_regions": total_regions,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            if strict:
                raise
            return {"total_resources": 0, "total_clouds": 0, "total_regions": 0}

    async def get_recent_deployments(self):
        """Get recent GitHub Actions workflow runs — the post-merge feedback loop."""
        try:
            raw = await self.git.github.get_workflow_runs(self.git.project_name)
            runs = []
            for r in raw:
                commit = r.get("head_commit") or {}
                runs.append({
                    "id": r.get("id"),
                    "name": r.get("name", "Workflow"),
                    "status": r.get("status"),  # queued | in_progress | completed
                    "conclusion": r.get("conclusion"),  # success | failure | cancelled | None
                    "branch": r.get("head_branch", ""),
                    "commit_msg": (commit.get("message") or "")[:60],
                    "actor": r.get("triggering_actor", {}).get("login", ""),
                    "created_at": r.get("created_at", "")[:16].replace("T", " "),
                    "url": r.get("html_url", ""),
                })
            return runs
        except Exception as e:
            logger.error(f"Failed to get workflow runs for {self.git.project_name}: {e}")
            return []

    async def get_pending_prs(self):
        """Get open PRs waiting for review."""
        try:
            raw = await self.git.github.get_open_prs(self.git.project_name)
            prs = []
            for pr in raw:
                prs.append({
                    "number": pr.get("number"),
                    "title": pr.get("title", ""),
                    "author": pr.get("user", {}).get("login", ""),
                    "created_at": pr.get("created_at", "")[:10],
                    "branch": pr.get("head", {}).get("ref", ""),
                    "url": pr.get("html_url", ""),
                })
            return prs
        except Exception as e:
            logger.error(f"Failed to get pending PRs for {self.git.project_name}: {e}")
            return []

    async def get_resource_inventory(self, strict: bool = False):
        """Get flat list of all resources."""
        resources = []
        summary = {"total_resources": 0, "by_cloud": {}, "by_type": {}}

        try:
            structure = await self.git.get_repository_structure(strict=strict)

            # Pass 1: collect tasks (cloud, environment, region, relative path, file).
            tasks: list[tuple[str, str, str, str, dict]] = []
            for cloud in structure.get("clouds", []):
                cloud_name = cloud["name"]
                summary["by_cloud"][cloud_name] = 0

                for region in cloud.get("regions", []):
                    region_name = region["name"]
                    environment_name = region.get("environment", "")

                    for res in region.get("resources", []):
                        # Skip ansible operations - they are not resources
                        if (
                            res.get("type") in {"ansible", "lifecycle_operations"}
                            or "ansible" in res.get("path", "")
                            or "lifecycle_operations/" in res.get("path", "")
                        ):
                            continue

                        # Strip the V2 cloud/environment/region prefix before reading.
                        prefix = f"{cloud_name}/{environment_name}/{region_name}/"
                        relative_path = res["path"]
                        if relative_path.startswith(prefix):
                            relative_path = relative_path[len(prefix):]

                        tasks.append(
                            (
                                cloud_name,
                                environment_name,
                                region_name,
                                relative_path,
                                res,
                            )
                        )

            # Pass 2: parallel manifest reads
            manifests = await asyncio.gather(
                *[
                    self.git.read_manifest(c, e, r, p, strict=strict)
                    for (c, e, r, p, _) in tasks
                ],
                return_exceptions=not strict,
            )

            # Pass 3: extract resources, preserving order
            for (
                cloud_name,
                environment_name,
                region_name,
                _relative_path,
                res,
            ), manifest in zip(tasks, manifests):
                if isinstance(manifest, Exception):
                    continue
                extracted = self._extract_resources(
                    manifest, cloud_name, environment_name, region_name, res
                )
                resources.extend(extracted)
                summary["total_resources"] += len(extracted)
                summary["by_cloud"][cloud_name] += len(extracted)

            logger.info(f"Inventory: {summary['total_resources']} resources across {len(summary['by_cloud'])} clouds")
            return {"resources": resources, "clouds": structure.get("clouds", []), "summary": summary}

        except Exception as e:
            logger.error(f"Failed to get inventory: {e}", exc_info=strict)
            if strict:
                raise RepositoryStateError("Could not verify resource inventory") from e
            return {"resources": [], "clouds": [], "summary": summary}

    def _extract_resources(self, manifest, cloud, environment, region, file_info):
        """Extract individual resources from manifest."""
        resources = []
        source_path = file_info.get("path", "")

        if not isinstance(manifest, dict):
            return resources

        # Resource collections can be nested in a handed-off foundation structure.
        sections = []

        def collect_sections(value):
            if isinstance(value, dict):
                sections.append(value)
                for child in value.values():
                    collect_sections(child)
            elif isinstance(value, list):
                for child in value:
                    collect_sections(child)

        collect_sections(manifest)

        def _append_from_dict(resource_key: str, items: dict):
            for item_id, item_data in items.items():
                details = item_data if isinstance(item_data, dict) else {}
                display_name = glom(details, Coalesce("display_name", "db_name", default=item_id))
                resources.append(
                    {
                        "name": display_name,
                        "id": item_id,
                        "type": resource_key.replace("_", " ").title(),
                        "cloud": cloud,
                        "environment": environment,
                        "region": region,
                        "path": source_path,
                        "resource_path": source_path.split("/", 3)[-1],
                        "collection_name": resource_key,
                        "details": details,
                    }
                )

        def _append_from_list(resource_key: str, items: list):
            for item in items:
                details = item if isinstance(item, dict) else {}
                name = glom(details, Coalesce("name", "display_name", default="unnamed"))
                resources.append(
                    {
                        "name": name,
                        "id": name,
                        "type": resource_key.replace("_", " ").title(),
                        "cloud": cloud,
                        "environment": environment,
                        "region": region,
                        "path": source_path,
                        "resource_path": source_path.split("/", 3)[-1],
                        "details": details,
                    }
                )

        for section in sections:
            if not isinstance(section, dict):
                continue
            for resource_key in self.RESOURCE_KEYS:
                items = section.get(resource_key, SKIP)
                if items is SKIP:
                    continue
                if isinstance(items, dict):
                    _append_from_dict(resource_key, items)
                elif isinstance(items, list) and resource_key != "network_security_groups":
                    _append_from_list(resource_key, items)

        # Fallback: handle flat manifests where one file maps to one resource.
        if not resources and manifest:
            name = glom(manifest, Coalesce("display_name", "db_name", "name", default=None))
            if name:
                resource_type = "Resource"
                filename = file_info.get("file", "").lower()
                if "db" in filename or "database" in filename:
                    resource_type = "Database"
                elif "vm" in filename or "instance" in filename:
                    resource_type = "Instance"
                resources.append(
                    {
                        "name": name,
                        "id": file_info.get("file", "").replace(".json", ""),
                        "type": resource_type,
                        "cloud": cloud,
                        "environment": environment,
                        "region": region,
                        "path": source_path,
                        "details": manifest,
                    }
                )

        return resources
