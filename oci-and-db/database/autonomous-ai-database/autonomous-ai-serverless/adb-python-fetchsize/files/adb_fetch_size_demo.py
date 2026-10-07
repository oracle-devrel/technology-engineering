#!/usr/bin/env python3
"""
Oracle Autonomous Database Serverless fetch-size testcase.

This script showcases python-oracledb Thin mode fetch performance with different
cursor.arraysize values against a small one-table data model.

Connection mode:
  - python-oracledb Thin mode
  - Autonomous Database mTLS wallet
  - Uses tnsnames.ora + ewallet.pem from the wallet directory

The script creates and loads a demo table by default. Do not run it in a schema
where a table named FETCH_SIZE_DEMO must be preserved.
"""

from __future__ import annotations

import argparse
import getpass
import os
import statistics
import time
from pathlib import Path
from typing import Iterable

import oracledb


TABLE_NAME = "FETCH_SIZE_DEMO"

DDL = f"""
create table {TABLE_NAME} (
    id          number generated always as identity primary key,
    group_id    number not null,
    payload     varchar2(200) not null,
    created_at  timestamp default systimestamp not null
)
"""

INSERT_SQL = f"""
insert into {TABLE_NAME} (group_id, payload)
select
    mod(level, 100),
    rpad('x', 200, 'x')
from dual
connect by level <= :num_rows
"""

QUERY_SQL = f"""
select id, group_id, payload, created_at
from {TABLE_NAME}
order by id
"""


def get_secret(cli_value: str | None, env_name: str, prompt: str) -> str:
    """Return a secret from CLI, environment, or interactive prompt."""
    value = cli_value or os.getenv(env_name)
    if value:
        return value
    return getpass.getpass(prompt)


def validate_wallet_dir(wallet_dir: str) -> None:
    """Validate that required Thin-mode mTLS wallet files are present."""
    path = Path(wallet_dir).expanduser().resolve()
    required_files = ["tnsnames.ora", "ewallet.pem"]
    missing = [name for name in required_files if not (path / name).is_file()]

    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            f"Wallet directory {path} is missing required file(s): {missing_list}. "
            "For python-oracledb Thin mode with Autonomous Database mTLS, "
            "the wallet directory must contain tnsnames.ora and ewallet.pem."
        )


def connect_to_adb(args: argparse.Namespace) -> oracledb.Connection:
    """
    Connect to Oracle Autonomous Database Serverless using python-oracledb Thin mode.

    Required wallet files in args.wallet_dir:
      - tnsnames.ora
      - ewallet.pem

    The DSN should be a service alias from tnsnames.ora, for example:
      myadb_low
      myadb_medium
      myadb_high
      myadb_tp
      myadb_tpurgent
    """
    validate_wallet_dir(args.wallet_dir)

    db_password = get_secret(
        cli_value=args.db_password,
        env_name="ADB_PASSWORD",
        prompt="Database password: ",
    )

    wallet_password = get_secret(
        cli_value=args.wallet_password,
        env_name="ADB_WALLET_PASSWORD",
        prompt="Wallet password: ",
    )

    return oracledb.connect(
        user=args.user,
        password=db_password,
        dsn=args.dsn,
        config_dir=args.wallet_dir,
        wallet_location=args.wallet_dir,
        wallet_password=wallet_password,
    )


def reset_demo_table(conn: oracledb.Connection, num_rows: int) -> None:
    """Drop, recreate, and populate the demo table."""
    with conn.cursor() as cur:
        try:
            cur.execute(f"drop table {TABLE_NAME} purge")
        except oracledb.DatabaseError as exc:
            error_obj = exc.args[0]
            # ORA-00942: table or view does not exist
            if getattr(error_obj, "code", None) != 942:
                raise

        cur.execute(DDL)
        cur.execute(INSERT_SQL, num_rows=num_rows)

    conn.commit()
    print(f"Created {TABLE_NAME} with {num_rows:,} rows")


def fetch_all_rows(
    conn: oracledb.Connection,
    arraysize: int,
    prefetchrows: int | None = None,
    fetchmany_size: int | None = None,
) -> tuple[float, int]:
    """
    Fetch all rows and return elapsed seconds and row count.

    arraysize:
      Driver row-array buffer size. This is the main setting being tested.

    prefetchrows:
      Optional. Leave unset for the driver's default unless you specifically
      want to compare prefetch behavior.

    fetchmany_size:
      Optional. If unset, cursor.fetchmany() uses cursor.arraysize.
    """
    with conn.cursor() as cur:
        cur.arraysize = arraysize

        if prefetchrows is not None:
            cur.prefetchrows = prefetchrows

        start = time.perf_counter()

        cur.execute(QUERY_SQL)

        row_count = 0

        while True:
            rows = cur.fetchmany(fetchmany_size) if fetchmany_size else cur.fetchmany()

            if not rows:
                break

            # Minimal processing so the test mostly measures fetch behavior.
            row_count += len(rows)

        elapsed = time.perf_counter() - start

    return elapsed, row_count


