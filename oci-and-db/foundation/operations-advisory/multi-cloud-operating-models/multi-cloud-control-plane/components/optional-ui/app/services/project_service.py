"""Project management service."""
import logging
from app.config import settings
from app.github import github_client as default_github_client
from app.services.installation_service import InstallationError, load_mccp_installation

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for listing handed-off GitOps project repositories."""

    def __init__(self, github_client=None):
        self.org = settings.github_org
        self.github = github_client or default_github_client

    @staticmethod
    def _filter_projects(repos: list, installation) -> list[dict]:
        """Return only V2 handed-off project repository names."""
        projects = []
        seen_names = set()
        for r in repos:
            name = (r.get("name", "") or "").strip()
            if not name or name in seen_names:
                continue

            if r.get("is_template"):
                continue

            name_lc = name.lower()
            try:
                if name_lc.startswith("nonprod-"):
                    installation.project_context(name, "dev")
                elif name_lc.startswith("prod-"):
                    installation.project_context(name, "prod")
                else:
                    continue
            except InstallationError:
                continue

            if name_lc.endswith("-template"):
                continue

            seen_names.add(name)
            projects.append({
                "name": name,
                "description": r.get("description", ""),
                "is_template": r.get("is_template", False),
            })

        return sorted(projects, key=lambda x: x["name"])

    async def list_projects(self):
        """List projects visible to current token, filtered by prefix."""
        try:
            user_repos = await self.github.list_user_repos() or []
            org_repos = await self.github.list_org_repos() or []
            repos = (user_repos or []) + (org_repos or [])

            logger.info(f"Total repos fetched: {len(repos)}")
            installation = load_mccp_installation(settings.mccp_installation_path)
            if self.org != installation.customer_org:
                return []
            projects = self._filter_projects(repos, installation)

            logger.info("Projects visible after filtering: %d", len(projects))
            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
