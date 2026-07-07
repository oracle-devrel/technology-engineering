from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_has_resource_manager_button_and_workshop_entrypoint() -> None:
    readme = read("README.md")

    assert "cloud.oracle.com/resourcemanager/stacks/create" in readme
    assert "Deploy to Oracle Cloud" in readme
    assert "docs/workshop/README.md" in readme
    assert "Cloud Shell" in readme


def test_workshop_docs_cover_end_to_end_paths_without_tenant_names() -> None:
    workshop = read("docs/workshop/README.md")
    personal_name = "ad" + "rian"
    tenant_phrase = "cap " + "tenant"

    assert "Lab 1" in workshop
    assert "Lab 2" in workshop
    assert "Lab 3" in workshop
    assert "Lab 4" in workshop
    assert "DBCS" in workshop
    assert "Autonomous Database" in workshop
    assert "Exadata" in workshop
    assert "Management Agent" in workshop
    assert personal_name not in workshop.lower()
    assert tenant_phrase not in workshop.lower()


def test_resource_manager_schema_exists_for_public_stack() -> None:
    schema = read("terraform/examples/zero-start-poc/schema.yaml")

    assert "title: OCI DB Management and Ops Insights Enablement" in schema
    assert "tenancy_ocid" in schema
    assert "compartment_ocid" in schema
    assert "password" not in schema.lower()


def test_public_surface_does_not_contain_raw_sensitive_values() -> None:
    ocid_prefix = "ocid1" + "."
    personal_name = "ad" + "rian"
    company_name = "cap" + "gemini"
    tenant_phrase = "cap " + "tenant"
    public_ip_prefixes = ("130" + ".61.", "161" + ".153.")
    checked_paths = [
        "README.md",
        "docs/workshop/README.md",
        "docs/security.md",
        "terraform/examples/zero-start-poc/main.tf",
        "terraform/examples/zero-start-poc/variables.tf",
        "terraform/examples/zero-start-poc/schema.yaml",
    ]
    combined = "\n".join(read(path) for path in checked_paths)

    assert ocid_prefix not in combined
    assert personal_name not in combined.lower()
    assert company_name not in combined.lower()
    assert tenant_phrase not in combined.lower()
    for prefix in public_ip_prefixes:
        assert prefix not in combined


def test_gitignore_excludes_public_repo_local_artifacts() -> None:
    ignore = read(".gitignore")

    for pattern in [
        "generated/",
        "dbman-opsi*.yaml",
        "dbman-opsi*.json",
        "*.log",
        ".mcp.json",
        ".claude/",
        ".agentsroom/",
        "firepit-log.txt",
        "terraform/**/terraform.tfvars.json",
    ]:
        assert pattern in ignore


def test_sanitized_screenshots_are_present() -> None:
    for path in ["docs/screenshots/readme.png", "docs/screenshots/workshop.png"]:
        screenshot = ROOT / path
        assert screenshot.exists()
        assert screenshot.stat().st_size > 10_000
