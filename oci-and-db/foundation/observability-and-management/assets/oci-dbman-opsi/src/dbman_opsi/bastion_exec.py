"""Bastion-based SQL transport for the hybrid DB-side executor.

Implements the proven Bastion procedure as an injectable ``SqlRunner`` for
``db_exec.DbExecService``: create a managed-SSH **port-forwarding** session to the
DB node :22, tunnel a local port through it, ``scp`` each generated script to the
host and run it as ``oracle`` via ``sqlplus / as sysdba``, then tear the session
down. The session is always deleted in a ``finally`` block.

The subprocess calls are injected (``exec_fn``/``exec_bg_fn``/``session_id_fn``)
so the command sequence is unit-tested without real SSH; the defaults shell out.

Note: the generated DB-side scripts use SQL*Plus ``accept`` prompts (so passwords
are never stored). When auto-executing, supply the answers non-interactively via
``answers`` (piped to the script's stdin) — e.g. the PDB/container name and the
monitoring password — in the order the script prompts for them.
"""

from __future__ import annotations

import atexit
import json
import os
import re
import shlex
import socket
import subprocess
import tempfile
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from dbman_opsi.config import Target

# A remote script filename must be a plain name — it is interpolated into remote
# shell command strings (scp target, sqlplus @path, rm -f), so anything with
# whitespace or shell metacharacters is rejected before it can reach a shell.
_SAFE_REMOTE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _free_port() -> int:
    """Pick a currently-free local TCP port for this run's tunnel."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _default_exec(argv: list[str], input: str | None = None) -> str:  # noqa: A002
    result = subprocess.run(argv, input=input, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(argv[:3])}…\n{result.stderr}")
    return result.stdout


def _default_exec_bg(argv: list[str]) -> subprocess.Popen:
    # Return the handle so the caller owns the forward's lifecycle and can
    # terminate it when the run ends (the forward runs foreground under Popen;
    # ssh is invoked without -f so it does not self-background and detach).
    return subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class BastionSqlRunner:
    def __init__(
        self,
        bastion_id: str,
        target_private_ip: str,
        ssh_key: str,
        profile: str,
        region: str,
        *,
        local_port: int | None = None,
        bastion_host: str | None = None,
        session_ttl: int = 3600,
        remote_dir: str = "/tmp",  # nosec B108 - remote DB-host SSH path, not a local tempfile
        answers: str | None = None,
        known_hosts: str | None = None,
        exec_fn: Callable[..., str] | None = None,
        exec_bg_fn: Callable[[list[str]], Any] | None = None,
        session_id_fn: Callable[[], str] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.time,
        stale_session_age: int | None = None,
        tunnel_wait: float = 6.0,
        atexit_register: Callable[[Callable[[], None]], Any] = atexit.register,
        atexit_unregister: Callable[[Callable[[], None]], Any] = atexit.unregister,
    ) -> None:
        self.bastion_id = bastion_id
        self.target_private_ip = target_private_ip
        self.ssh_key = ssh_key
        self.profile = profile
        self.region = region
        self.local_port = local_port
        self.bastion_host = bastion_host or f"host.bastion.{region}.oci.oraclecloud.com"
        self.session_ttl = session_ttl
        self.remote_dir = remote_dir
        self.answers = answers
        self.known_hosts = known_hosts
        self._exec = exec_fn or _default_exec
        self._exec_bg = exec_bg_fn or _default_exec_bg
        self._session_id_fn = session_id_fn or self._resolve_session_id
        self._sleep = sleeper
        self._now = now
        self.stale_session_age = session_ttl if stale_session_age is None else stale_session_age
        self.tunnel_wait = tunnel_wait
        self._atexit_register = atexit_register
        self._atexit_unregister = atexit_unregister

    # SqlRunner protocol: (target, scripts) -> combined output.
    def __call__(self, target: Target, scripts: list[Path]) -> str:
        display_name = f"dbman-exec-{target.name}".replace(" ", "-").lower()[:60]
        self._reap_stale_sessions()
        self._exec([
            "oci", "--profile", self.profile, "--region", self.region,
            "bastion", "session", "create-port-forwarding",
            "--bastion-id", self.bastion_id,
            "--display-name", display_name,
            "--ssh-public-key-file", f"{self.ssh_key}.pub",
            "--target-private-ip", self.target_private_ip,
            "--target-port", "22",
            "--session-ttl", str(self.session_ttl),
            "--wait-for-state", "SUCCEEDED",
            "--max-wait-seconds", "600", "--wait-interval-seconds", "15",
        ])
        session_id = self._session_id_fn()
        # A fresh ephemeral local port per run (unless one is pinned explicitly):
        # a leaked forward from a prior run can never be silently reused, so the
        # password is never piped to a stale host on a fixed port.
        port = self.local_port if self.local_port is not None else _free_port()
        known_hosts, kh_owned = self._known_hosts_path()
        ssh_opts = self._ssh_opts(known_hosts)

        # Idempotent teardown: registered with atexit so an interpreter exit (or an
        # unhandled signal that surfaces as an exception) still deletes the session,
        # not just the normal finally below. SIGKILL can't be caught — the session
        # TTL is the backstop for that. The guard makes the atexit + finally calls
        # collapse to a single delete, and the handler unregisters itself so it does
        # not pin this runner alive or re-fire across multiple targets.
        torn = {"done": False}

        def _safe_teardown() -> None:
            if torn["done"]:
                return
            torn["done"] = True
            self._teardown(session_id)
            self._atexit_unregister(_safe_teardown)

        self._atexit_register(_safe_teardown)

        forward: Any = None
        remote_paths: list[str] = []
        outputs: list[str] = []
        try:
            forward = self._exec_bg([
                "ssh", "-i", self.ssh_key, "-NL",
                f"{port}:{self.target_private_ip}:22", "-p", "22",
                f"{session_id}@{self.bastion_host}",
                "-o", "ExitOnForwardFailure=yes", *ssh_opts,
            ])
            self._sleep(self.tunnel_wait)
            for script in scripts:
                if not _SAFE_REMOTE_NAME.match(script.name):
                    raise ValueError(f"unsafe script name for remote execution: {script.name!r}")
                remote = f"{self.remote_dir}/{script.name}"
                remote_paths.append(remote)
                self._exec([
                    "scp", "-i", self.ssh_key, "-P", str(port), *ssh_opts,
                    str(script), f"opc@127.0.0.1:{remote}",
                ])
                outputs.append(self._exec([
                    "ssh", "-i", self.ssh_key, "-p", str(port), *ssh_opts,
                    "opc@127.0.0.1",
                    f"sudo su - oracle -c 'sqlplus -s / as sysdba @{shlex.quote(remote)}'",
                ], input=self.answers))
        finally:
            # Remove the uploaded scripts while the tunnel is still up (before
            # teardown), then kill the forward and delete the session.
            self._cleanup_remote(ssh_opts, remote_paths, port)
            self._terminate_forward(forward)
            _safe_teardown()
            if kh_owned:
                try:
                    Path(known_hosts).unlink()
                except OSError:
                    pass
        return "\n".join(outputs)

    @staticmethod
    def _terminate_forward(forward: Any) -> None:
        """Kill the local ssh forward so it does not orphan and hold the port."""

        if forward is None or not hasattr(forward, "terminate"):
            return
        try:
            forward.terminate()
        except Exception:  # noqa: BLE001 - best-effort; the forward may already be gone
            pass

    def _cleanup_remote(self, ssh_opts: list[str], remote_paths: list[str], port: int) -> None:
        """Best-effort removal of uploaded scripts from the DB host's /tmp."""

        if not remote_paths:
            return
        quoted = " ".join(shlex.quote(path) for path in remote_paths)
        try:
            self._exec([
                "ssh", "-i", self.ssh_key, "-p", str(port), *ssh_opts,
                "opc@127.0.0.1", f"rm -f {quoted}",
            ])
        except Exception:  # noqa: BLE001 - tunnel may be down; nothing else to do
            pass

    def _ssh_opts(self, known_hosts: str) -> list[str]:
        """TOFU host-key options shared by the tunnel, scp and ssh hops.

        ``accept-new`` records the host key on first contact into ``known_hosts``
        and *verifies* it for every subsequent hop in the same run — closing the
        loopback-tunnel MITM gap that ``StrictHostKeyChecking=no`` left open. The
        file is per-run because the loopback tunnel (127.0.0.1:local_port) maps to
        a different DB host each run; a persistent file would reject the new key as
        a host-key change.
        """

        return [
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={known_hosts}",
            "-o", "ConnectTimeout=20",
        ]

    def _known_hosts_path(self) -> tuple[str, bool]:
        """Return ``(path, owned)``; create a 0600 per-run file when unset."""

        if self.known_hosts:
            return self.known_hosts, False
        fd, path = tempfile.mkstemp(prefix="dbman-knownhosts-")
        os.close(fd)
        os.chmod(path, 0o600)
        return path, True

    def _teardown(self, session_id: str) -> None:
        try:
            self._exec([
                "oci", "--profile", self.profile, "--region", self.region,
                "bastion", "session", "delete", "--session-id", session_id, "--force",
            ])
        except Exception:  # noqa: BLE001 - teardown is best-effort
            pass

    def _reap_stale_sessions(self) -> None:
        try:
            sessions = self._list_bastion_sessions()
        except Exception:  # noqa: BLE001 - stale-session sweep is best-effort
            return
        for session in sessions:
            if self._is_stale_dbman_session(session):
                self._teardown(str(session.get("id") or ""))

    def _list_bastion_sessions(self) -> list[dict[str, Any]]:
        raw = self._exec([
            "oci", "--profile", self.profile, "--region", self.region,
            "bastion", "session", "list", "--bastion-id", self.bastion_id, "--all",
            "--output", "json",
        ])
        payload = json.loads(raw or "{}")
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return list(data) if isinstance(data, list) else []

    def _is_stale_dbman_session(self, session: dict[str, Any]) -> bool:
        name = str(session.get("display-name") or "")
        state = str(session.get("lifecycle-state") or "")
        session_id = str(session.get("id") or "")
        created = self._session_created_epoch(session)
        if not name.startswith("dbman-exec-") or state not in {"ACTIVE", "CREATING"}:
            return False
        return bool(
            session_id
            and created is not None
            and self._now() - created > self.stale_session_age
        )

    @staticmethod
    def _session_created_epoch(session: dict[str, Any]) -> float | None:
        value = session.get("time-created")
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None

    def _resolve_session_id(self) -> str:
        # Default resolver: list active sessions and return the most recent id.
        raw = self._exec([
            "oci", "--profile", self.profile, "--region", self.region,
            "bastion", "session", "list", "--bastion-id", self.bastion_id, "--all",
            "--query", "data[?\"lifecycle-state\"=='ACTIVE']|[0].id",
            "--raw-output", "--output", "json",
        ])
        value = raw.strip()
        if value.startswith('"'):
            value = json.loads(value)
        return value
