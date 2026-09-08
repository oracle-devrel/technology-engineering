"""GitHub client using githubkit with async-first operations."""
import base64
import hashlib
import logging
from collections.abc import Callable
from typing import Any

from cashews import cache
from githubkit import GitHub
from githubkit.exception import RequestFailed

from app.config import _load_gh_fallback_token, settings

logger = logging.getLogger(__name__)

# Configure cache - Use disk cache for persistence across restarts.
cache.setup("disk://?directory=/tmp/multi_cloud_cache&shards=1")

_MISSING = object()


class GitHubClient:
    """Async GitHub client with cached reads and async write operations."""

    def __init__(self, token=None):
        self.token = token or settings.github_token
        if not self.token:
            self.token = _load_gh_fallback_token()
        self.org = settings.github_org
        self.cache_key = self._build_cache_key(self.token)
        self.timeout = settings.github_api_timeout_seconds
        self.api_headers = {"X-GitHub-Api-Version": "2022-11-28"}
        self._github = GitHub(
            auth=self.token or None,
            timeout=self.timeout,
            user_agent=f"{self.org}/multi-cloud-plane",
            auto_retry=True,
        )

    @staticmethod
    def _build_cache_key(token: str | None) -> str:
        if not token:
            return "anonymous"
        return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _status_code(exc: RequestFailed) -> int | None:
        try:
            return int(exc.response.status_code)
        except Exception:
            return None

    @staticmethod
    def _to_plain(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json", by_alias=True)
        if isinstance(value, list):
            return [GitHubClient._to_plain(v) for v in value]
        if isinstance(value, tuple):
            return tuple(GitHubClient._to_plain(v) for v in value)
        if isinstance(value, dict):
            return {k: GitHubClient._to_plain(v) for k, v in value.items()}
        return value

    @staticmethod
    def _ensure_writes_enabled():
        if not settings.github_writes_v2:
            raise RuntimeError(
                "GitHub write path v2 is disabled. Set GITHUB_WRITES_V2=true to enable writes."
            )

    async def invalidate_repo_caches(
        self,
        repo_name: str | None,
        *,
        scopes: set[str],
    ) -> None:
        """Drop cached read entries that go stale after a write.

        Scopes (pick what the write actually invalidates):
          - "pulls":     get_open_prs for this repo
          - "tree":      get_repo_tree for this repo (all refs)
          - "commits":   get_commits for this repo
          - "content":   get_file_content for this repo (all paths/refs)
          - "runs":      get_workflow_runs for this repo
          - "commit_pr": get_commit_pr for this repo
          - "repo":      get_repo metadata for this repo
          - "repos":     org/user repo listings (repo_name ignored)
        """
        patterns: list[str] = []
        if repo_name:
            if "pulls" in scopes:
                patterns.append(f"pulls:{self.org}:*:{repo_name}")
            if "tree" in scopes:
                patterns.append(f"tree:{self.org}:*:{repo_name}:*")
            if "commits" in scopes:
                patterns.append(f"commits:{self.org}:*:{repo_name}:*")
            if "content" in scopes:
                patterns.append(f"content:{self.org}:*:{repo_name}:*")
            if "runs" in scopes:
                patterns.append(f"runs:{self.org}:*:{repo_name}:*")
                patterns.append(f"runs_sha:{self.org}:*:{repo_name}:*")
            if "commit_pr" in scopes:
                patterns.append(f"commit_pr:{self.org}:*:{repo_name}:*")
            if "repo" in scopes:
                patterns.append(f"repo:{self.org}:*:{repo_name}")
        if "repos" in scopes:
            patterns.append(f"repos:{self.org}:*")
            patterns.append("user_repos:*")

        for pattern in patterns:
            try:
                await cache.delete_match(pattern)
            except Exception as exc:
                logger.warning("Cache invalidate failed for %s: %s", pattern, exc)

    async def _request(
        self,
        fn: Callable[..., Any],
        *args,
        allow_statuses: set[int] | None = None,
        **kwargs,
    ):
        allow_statuses = allow_statuses or set()
        kwargs.setdefault("headers", self.api_headers)

        try:
            response = await fn(*args, **kwargs)
            return self._to_plain(response.parsed_data)
        except RequestFailed as exc:
            if self._status_code(exc) in allow_statuses:
                return _MISSING
            raise

    async def _paginate(
        self,
        request_fn: Callable[..., Any],
        *args,
        limit: int,
        map_func: Callable[[Any], list[Any]] | None = None,
        **kwargs,
    ) -> list[dict]:
        kwargs.setdefault("headers", self.api_headers)
        results: list[dict] = []
        paginator = self._github.rest.paginate(
            request_fn,
            map_func,
            *args,
            **kwargs,
        )
        async for item in paginator:
            results.append(self._to_plain(item))
            if len(results) >= limit:
                break
        return results

    @cache(ttl="30s", prefix="repos", key="{self.org}:{self.cache_key}:{limit}")
    async def list_org_repos(self, limit: int = 500):
        """List repos in org with pagination (cached)."""
        try:
            return await self._paginate(
                self._github.rest.repos.async_list_for_org,
                self.org,
                limit=max(1, limit),
                per_page=100,
                type="all",
            )
        except Exception as e:
            logger.error("Failed to list repos: %s", e)
            raise

    @cache(ttl="30s", prefix="user_repos", key="{self.cache_key}:{limit}")
    async def list_user_repos(self, limit: int = 500):
        """List repos the user can access with pagination (cached)."""
        try:
            return await self._paginate(
                self._github.rest.repos.async_list_for_authenticated_user,
                limit=max(1, limit),
                per_page=100,
                type="all",
            )
        except Exception as e:
            logger.error("Failed to list user repos: %s", e)
            return []

    @cache(ttl="30s", prefix="repo", key="{self.org}:{self.cache_key}:{repo_name}")
    async def get_repo(self, repo_name: str):
        """Get repo details for permission checks (cached)."""
        try:
            repo = await self._request(
                self._github.rest.repos.async_get,
                self.org,
                repo_name,
                allow_statuses={403, 404},
            )
            return None if repo is _MISSING else repo
        except Exception as e:
            logger.error("Failed to get repo %s: %s", repo_name, e)
            return None

    async def get_repo_permissions(self, repo_name: str) -> dict:
        """Return permissions for the authenticated user on a repo."""
        repo = await self.get_repo(repo_name)
        if not repo:
            return {}
        return repo.get("permissions", {})

    @cache(ttl="30s", prefix="tree", key="{self.org}:{self.cache_key}:{repo_name}:{ref}")
    async def get_repo_tree(self, repo_name: str, ref: str = "main"):
        """Get repo tree (cached)."""
        try:
            tree = await self._request(
                self._github.rest.git.async_get_tree,
                self.org,
                repo_name,
                ref,
                recursive="1",
                allow_statuses={404},
            )
            return {"tree": []} if tree is _MISSING else tree
        except Exception as e:
            logger.error("Failed to get tree for %s: %s", repo_name, e)
            return {"tree": []}

    async def get_repo_tree_strict(self, repo_name: str, ref: str = "main"):
        """Get repo tree and propagate GitHub errors to callers."""
        return await self._request(
            self._github.rest.git.async_get_tree,
            self.org,
            repo_name,
            ref,
            recursive="1",
        )

    @cache(ttl="30s", prefix="content", key="{self.org}:{self.cache_key}:{repo_name}:{path}:{ref}")
    async def get_file_content(self, repo_name: str, path: str, ref: str = "main"):
        """Get file content (cached)."""
        try:
            data = await self._request(
                self._github.rest.repos.async_get_content,
                self.org,
                repo_name,
                path,
                ref=ref,
                allow_statuses={404},
            )
            if data is _MISSING:
                return None
            if isinstance(data, dict) and data.get("content") and data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8")
            return None
        except Exception as e:
            logger.error("Failed to get content for %s/%s: %s", repo_name, path, e)
            return None

    async def get_file_content_strict(self, repo_name: str, path: str, ref: str = "main"):
        """Get file content and propagate GitHub errors to callers."""
        data = await self._request(
            self._github.rest.repos.async_get_content,
            self.org,
            repo_name,
            path,
            ref=ref,
        )
        if (
            isinstance(data, dict)
            and data.get("encoding") == "base64"
            and "content" in data
        ):
            return base64.b64decode(data["content"]).decode("utf-8")
        raise RuntimeError(f"Unexpected content response for {repo_name}/{path}")

    @cache(ttl="30s", prefix="runs", key="{self.org}:{self.cache_key}:{repo_name}:{limit}")
    async def get_workflow_runs(self, repo_name: str, limit: int = 10):
        """Get recent GitHub Actions workflow runs (cached)."""
        try:
            data = await self._request(
                self._github.rest.actions.async_list_workflow_runs_for_repo,
                self.org,
                repo_name,
                per_page=limit,
                allow_statuses={403, 404},
            )
            if data is _MISSING:
                return []
            return data.get("workflow_runs", [])
        except Exception as e:
            logger.error("Failed to get workflow runs for %s: %s", repo_name, e)
            return []

    @cache(ttl="30s", prefix="runs_sha", key="{self.org}:{self.cache_key}:{repo_name}:{sha}:{limit}")
    async def get_workflow_runs_for_sha(self, repo_name: str, sha: str, limit: int = 20):
        """Get workflow runs for a specific commit SHA, falling back to local filtering."""
        if not sha:
            return []

        try:
            data = await self._request(
                self._github.rest.actions.async_list_workflow_runs_for_repo,
                self.org,
                repo_name,
                per_page=limit,
                head_sha=sha,
                allow_statuses={403, 404},
            )
            if data is not _MISSING:
                return data.get("workflow_runs", [])
        except Exception as e:
            logger.warning("Failed to query workflow runs by SHA for %s/%s: %s", repo_name, sha, e)

        runs = await self.get_workflow_runs(repo_name, limit=max(limit, 50))
        return [run for run in runs if run.get("head_sha") == sha][:limit]

    @cache(ttl="30s", prefix="commit_pr", key="{self.org}:{self.cache_key}:{repo_name}:{sha}")
    async def get_commit_pr(self, repo_name: str, sha: str):
        """Get the PR associated with a commit SHA (cached)."""
        try:
            prs = await self._request(
                self._github.rest.repos.async_list_pull_requests_associated_with_commit,
                self.org,
                repo_name,
                sha,
                per_page=20,
                allow_statuses={403, 404},
            )
            if prs is _MISSING:
                return None
            return prs[0] if prs else None
        except Exception as e:
            logger.error("Failed to get PR for commit %s: %s", sha, e)
            return None

    @cache(ttl="30s", prefix="pr_reviews", key="{self.org}:{self.cache_key}:{repo_name}:{pr_number}")
    async def get_pr_approvers(self, repo_name: str, pr_number: int):
        """Get list of users who approved a PR (cached)."""
        try:
            reviews = await self._request(
                self._github.rest.pulls.async_list_reviews,
                self.org,
                repo_name,
                pr_number,
                per_page=100,
                allow_statuses={403, 404},
            )
            if reviews is _MISSING:
                return []
            return list(
                {
                    r["user"]["login"]
                    for r in reviews
                    if r.get("state") == "APPROVED" and r.get("user")
                }
            )
        except Exception as e:
            logger.error("Failed to get reviews for PR#%s: %s", pr_number, e)
            return []

    @cache(ttl="30s", prefix="pulls", key="{self.org}:{self.cache_key}:{repo_name}")
    async def get_open_prs(self, repo_name: str):
        """Get open pull requests for a repo (cached)."""
        try:
            pulls = await self._request(
                self._github.rest.pulls.async_list,
                self.org,
                repo_name,
                state="open",
                per_page=20,
                allow_statuses={404},
            )
            return [] if pulls is _MISSING else pulls
        except Exception as e:
            logger.error("Failed to get open PRs for %s: %s", repo_name, e)
            return []

    @cache(ttl="30s", prefix="commits", key="{self.org}:{self.cache_key}:{repo_name}:{limit}")
    async def get_commits(self, repo_name: str, limit: int = 20):
        """Get recent commits (cached)."""
        try:
            return await self._request(
                self._github.rest.repos.async_list_commits,
                self.org,
                repo_name,
                per_page=limit,
            )
        except Exception as e:
            logger.error("Failed to get commits for %s: %s", repo_name, e)
            return []

    @cache(ttl="30s", prefix="commit_detail", key="{self.org}:{self.cache_key}:{repo_name}:{sha}")
    async def get_commit_details(self, repo_name: str, sha: str):
        """Get commit details including changed files (cached)."""
        try:
            details = await self._request(
                self._github.rest.repos.async_get_commit,
                self.org,
                repo_name,
                sha,
                allow_statuses={403, 404},
            )
            return {} if details is _MISSING else details
        except Exception as e:
            logger.error("Failed to get commit details for %s/%s: %s", repo_name, sha, e)
            return {}

    @cache(ttl="30s", prefix="pr_detail", key="{self.org}:{self.cache_key}:{repo_name}:{pr_number}")
    async def get_pull_request(self, repo_name: str, pr_number: int):
        """Get pull request details (cached)."""
        try:
            pr = await self._request(
                self._github.rest.pulls.async_get,
                self.org,
                repo_name,
                pr_number,
                allow_statuses={403, 404},
            )
            return {} if pr is _MISSING else pr
        except Exception as e:
            logger.error("Failed to get PR details for %s#%s: %s", repo_name, pr_number, e)
            return {}

    async def create_issue_async(self, repo_name: str, **kwargs):
        """Create an issue in a repository."""
        self._ensure_writes_enabled()
        return await self._request(
            self._github.rest.issues.async_create,
            self.org,
            repo_name,
            data=kwargs,
        )

    async def create_branch_async(self, repo_name: str, branch_name: str, from_branch: str = "main"):
        """Create a branch from an existing source branch."""
        self._ensure_writes_enabled()
        source_ref = await self._request(
            self._github.rest.git.async_get_ref,
            self.org,
            repo_name,
            f"heads/{from_branch}",
        )
        source_sha = source_ref.get("object", {}).get("sha")
        if not source_sha:
            raise RuntimeError(f"Could not resolve source SHA for branch '{from_branch}'")
        await self._request(
            self._github.rest.git.async_create_ref,
            self.org,
            repo_name,
            data={"ref": f"refs/heads/{branch_name}", "sha": source_sha},
        )

    async def create_or_update_file_async(
        self,
        repo_name: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ):
        """Create or update a file in a branch."""
        self._ensure_writes_enabled()
        existing = await self._request(
            self._github.rest.repos.async_get_content,
            self.org,
            repo_name,
            path,
            ref=branch,
            allow_statuses={404},
        )
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
            "committer": {
                "name": settings.git_author_name,
                "email": settings.git_author_email,
            },
        }
        if existing is not _MISSING:
            existing_sha = existing.get("sha")
            if existing_sha:
                payload["sha"] = existing_sha
        return await self._request(
            self._github.rest.repos.async_create_or_update_file_contents,
            self.org,
            repo_name,
            path,
            data=payload,
        )

    async def create_pull_request_async(self, repo_name: str, **kwargs):
        """Create a pull request."""
        self._ensure_writes_enabled()
        result = await self._request(
            self._github.rest.pulls.async_create,
            self.org,
            repo_name,
            data=kwargs,
        )
        await self.invalidate_repo_caches(repo_name, scopes={"pulls"})
        return result

    async def get_latest_commit_async(self, repo_name: str, branch: str = "main"):
        """Get branch head commit metadata."""
        branch_data = await self._request(
            self._github.rest.repos.async_get_branch,
            self.org,
            repo_name,
            branch,
        )
        return branch_data.get("commit", {})

    async def get_pr_status_async(self, repo_name: str, pr_number: int):
        """Get PR status summary."""
        pr = await self.get_pull_request(repo_name, pr_number)
        return {
            "state": pr.get("state"),
            "merged": pr.get("merged", False),
            "mergeable": pr.get("mergeable"),
            "merge_commit_sha": pr.get("merge_commit_sha", ""),
            "head_sha": pr.get("head", {}).get("sha", ""),
            "html_url": pr.get("html_url", ""),
        }

    async def get_pr_check_runs_async(self, repo_name: str, pr_number: int):
        """List check runs for the PR head commit."""
        pr = await self.get_pull_request(repo_name, pr_number)
        head_sha = pr.get("head", {}).get("sha")
        if not head_sha:
            return []
        data = await self._request(
            self._github.rest.checks.async_list_for_ref,
            self.org,
            repo_name,
            head_sha,
            per_page=100,
            allow_statuses={403, 404},
        )
        if data is _MISSING:
            return []
        runs = data.get("check_runs", [])
        return [
            {"name": r.get("name"), "status": r.get("status"), "conclusion": r.get("conclusion")}
            for r in runs
        ]

    async def get_pr_comments_async(self, repo_name: str, pr_number: int):
        """List issue comments for a pull request."""
        comments = await self._request(
            self._github.rest.issues.async_list_comments,
            self.org,
            repo_name,
            pr_number,
            per_page=100,
            allow_statuses={403, 404},
        )
        if comments is _MISSING:
            return []
        return [
            {"body": c.get("body", ""), "user": (c.get("user") or {}).get("login", "")}
            for c in comments
        ]

# Singleton instance
github_client = GitHubClient()
