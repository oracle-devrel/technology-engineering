import os
from pathlib import Path

from dbman_opsi.envfile import load_env_file


def test_load_env_file_reads_local_variables(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "\n".join(
            [
                "# local secrets",
                "TF_VAR_db_admin_password='secret value'",
                'export TF_VAR_ssh_public_keys="[key]"',
                "UNQUOTED=value # comment",
            ]
        ),
        encoding="utf-8",
    )
    for key in ("TF_VAR_db_admin_password", "TF_VAR_ssh_public_keys", "UNQUOTED"):
        monkeypatch.delenv(key, raising=False)

    loaded = load_env_file(env_file)

    assert loaded == ("TF_VAR_db_admin_password", "TF_VAR_ssh_public_keys", "UNQUOTED")
    assert os.environ["TF_VAR_db_admin_password"] == "secret value"
    assert os.environ["TF_VAR_ssh_public_keys"] == "[key]"
    assert os.environ["UNQUOTED"] == "value"


def test_load_env_file_does_not_override_existing_values(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text("TF_VAR_db_admin_password=from-file\n", encoding="utf-8")
    monkeypatch.setenv("TF_VAR_db_admin_password", "from-env")

    loaded = load_env_file(env_file)

    assert loaded == ()
    assert os.environ["TF_VAR_db_admin_password"] == "from-env"


def test_load_env_file_missing_file_is_noop(tmp_path: Path) -> None:
    assert load_env_file(tmp_path / ".env.local") == ()
