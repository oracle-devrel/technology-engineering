"""Git operations service backed by async GitHub API calls."""
import json
import logging
import time
import uuid

from app.config import settings
from app.github import GitHubClient, github_client as default_github_client
from app.helpers import extract_plan_from_markdown, extract_status_from_markdown
from app.path_validation import validate_path_segment, validate_relative_path
from app.schemas import OperationsCatalog
from app.services.catalog_service import CatalogService
from app.services.installation_service import load_mccp_installation

logger = logging.getLogger(__name__)


class RepositoryStateError(RuntimeError):
    """Raised when repository state cannot be verified safely."""


class GitService:
    """Git operations for GitOps repositories."""

    def __init__(self, project_name, github_client=None):
        self.project_name = project_name
        self.org = settings.github_org
        self.github = github_client or default_github_client

    @staticmethod
    def _catalog_service(github_client):
        installation = load_mccp_installation(settings.mccp_installation_path)
        return CatalogService(
            github_client,
            repo_name=installation.catalog_repository.rsplit("/", 1)[1],
            revision=installation.catalog_revision,
        )

    async def get_repository_structure(self, strict: bool = False):
        """Get repo structure as tree."""
        clouds_dict = {}

        try:
            if strict:
                tree = await self.github.get_repo_tree_strict(self.project_name)
            else:
                tree = await self.github.get_repo_tree(self.project_name)
            if not isinstance(tree, dict):
                raise TypeError("Repository tree response is not an object")

            for item in tree.get("tree", []):
                path = item["path"]
                if not path.endswith(".json"):
                    continue

                parts = path.split("/")
                if len(parts) < 4:
                    continue

                cloud, environment, region = parts[0], parts[1], parts[2]
                if cloud not in {"oci", "azure", "gcp"}:
                    continue

                if cloud not in clouds_dict:
                    clouds_dict[cloud] = {}
                environment_region = (environment, region)
                if environment_region not in clouds_dict[cloud]:
                    clouds_dict[cloud][environment_region] = []

                res_type = parts[3]
                clouds_dict[cloud][environment_region].append(
                    {
                        "type": res_type,
                        "file": parts[-1],
                        "path": path,
                    }
                )

            clouds = []
            for cloud_name, regions in clouds_dict.items():
                regions_list = []
                for (environment_name, region_name), resources in regions.items():
                    regions_list.append(
                        {
                            "environment": environment_name,
                            "name": region_name,
                            "resources": resources,
                        }
                    )
                clouds.append({"name": cloud_name, "regions": regions_list})

            return {"clouds": clouds}
        except Exception as e:
            logger.error("Failed to get structure: %s", e, exc_info=strict)
            if strict:
                raise RepositoryStateError("Could not verify repository tree") from e
            return {"clouds": []}

    async def read_manifest(
        self,
        cloud,
        environment,
        region,
        resource_path,
        strict: bool = False,
    ):
        """Read manifest file."""
        validate_path_segment(cloud, "cloud")
        validate_path_segment(environment, "environment")
        validate_path_segment(region, "region")
        validate_relative_path(resource_path)
        path = f"{cloud}/{environment}/{region}/{resource_path}"
        try:
            if strict:
                content = await self.github.get_file_content_strict(self.project_name, path)
            else:
                content = await self.github.get_file_content(self.project_name, path)
            if content is None:
                raise FileNotFoundError(f"Manifest not found: {path}")
            return json.loads(content)
        except Exception as exc:
            if strict:
                logger.error("Failed to read manifest %s: %s", path, exc, exc_info=True)
                raise RepositoryStateError(f"Could not verify manifest: {path}") from exc
            raise

    async def write_manifest(
        self,
        cloud,
        environment,
        region,
        resource_path,
        data,
        commit_message=None,
    ):
        """Write one manifest file via issue + branch + PR flow."""
        validate_path_segment(cloud, "cloud")
        validate_path_segment(environment, "environment")
        validate_path_segment(region, "region")
        validate_relative_path(resource_path)
        file_path = f"{cloud}/{environment}/{region}/{resource_path}"
        commit_message = commit_message or f"Update {file_path}"
        branch_suffix = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        branch = f"change/{cloud}-{environment}-{region}-{branch_suffix}"

        issue = await self.github.create_issue_async(
            self.project_name,
            title=commit_message,
            body=f"Change request for `{file_path}`",
            labels=["gitops"],
        )
        issue_num = issue["number"]
        logger.info("Created issue #%s", issue_num)

        try:
            await self.github.create_branch_async(self.project_name, branch)
            logger.info("Created branch: %s", branch)

            content = json.dumps(data, indent=2) + "\n"
            await self.github.create_or_update_file_async(
                self.project_name,
                file_path,
                content,
                commit_message,
                branch=branch,
            )
            logger.info("Committed to %s", branch)

            pr = await self.github.create_pull_request_async(
                self.project_name,
                title=commit_message,
                head=branch,
                base="main",
                body=f"Closes #{issue_num}",
            )
            pr_num = pr["number"]
            pr_url = pr["html_url"]
            logger.info("Created PR #%s", pr_num)

            return {
                "success": True,
                "issue_number": issue_num,
                "issue_url": issue.get("html_url"),
                "pr_number": pr_num,
                "pr_url": pr_url,
                "merged": False,
            }
        except Exception as e:
            logger.error("PR flow failed: %s", e)
            raise

    async def get_git_status(self):
        """Get current status from the repository main branch head."""
        try:
            commit = await self.github.get_latest_commit_async(self.project_name)
            sha = commit.get("sha", "")
            return {"branch": "main", "commit": sha[:8] if sha else "unknown", "is_dirty": False}
        except Exception as e:
            logger.warning("Could not get git status for %s: %s", self.project_name, e)
            return {"branch": "main", "commit": "unknown", "is_dirty": False}

    async def get_operations_catalog(self, cloud_filter: str | None = None) -> OperationsCatalog:
        """Get operations catalog from gitops-templates repo."""
        catalog = self._catalog_service(self.github)
        try:
            operations = await catalog.list_operations_catalog(cloud_filter=cloud_filter)
        except Exception:
            if not self._can_use_catalog_pat():
                raise
            fallback_catalog = self._catalog_service(default_github_client)
            operations = await fallback_catalog.list_operations_catalog(cloud_filter=cloud_filter)
        else:
            if not operations and self._can_use_catalog_pat():
                fallback_catalog = self._catalog_service(default_github_client)
                fallback_operations = await fallback_catalog.list_operations_catalog(
                    cloud_filter=cloud_filter
                )
                if fallback_operations:
                    operations = fallback_operations
        return OperationsCatalog(operations=operations)

    def _can_use_catalog_pat(self) -> bool:
        """Return whether server PAT fallback is appropriate for gitops-templates reads."""
        return (
            bool(settings.github_token)
            and isinstance(self.github, GitHubClient)
            and self.github is not default_github_client
        )

    @staticmethod
    def _preview_kind(check_runs: list[dict], comments: list[dict], expected_kind: str = "") -> str:
        """Infer the PR preview type from caller hint, checks, and comments."""
        expected = (expected_kind or "").strip().lower()
        if expected in {"terraform", "operation", "ansible"}:
            return "operation" if expected in {"operation", "ansible"} else "terraform"

        if any("Terraform Plan" in (comment.get("body") or "") for comment in comments):
            return "terraform"

        check_names = " ".join(str(run.get("name") or "").lower() for run in check_runs)
        if "ansible" in check_names:
            return "operation"
        if "terraform" in check_names:
            return "terraform"
        return "checks"

    @staticmethod
    def _format_workflow_run(run: dict) -> dict:
        """Return the small workflow-run shape used by PR preview templates."""
        commit = run.get("head_commit") or {}
        return {
            "id": run.get("id"),
            "name": run.get("name", "Workflow"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "branch": run.get("head_branch", ""),
            "commit_msg": (commit.get("message") or "")[:80],
            "actor": run.get("triggering_actor", {}).get("login", ""),
            "created_at": run.get("created_at", "")[:16].replace("T", " "),
            "url": run.get("html_url", ""),
        }

    async def _pr_execution_preview(self, pr_status: dict) -> dict:
        """Build post-merge execution state for the PR's merge commit."""
        if not pr_status.get("merged"):
            return {
                "execution_status": "waiting",
                "execution_conclusion": "",
                "execution_message": "Execution starts after the PR is merged.",
                "execution_runs": [],
                "execution_url": "",
                "merge_commit_sha": pr_status.get("merge_commit_sha", ""),
            }

        merge_commit_sha = pr_status.get("merge_commit_sha") or ""
        if not merge_commit_sha:
            return {
                "execution_status": "waiting",
                "execution_conclusion": "",
                "execution_message": "PR is merged, but GitHub has not exposed a merge commit SHA yet.",
                "execution_runs": [],
                "execution_url": "",
                "merge_commit_sha": "",
            }

        try:
            raw_runs = await self.github.get_workflow_runs_for_sha(
                self.project_name,
                merge_commit_sha,
                limit=20,
            )
        except AttributeError:
            runs = await self.github.get_workflow_runs(self.project_name, limit=50)
            raw_runs = [run for run in runs if run.get("head_sha") == merge_commit_sha]
        except Exception as e:
            logger.warning("Could not get post-merge workflow runs: %s", e)
            raw_runs = []

        execution_runs = [self._format_workflow_run(run) for run in raw_runs]
        if not execution_runs:
            return {
                "execution_status": "waiting",
                "execution_conclusion": "",
                "execution_message": "Waiting for the post-merge GitHub Actions run on main.",
                "execution_runs": [],
                "execution_url": "",
                "merge_commit_sha": merge_commit_sha,
            }

        latest = execution_runs[0]
        status = latest.get("status") or "queued"
        conclusion = latest.get("conclusion") or ""
        if status == "completed" and conclusion == "success":
            message = "Execution completed successfully."
        elif status == "completed" and conclusion:
            message = "Execution failed or did not complete successfully. Open GitHub Actions for details."
        elif status in {"queued", "in_progress", "pending"}:
            message = "Execution is still running in GitHub Actions."
        else:
            message = "Execution status is available in GitHub Actions."

        return {
            "execution_status": status,
            "execution_conclusion": conclusion,
            "execution_message": message,
            "execution_runs": execution_runs,
            "execution_url": latest.get("url", ""),
            "merge_commit_sha": merge_commit_sha,
        }

    async def get_pr_ci_preview(self, pr_number, expected_kind: str = ""):
        """Get CI preview data for a PR, including Terraform plans when present."""
        try:
            pr_status = await self.github.get_pr_status_async(self.project_name, pr_number)
            execution = await self._pr_execution_preview(pr_status)

            try:
                check_runs = await self.github.get_pr_check_runs_async(self.project_name, pr_number)
            except Exception as e:
                logger.warning("Could not get check runs: %s", e)
                check_runs = []

            comments = await self.github.get_pr_comments_async(self.project_name, pr_number)
            preview_kind = self._preview_kind(check_runs, comments, expected_kind)

            if preview_kind != "operation":
                for comment in reversed(comments):
                    body = comment.get("body", "")
                    if "Terraform Plan" in body:
                        return {
                            "found": True,
                            "preview_kind": "terraform",
                            "title": "Terraform Plan Preview",
                            "unavailable_title": "Plan Not Available",
                            "output_label": "Plan Output",
                            "action_hint": "Review the plan above, then decide:",
                            "pr_number": pr_number,
                            "pr_status": pr_status,
                            "check_runs": check_runs,
                            **execution,
                            "plan_comment": comment,
                            "plan_output": extract_plan_from_markdown(body),
                            "format_status": extract_status_from_markdown(body, "Format"),
                            "validate_status": extract_status_from_markdown(body, "Validate"),
                        }

            if preview_kind == "operation":
                message = (
                    "This PR runs an Ansible operation. Review the CI checks and GitHub PR; "
                    "no Terraform plan is generated for this change."
                )
                title = "Operation Check Preview"
                unavailable_title = "No Plan Expected"
            elif preview_kind == "terraform":
                message = "Terraform plan not found. CI may still be running."
                title = "Terraform Plan Preview"
                unavailable_title = "Plan Not Available"
            else:
                message = "No generated preview was found yet. Review the CI checks or open the PR on GitHub."
                title = "PR Check Preview"
                unavailable_title = "Preview Not Available"

            return {
                "found": False,
                "preview_kind": preview_kind,
                "title": title,
                "unavailable_title": unavailable_title,
                "output_label": "Plan Output",
                "action_hint": "Review the CI checks above, then decide:",
                "pr_number": pr_number,
                "pr_status": pr_status,
                "check_runs": check_runs,
                **execution,
                "message": message,
            }
        except Exception as e:
            logger.error("Failed to get PR CI preview: %s", e)
            return {
                "found": False,
                "preview_kind": "checks",
                "title": "PR Check Preview",
                "unavailable_title": "Preview Not Available",
                "output_label": "Plan Output",
                "action_hint": "Review the CI checks above, then decide:",
                "pr_number": pr_number,
                "execution_status": "unknown",
                "execution_conclusion": "",
                "execution_message": "Execution status could not be loaded.",
                "execution_runs": [],
                "execution_url": "",
                "merge_commit_sha": "",
                "error": str(e),
                "message": f"Error retrieving PR checks: {e}",
            }
