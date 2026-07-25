import json
from pathlib import Path

import pytest

from dbman_opsi.journal import RunJournal, summarize
from dbman_opsi.runner import CommandRunner


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_journal_appends_redacted_command_entries(tmp_path: Path) -> None:
    journal = RunJournal(
        run_id="run-123",
        profile="DEFAULT",
        region="eu-frankfurt-1",
        root=tmp_path / "runs",
        now=lambda: 1710000000.25,
    )

    journal.record(
        argv=[
            "oci",
            "db",
            "get",
            "--database-id",
            "ocid1" + ".database.oc1..aaaaaaaa",
            "--endpoint",
            "10.42.7.9",
        ],
        returncode=0,
        duration_ms=42,
        dry_run=False,
    )

    entries = _read_jsonl(tmp_path / "runs" / "run-123.jsonl")
    assert entries == [
        {
            "ts": 1710000000.25,
            "run_id": "run-123",
            "profile": "DEFAULT",
            "region": "eu-frankfurt-1",
            "argv_redacted": [
                "oci",
                "db",
                "get",
                "--database-id",
                "<OCI_OCID>",
                "--endpoint",
                "<PRIVATE_IP>",
            ],
            "returncode": 0,
            "duration_ms": 42,
            "dry_run": False,
        }
    ]
    raw = (tmp_path / "runs" / "run-123.jsonl").read_text(encoding="utf-8")
    assert "ocid1" + "." not in raw
    assert "10.42.7.9" not in raw


def test_journal_appends_one_json_line_per_record(tmp_path: Path) -> None:
    values = iter((1.0, 2.0))
    journal = RunJournal(
        run_id="run-append",
        profile="p",
        region="r",
        root=tmp_path / "runs",
        now=lambda: next(values),
    )

    journal.record(argv=["first"], returncode=0, duration_ms=1, dry_run=True)
    journal.record(argv=["second"], returncode=7, duration_ms=2, dry_run=False)

    lines = (tmp_path / "runs" / "run-append.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["argv_redacted"] for line in lines] == [["first"], ["second"]]


def test_runner_journals_live_command_and_keeps_raw_stdout(tmp_path: Path) -> None:
    ocid = "ocid1" + ".database.oc1..realexample"
    journal = RunJournal(
        run_id="run-live",
        profile="DEFAULT",
        region="eu-frankfurt-1",
        root=tmp_path / "runs",
        now=lambda: 500.0,
    )
    ticks = iter((100.0, 100.125))
    runner = CommandRunner(dry_run=False, journal=journal, run_id="run-live", clock=lambda: next(ticks))

    result = runner.run(["python3", "-c", f"print('{{\"id\": \"{ocid}\"}}')", ocid])

    assert result.json()["id"] == ocid
    entries = _read_jsonl(tmp_path / "runs" / "run-live.jsonl")
    assert entries[0]["returncode"] == 0
    assert entries[0]["duration_ms"] == 125
    assert entries[0]["dry_run"] is False
    raw = (tmp_path / "runs" / "run-live.jsonl").read_text(encoding="utf-8")
    assert "ocid1" + "." not in raw


def test_runner_journals_dry_run_commands(tmp_path: Path) -> None:
    journal = RunJournal(
        run_id="run-dry",
        profile="DEFAULT",
        region="eu-frankfurt-1",
        root=tmp_path / "runs",
        now=lambda: 600.0,
    )
    ticks = iter((20.0, 20.003))
    runner = CommandRunner(dry_run=True, journal=journal, run_id="run-dry", clock=lambda: next(ticks))

    result = runner.run(["oci", "db", "get", "--database-id", "ocid1" + ".database.oc1..dryrun"])

    assert result.returncode == 0
    assert result.json() == {}
    entries = _read_jsonl(tmp_path / "runs" / "run-dry.jsonl")
    assert entries[0]["dry_run"] is True
    assert entries[0]["duration_ms"] == 3
    assert "ocid1" + "." not in (tmp_path / "runs" / "run-dry.jsonl").read_text(encoding="utf-8")


def test_run_journal_reads_jsonl_and_summarizes_failures(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    root.mkdir()
    path = root / "run-read.jsonl"
    first = {
        "argv_redacted": ["oci", "db", "get"],
        "returncode": 0,
        "duration_ms": 12,
    }
    second = {
        "argv_redacted": ["oci", "db", "bad"],
        "returncode": 2,
        "duration_ms": 8,
    }
    path.write_text(
        json.dumps(first) + "\n" + json.dumps(second) + "\n",
        encoding="utf-8",
    )

    entries = RunJournal.read("run-read", root=root)
    summary = summarize(entries)

    assert entries == [first, second]
    assert summary == {
        "command_count": 2,
        "total_duration_ms": 20,
        "failures": [second],
    }


def test_run_journal_rejects_pathlike_run_id(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    root.mkdir()
    (tmp_path / "outside.jsonl").write_text('{"returncode": 0}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="plain run id"):
        RunJournal.read("../outside", root=root)
