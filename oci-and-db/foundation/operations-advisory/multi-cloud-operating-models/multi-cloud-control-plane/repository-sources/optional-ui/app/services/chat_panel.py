"""Small, read-only evidence model for the chat request panel."""
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re

from fastapi import HTTPException
from githubkit.exception import RequestFailed

from app.services.catalog_service import CatalogService
from app.services.manifest_service import validate_oci_adb_secret_references


def _panel(project, environment, region):
    return {
        "project": project, "environment": environment, "region": region,
        "kind": "empty", "resources": [], "secret_keys": [], "secret_references": [],
        "stages": [
            {"label": label, "state": "waiting", "detail": ""}
            for label in ("Proposal", "Confirmation", "PR & checks", "Review & merge", "Execution")
        ],
    }


def _in_scope(path, environment, region):
    parts = PurePosixPath(path).parts
    return len(parts) >= 5 and parts[:3] == ("oci", environment, region) and ".." not in parts


def proposal_panel(workspace, project, environment, region, candidate_path, manifest_path, resource_keys, crq):
    """Read only selected resource records, never expose the raw candidate."""
    try:
        path = Path(candidate_path).resolve(strict=True)
        if not path.is_relative_to(Path(workspace).resolve()) or path.suffix != ".json" or path.stat().st_size > 1024 * 1024:
            raise ValueError
        if not _in_scope(manifest_path, environment, region) or not manifest_path.endswith(".json"):
            raise ValueError
        if not re.fullmatch(r"CRQ[0-9]{1,20}", crq or ""):
            raise ValueError
        data = json.loads(path.read_text())
        is_operation = PurePosixPath(manifest_path).parts[3] == "lifecycle_operations"
        is_clear = is_operation and data == {}
        if ((not resource_keys and not is_clear) or (resource_keys and is_clear)
                or len(resource_keys) > 20
                or any(not isinstance(key, str) or len(key) > 160 for key in resource_keys)):
            raise ValueError
    except (ValueError, OSError, TypeError):
        raise ValueError("Provide a scoped candidate JSON, CRQ and explicit resource keys.") from None

    records = []
    secrets = set()
    native_references = validate_oci_adb_secret_references(data)
    if is_clear:
        panel = _panel(project, environment, region)
        panel.update(kind="proposal", request_type="operation_clear", crq=crq, manifest_path=manifest_path,
                     summary="Remove the pending lifecycle request; no cloud action will run.",
                     source="Local clear candidate · review the full proposal in chat")
        panel["stages"][0].update(state="done", detail="Pending operation removal prepared.")
        panel["stages"][1].update(state="current", detail="Review the removal and reply confirm to publish it.")
        return panel

    def walk(value, key=""):
        if isinstance(value, dict):
            for field, content in value.items():
                if (field == "admin_password_secret_id" and key in native_references
                        and value is data["autonomous_databases_configuration"]["databases"][key]):
                    continue
                if re.search(r"password|private_key|secret_value|access_token", field, re.I) and content:
                    if not isinstance(content, str) or not re.fullmatch(r"__[A-Z0-9_]+__", content):
                        raise ValueError("The candidate contains a literal credential. Use runtime placeholders.")
                    secrets.add(content[2:-2])
            names = [key] + [value.get(field) for field in ("display_name", "name", "db_name")]
            if any(selected in names for selected in resource_keys):
                records.append((key, value))
            for child_key, child in value.items():
                walk(child, child_key)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    if is_operation and (not isinstance(data, dict) or not isinstance(data.get("operation_type"), str)):
        raise ValueError("An operation candidate must name its operation type.")
    # Every selection must resolve once; do not silently summarize another resource.
    for selected in resource_keys:
        matches = [record for key, record in records if selected in (key, record.get("display_name"), record.get("name"), record.get("db_name"))]
        if len(matches) != 1:
            raise ValueError("Each resource key must identify exactly one candidate record.")
    panel = _panel(project, environment, region)
    panel.update(kind="proposal", crq=crq, manifest_path=manifest_path,
                 request_type="operation" if is_operation else "resource",
                 secret_keys=sorted(secrets), source="Local candidate · review the full proposal in chat")
    if is_operation:
        panel["operation_type"] = data["operation_type"][:100]
    for key, record in records:
        details = CatalogService.resource_facts(record)
        for field in ("shape", "db_workload", "action"):
            if isinstance(record.get(field), str):
                details.append(record[field][:100])
        if isinstance(record.get("freeform_tags"), dict) and isinstance(record["freeform_tags"].get("Tier"), str):
            details.append(record["freeform_tags"]["Tier"][:100])
        for field, label in (("ingress_rules", "ingress rules"), ("egress_rules", "egress rules")):
            if isinstance(record.get(field), dict):
                details.append(f"{len(record[field])} {label}")
        name = record.get("display_name") or record.get("name") or record.get("db_name") or key
        panel["resources"].append({"name": str(name)[:160], "key": key, "details": " · ".join(details)})
        if key in native_references:
            panel["secret_references"].append({"resource": str(name)[:160], "secret_id": native_references[key]})
    panel["stages"][0].update(state="done", detail="Candidate prepared; review the chat before confirming.")
    panel["stages"][1].update(state="current", detail="Reply confirm only after reviewing the proposal.")
    return panel