def testperf(
    conn: oracledb.Connection,
    array_sizes: Iterable[int],
    repeats: int,
    prefetchrows: int | None = None,
) -> None:
    """Run the arraysize testcase and print a compact result table."""
    print()
    print("arraysize | rows fetched | avg seconds | runs")
    print("----------+--------------+-------------+----------------")

    for arraysize in array_sizes:
        timings = []
        rows_seen = None

        for _ in range(repeats):
            elapsed, row_count = fetch_all_rows(
                conn=conn,
                arraysize=arraysize,
                prefetchrows=prefetchrows,
                fetchmany_size=None,
            )
            timings.append(elapsed)
            rows_seen = row_count

        avg = statistics.mean(timings)
        runs = ", ".join(f"{t:.3f}" for t in timings)

        print(f"{arraysize:9d} | {rows_seen:12,d} | {avg:11.3f} | {runs}")


def parse_array_sizes(value: str) -> list[int]:
    """Parse a comma-separated arraysize list."""
    sizes = [int(x.strip()) for x in value.split(",") if x.strip()]
    if not sizes:
        raise argparse.ArgumentTypeError("At least one arraysize value is required")
    if any(size <= 0 for size in sizes):
        raise argparse.ArgumentTypeError("All arraysize values must be positive integers")
    return sizes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "testcase python-oracledb Thin mode cursor.arraysize against "
            "Oracle Autonomous Database Serverless."
        )
    )

    parser.add_argument(
        "--user",
        default=os.getenv("ADB_USER", "ADMIN"),
        help="Database user. Default: ADB_USER env var, or ADMIN.",
    )

    parser.add_argument(
        "--db-password",
        default=os.getenv("ADB_PASSWORD"),
        help=(
            "Database password. Prefer ADB_PASSWORD env var instead of passing "
            "this on the command line."
        ),
    )

    parser.add_argument(
        "--wallet-password",
        default=os.getenv("ADB_WALLET_PASSWORD"),
        help=(
            "Autonomous Database wallet password. Prefer ADB_WALLET_PASSWORD "
            "env var instead of passing this on the command line."
        ),
    )

    parser.add_argument(
        "--wallet-dir",
        default=os.getenv("ADB_WALLET_DIR"),
        required=os.getenv("ADB_WALLET_DIR") is None,
        help=(
            "Directory containing tnsnames.ora and ewallet.pem from the "
            "Autonomous Database wallet."
        ),
    )

    parser.add_argument(
        "--dsn",
        default=os.getenv("ADB_DSN"),
        required=os.getenv("ADB_DSN") is None,
        help=(
            "TNS alias from tnsnames.ora, for example myadb_low, "
            "myadb_medium, myadb_high, myadb_tp, or myadb_tpurgent."
        ),
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=50_000,
        help="Number of rows to create in the demo table. Default: 50000.",
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="testcase repeats per arraysize. Default: 3.",
    )

    parser.add_argument(
        "--arraysizes",
        type=parse_array_sizes,
        default=parse_array_sizes("1,10,50,100,500,1000,5000,10000"),
        help=(
            "Comma-separated arraysize values to test. "
            "Default: 1,10,50,100,500,1000,5000,10000."
        ),
    )

    parser.add_argument(
        "--prefetchrows",
        type=int,
        default=None,
        help="Optional cursor.prefetchrows value. Usually leave unset.",
    )

    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Do not recreate and reload the demo table.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print non-secret connection diagnostics before connecting.",
    )

    return parser.parse_args()


def print_debug(args: argparse.Namespace) -> None:
    """Print diagnostics that do not include secrets."""
    wallet_dir = Path(args.wallet_dir).expanduser().resolve()
    print("python-oracledb:", oracledb.__version__)
    print("thin mode before connect:", oracledb.is_thin_mode())
    print("user:", args.user)
    print("dsn:", args.dsn)
    print("wallet_dir:", wallet_dir)
    print("tnsnames exists:", (wallet_dir / "tnsnames.ora").exists())
    print("ewallet.pem exists:", (wallet_dir / "ewallet.pem").exists())


def main() -> None:
    args = parse_args()

    if args.rows <= 0:
        raise ValueError("--rows must be a positive integer")

    if args.repeats <= 0:
        raise ValueError("--repeats must be a positive integer")

    if args.prefetchrows is not None and args.prefetchrows <= 0:
        raise ValueError("--prefetchrows must be a positive integer when set")

    if args.debug:
        print_debug(args)

    with connect_to_adb(args) as conn:
        print("Connected to Autonomous Database Serverless using python-oracledb Thin mode")

        if not args.skip_setup:
            reset_demo_table(conn, args.rows)

        testperf(
            conn=conn,
            array_sizes=args.arraysizes,
            repeats=args.repeats,
            prefetchrows=args.prefetchrows,
        )


if __name__ == "__main__":
    main()
