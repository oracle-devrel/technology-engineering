import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "pre-push"


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "test@example.invalid")
    _run_git(repo, "config", "user.name", "Test User")
    (repo / ".gitleaks.toml").write_text("title = \"test\"\n", encoding="utf-8")
    (repo / "README.md").write_text("clean\n", encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")


def _run_hook(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HOOK)],
        cwd=repo,
        text=True,
        input="",
        capture_output=True,
        check=False,
    )


def _synthetic_ocid() -> str:
    return "ocid1" + ".tenancy.oc1.." + ("a" * 40)


def test_pre_push_script_is_executable() -> None:
    mode = HOOK.stat().st_mode

    assert mode & stat.S_IXUSR


def test_pre_push_blocks_synthetic_identifier_in_working_tree(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "leak.txt").write_text(f"id={_synthetic_ocid()}\n", encoding="utf-8")

    result = _run_hook(tmp_path)

    assert result.returncode == 1
    assert "real OCI identifier" in result.stderr
    assert "leak.txt" in result.stderr


def test_pre_push_allows_synthetic_identifier_in_markdown(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "notes.md").write_text(f"placeholder-ish {_synthetic_ocid()}\n", encoding="utf-8")

    result = _run_hook(tmp_path)

    assert result.returncode == 0


def test_pre_push_passes_clean_tree(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = _run_hook(tmp_path)

    assert result.returncode == 0


def test_pre_push_embeds_format_patterns_not_real_identifiers() -> None:
    script = HOOK.read_text(encoding="utf-8")
    banned_fragments = [
        _synthetic_ocid(),
        "fr4zqfimuxtr",
        "axoxdievda5j",
        "id9y6mi8tcky",
        "aaaadhp5ewo4eaaaaaaaaafs7q",
        "axfo51x8x2ap",
    ]

    for fragment in banned_fragments:
        assert fragment not in script
