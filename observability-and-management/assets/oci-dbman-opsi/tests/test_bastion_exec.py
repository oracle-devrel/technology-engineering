from pathlib import Path

import pytest

from dbman_opsi.bastion_exec import BastionSqlRunner
from dbman_opsi.config import Target


class _FakeExec:
    """Records foreground/background commands; returns canned stdout."""

    def __init__(self):
        self.fg: list[list[str]] = []
        self.bg: list[list[str]] = []

    def run(self, argv, input=None):  # noqa: A002 - mirror subprocess signature
        self.fg.append(argv)
        return "OK"

    def run_bg(self, argv):
        self.bg.append(argv)


class _ListingExec(_FakeExec):
    def __init__(self, payload: str, *, fail_delete: str | None = None) -> None:
        super().__init__()
        self.payload = payload
        self.fail_delete = fail_delete

    def run(self, argv, input=None):  # noqa: A002 - mirror subprocess signature
        self.fg.append(argv)
        joined = " ".join(argv)
        if "session list" in joined:
            return self.payload
        if self.fail_delete and self.fail_delete in joined:
            raise RuntimeError("delete failed")
        return "OK"


def _runner(ex, **kw):
    return BastionSqlRunner(
        bastion_id="ocid1.bastion.x",
        target_private_ip="10.0.0.5",
        ssh_key="/keys/id",
        profile="cap",
        region="eu-frankfurt-1",
        exec_fn=ex.run,
        exec_bg_fn=ex.run_bg,
        session_id_fn=lambda: "ocid1.bastionsession.x",
        sleeper=lambda d: None,
        local_port=8022,
        **kw,
    )


def test_runner_creates_session_tunnel_runs_scripts_and_tears_down(tmp_path: Path) -> None:
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    s2 = tmp_path / "06.sql"; s2.write_text("-- b")
    ex = _FakeExec()
    target = Target(kind="dbcs", name="cdb", service_name="PDB1")

    out = _runner(ex).__call__(target, [s1, s2])

    flat = " | ".join(" ".join(c) for c in ex.fg)
    # Session created with work-request wait, scripts scp'd + run, session deleted.
    assert "bastion session create-port-forwarding" in flat
    assert "--wait-for-state SUCCEEDED" in flat
    assert ex.bg and "8022:10.0.0.5:22" in " ".join(ex.bg[0])         # tunnel started
    assert sum("scp" in c[0] for c in ex.fg) == 2                      # both scripts copied
    assert any("sqlplus" in " ".join(c) for c in ex.fg)               # executed as sysdba
    assert "session delete" in flat                                   # torn down
    assert "OK" in out


def test_runner_uses_tofu_known_hosts_never_dev_null(tmp_path: Path) -> None:
    # §3 HIGH fix: host-key verification must be TOFU (accept-new) into a per-run
    # known_hosts file on EVERY hop — never StrictHostKeyChecking=no / /dev/null.
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    kh = tmp_path / "kh"
    ex = _FakeExec()

    _runner(ex, known_hosts=str(kh)).__call__(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    hops = ex.bg + [c for c in ex.fg if c and c[0] in {"ssh", "scp"}]
    assert hops, "expected tunnel + scp + ssh hops"
    for hop in hops:
        joined = " ".join(hop)
        assert "StrictHostKeyChecking=no" not in joined
        assert "UserKnownHostsFile=/dev/null" not in joined
        assert "StrictHostKeyChecking=accept-new" in joined
        assert f"UserKnownHostsFile={kh}" in joined


def test_runner_auto_creates_per_run_known_hosts_when_unset(tmp_path: Path) -> None:
    # With no known_hosts supplied, the runner provisions its own per-run file
    # (required because the loopback tunnel maps to a different host each run).
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()

    _runner(ex).__call__(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    scp = next(c for c in ex.fg if c and c[0] == "scp")
    kh_opt = next(a for a in scp if a.startswith("UserKnownHostsFile="))
    path = kh_opt.split("=", 1)[1]
    assert path not in {"/dev/null", ""}
    assert not Path(path).exists()  # per-run file cleaned up in finally


def test_runner_removes_remote_scripts_after_run(tmp_path: Path) -> None:
    # §3 MED: uploaded scripts must not linger in /tmp on the DB host.
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    s2 = tmp_path / "06.sql"; s2.write_text("-- b")
    ex = _FakeExec()

    _runner(ex).__call__(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1, s2])

    flat = " | ".join(" ".join(c) for c in ex.fg)
    assert "rm -f /tmp/01.sql /tmp/06.sql" in flat


def test_runner_registers_idempotent_atexit_teardown(tmp_path: Path) -> None:
    # §1 HIGH: an interpreter exit must still delete the bastion session, and the
    # atexit hook must not double-delete when the normal finally already ran.
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()
    registered: list = []

    _runner(ex, atexit_register=registered.append).__call__(
        Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1]
    )

    deletes_during_run = sum("session delete" in " ".join(c) for c in ex.fg)
    assert deletes_during_run == 1               # torn down once by the finally
    assert registered, "expected an atexit teardown to be registered"
    registered[0]()                              # simulate interpreter exit
    deletes_after = sum("session delete" in " ".join(c) for c in ex.fg)
    assert deletes_after == 1                     # idempotent: no second delete