def _run_state(run):
    if run is None:
        return "waiting", "No matching workflow run recorded."
    if run.get("status") != "completed":
        return "current", "Workflow running or waiting."
    conclusion = run.get("conclusion")
    if conclusion == "success":
        return "done", "Workflow succeeded."
    if conclusion in {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}:
        return "failed", f"Workflow {conclusion.replace('_', ' ')}. Open GitHub for details."
    return "unknown", "Workflow did not record a successful execution."


async def pr_panel(client, project, environment, region, number):
    """Independently verify PR scope and exact workflow/commit evidence."""
    panel = _panel(project, environment, region)
    panel.update(kind="pr", pr_number=number,
                 pr_url=f"https://github.com/multicloud-control-plane/{project}/pull/{number}",
                 source="GitHub · read-only verification", checked_at=datetime.now(timezone.utc).isoformat())
    try:
        evidence = await client.get_chat_pr_evidence(project, number)
        pr, files, runs = evidence["pr"], evidence["files"], evidence["runs"]
        if pr.get("base", {}).get("repo", {}).get("full_name") != f"multicloud-control-plane/{project}" or pr["base"].get("ref") != "main":
            raise ValueError
        if not files or len(files) >= 100 or not all(_in_scope(item["filename"], environment, region) for item in files):
            raise ValueError
        workflows = set()
        for item in files:
            path = item["filename"]
            if PurePosixPath(path).parts[3] == "lifecycle_operations" and path.endswith(".json"):
                workflows.add(".github/workflows/ansible.yaml")
            elif path.endswith(".json"):
                workflows.add(".github/workflows/terraform.yaml")
            else:
                raise ValueError
        panel.update(title=pr.get("title", "Pull request"), files=[item["filename"] for item in files])
        panel["stages"][0].update(state="done", detail="Request recorded in this PR.")
        panel["stages"][1].update(state="external", detail="Existing PR; confirmation is not recorded by this panel.")

        def stage_runs(sha, event):
            selected = []
            for workflow in sorted(workflows):
                matching = [run for run in runs if run.get("head_sha") == sha and run.get("event") == event
                            and run.get("path") == workflow and (event != "push" or run.get("head_branch") == "main")]
                selected.append(max(matching, key=lambda run: (run.get("id", 0), run.get("run_attempt", 0)), default=None))
            states = [_run_state(run) for run in selected]
            state = next((key for key in ("failed", "unknown", "current", "waiting") if any(s[0] == key for s in states)), "done")
            detail = next((detail for key, detail in states if key == state), "All matching workflows succeeded.")
            return selected, state, detail

        _, state, detail = stage_runs(pr["head"]["sha"], "pull_request_target")
        panel["stages"][2].update(state=state, detail=detail)
        if pr.get("merged"):
            panel["stages"][3].update(state="done", detail="PR merged into main. Review evidence remains in GitHub.")
            selected, state, detail = stage_runs(pr.get("merge_commit_sha"), "push")
            if state == "done":
                for run in selected:
                    expected = "Terraform apply" if run["path"].endswith("terraform.yaml") else "Ansible execute"
                    jobs = evidence["jobs"].get(str(run["id"]), [])
                    executed = [job for job in jobs if job.get("name", "").split(" / ")[-1] == expected]
                    if not executed or any(job.get("status") != "completed" or job.get("conclusion") != "success" for job in executed):
                        state, detail = "unknown", "Successful apply job not verified. Open the workflow in GitHub."
                        break
                    # An Ansible wrapper can succeed when lifecycle-clear skips execution.
                    # Without the actual execution step, keep the resource outcome unknown.
                    execution_step = "Execute Terraform" if run["path"].endswith("terraform.yaml") else "Ansible execute"
                    if any(not any(step.get("name") == execution_step and step.get("conclusion") == "success"
                                   for step in job.get("steps", [])) for job in executed):
                        state, detail = "unknown", "Workflow succeeded; actual execution is not verified. Check its logs in GitHub."
                        break
                else:
                    detail = "Apply succeeded for this PR's merge commit."
            panel["stages"][4].update(state=state, detail=detail)
        elif pr.get("state") == "closed":
            panel["stages"][3].update(state="closed", detail="PR closed without merge. No deployment from this PR.")
        else:
            panel["stages"][3].update(state="current" if state == "done" else "waiting", detail="Independent human review and merge required in GitHub.")
        return panel
    except Exception as error:
        if isinstance(error, RequestFailed):
            response = error.response
            rate_limited = response.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in response.headers
            if response.status_code in {401, 403} and not rate_limited:
                raise HTTPException(response.status_code, "Sign in again; GitHub evidence access was denied.") from None
        for stage in panel["stages"]:
            stage.update(state="unknown", detail="")
        panel["source"] = "Unable to verify GitHub evidence for this scope. Refresh or open the PR."
        return panel
