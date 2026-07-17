"""Project management service."""
import logging
from app.config import settings
from app.github import github_client as default_github_client

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for listing handed-off GitOps project repositories."""

    def __init__(self, github_client=None):
        self.org = settings.github_org
        self.github = github_client or default_github_client

    @staticmethod
    def _filter_projects(repos: list, prefix: str) -> list[dict]:
        """Filter repos by prefix and exclude template-style repos."""
        projects = []
        seen_names = set()
        prefix_lc = (prefix or "").strip().lower()

        for r in repos:
            name = (r.get("name", "") or "").strip()
            if not name or name in seen_names:
                continue

            if r.get("is_template"):
                continue

            name_lc = name.lower()
            if prefix_lc and not name_lc.startswith(prefix_lc):
                continue

            # Exclude template-style repos from oe-* listing (e.g., oe-foo-template)
            if name_lc.startswith("oe-") and name_lc.endswith("-template"):
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
            prefix = (settings.project_repo_prefix or "").strip()
            logger.info("Looking for prefix: '%s'", prefix)

            projects = self._filter_projects(repos, prefix)

            logger.info("Projects visible after filtering: %d", len(projects))
            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