class _Handle:
    """Stands in for the ssh-forward Popen; records terminate() calls."""

    def __init__(self) -> None:
        self.terminated = 0

    def terminate(self) -> None:
        self.terminated += 1


def test_forward_process_is_terminated_in_finally(tmp_path: Path) -> None:
    # H1: the local ssh -L forward must die with the run, not orphan and hold the
    # port for a later run to misdeliver the password onto a stale host.
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()
    handle = _Handle()

    def run_bg(argv: list[str]) -> _Handle:
        ex.bg.append(argv)
        return handle

    BastionSqlRunner(
        bastion_id="b", target_private_ip="10.0.0.5", ssh_key="/k",
        profile="cap", region="eu-frankfurt-1", local_port=8022,
        exec_fn=ex.run, exec_bg_fn=run_bg, session_id_fn=lambda: "s", sleeper=lambda d: None,
    )(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    assert handle.terminated == 1


def test_forward_drops_dash_f_so_caller_owns_the_process(tmp_path: Path) -> None:
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()

    _runner(ex).__call__(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    forward = ex.bg[0]
    assert "-fNL" not in forward and "-f" not in forward   # not self-backgrounded
    assert "-NL" in forward                                 # Popen owns the foreground forward


def test_ephemeral_local_port_when_unset(tmp_path: Path) -> None:
    # H1: with no explicit local_port, a fresh ephemeral port is chosen per run and
    # used consistently for the forward, scp and ssh — so a leaked forward on a
    # fixed 8022 can never be silently reused.
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()
    runner = BastionSqlRunner(
        bastion_id="b", target_private_ip="10.0.0.5", ssh_key="/k",
        profile="cap", region="eu-frankfurt-1",
        exec_fn=ex.run, exec_bg_fn=ex.run_bg, session_id_fn=lambda: "s", sleeper=lambda d: None,
    )

    runner(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    scp = next(c for c in ex.fg if c and c[0] == "scp")
    port = scp[scp.index("-P") + 1]
    assert int(port) > 1024 and port != "8022"
    assert f"{port}:10.0.0.5:22" in " ".join(ex.bg[0])


def test_rejects_remote_script_name_with_shell_metacharacters(tmp_path: Path) -> None:
    # L6/M: script.name is interpolated into remote shell strings; reject anything
    # that isn't a plain filename before it reaches scp/ssh.
    bad = tmp_path / "evil; rm -rf x.sql"
    bad.write_text("-- x")
    ex = _FakeExec()

    with pytest.raises(ValueError):
        _runner(ex).__call__(Target(kind="dbcs", name="cdb", service_name="PDB1"), [bad])


def test_runner_tears_down_even_when_a_script_fails(tmp_path: Path) -> None:
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    ex = _FakeExec()

    def boom(argv, input=None):  # noqa: A002
        ex.fg.append(argv)
        if any("sqlplus" in a for a in argv):
            raise RuntimeError("ORA-00942")
        return "OK"

    runner = _runner(ex)
    runner._exec = boom  # type: ignore[assignment]

    with pytest.raises(RuntimeError):
        runner(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    # The bastion session must still be deleted on failure (cleanup in finally).
    assert any("delete" in " ".join(c) for c in ex.fg)


def test_resolve_session_id_parses_quoted_and_plain() -> None:
    ex = _FakeExec()
    # Default resolver uses self._exec; stub it to return a JSON-quoted OCID.
    runner = BastionSqlRunner(
        bastion_id="b", target_private_ip="xxxx", ssh_key="/k", profile="cap", region="eu-frankfurt-1",
        exec_fn=lambda argv, input=None: '"ocid1.bastionsession.q"\n',
        exec_bg_fn=ex.run_bg, sleeper=lambda d: None,
    )
    assert runner._resolve_session_id() == "ocid1.bastionsession.q"

    runner2 = BastionSqlRunner(
        bastion_id="b", target_private_ip="xxx", ssh_key="/k", profile="cap", region="eu-frankfurt-1",
        exec_fn=lambda argv, input=None: "ocid1.bastionsession.plain\n",
        exec_bg_fn=ex.run_bg, sleeper=lambda d: None,
    )
    assert runner2._resolve_session_id() == "ocid1.bastionsession.plain"


def test_teardown_is_best_effort_on_delete_failure() -> None:
    calls: list[str] = []

    def ex(argv, input=None):  # noqa: A002
        calls.append(" ".join(argv))
        raise RuntimeError("delete blew up")

    runner = BastionSqlRunner(
        bastion_id="b", target_private_ip="xxx", ssh_key="/k", profile="cap", region="eu-frankfurt-1",
        exec_fn=ex, exec_bg_fn=lambda a: None, sleeper=lambda d: None,
    )
    # Must not raise even though the delete command fails.
    runner._teardown("ocid1.bastionsession.x")
    assert any("session delete" in c for c in calls)


def test_reaps_stale_dbman_sessions_before_creating_new_session(tmp_path: Path) -> None:
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    payload = (
        '{"data": ['
        '{"id": "stale-active", "display-name": "dbman-exec-old-a", '
        '"lifecycle-state": "ACTIVE", "time-created": "2026-06-13T08:00:00+00:00"},'
        '{"id": "stale-creating", "display-name": "dbman-exec-old-b", '
        '"lifecycle-state": "CREATING", "time-created": "2026-06-13T08:01:00+00:00"},'
        '{"id": "other-tool", "display-name": "other-tool", '
        '"lifecycle-state": "ACTIVE", "time-created": "2026-06-13T08:00:00+00:00"}'
        ']}'
    )
    ex = _ListingExec(payload)
    runner = _runner(ex, now=lambda: 1_781_338_000.0, stale_session_age=60)

    runner(Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1])

    commands = [" ".join(command) for command in ex.fg]
    create_index = next(
        i for i, command in enumerate(commands) if "create-port-forwarding" in command
    )
    pre_create_deletes = [
        command for command in commands[:create_index] if "session delete" in command
    ]
    assert any("--session-id stale-active" in command for command in pre_create_deletes)
    assert any("--session-id stale-creating" in command for command in pre_create_deletes)
    assert all("other-tool" not in command for command in pre_create_deletes)


def test_reap_delete_failure_does_not_abort_new_session(tmp_path: Path) -> None:
    s1 = tmp_path / "01.sql"; s1.write_text("-- a")
    payload = (
        '{"data": [{"id": "stale-active", "display-name": "dbman-exec-old", '
        '"lifecycle-state": "ACTIVE", "time-created": "2026-06-13T08:00:00+00:00"}]}'
    )
    ex = _ListingExec(payload, fail_delete="--session-id stale-active")

    out = _runner(ex, now=lambda: 1_781_338_000.0, stale_session_age=60).__call__(
        Target(kind="dbcs", name="cdb", service_name="PDB1"), [s1]
    )

    flat = " | ".join(" ".join(command) for command in ex.fg)
    assert "session delete --session-id stale-active" in flat
    assert "create-port-forwarding" in flat
    assert "OK" in out
