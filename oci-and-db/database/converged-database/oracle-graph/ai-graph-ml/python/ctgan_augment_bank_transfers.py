"""Create synthetic BANK_TRANSFERS rows with CTGAN.

This script is deliberately non-destructive to the source data:
  * It reads YOUR_USER.BANK_ACCOUNTS and BANK_TRANSFERS.
  * It never changes either source table.
  * It creates BANK_TRANSFERS_SYNTHETIC only when that table does not exist.

Run only after setting DB_PASSWORD in your operating-system environment:
    C:\Project\Scripts\python.exe ctgan_augment_bank_transfers.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import oracledb
import pandas as pd
from ctgan import CTGAN
from joblib import parallel_config


# Change these settings only if you choose a different demo scale/table name.
SYNTHETIC_ROWS = 4_999
OUTPUT_TABLE = "BANK_TRANSFERS_SYNTHETIC"
CTGAN_EPOCHS = 300

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
GRAPH_OWNER = "YOUR_USER"
ACCOUNT_TABLE = "BANK_ACCOUNTS"
TRANSFER_TABLE = "BANK_TRANSFERS"


def identifier(value: str) -> str:
    """Allow only simple Oracle identifiers configured in this script."""
    value = value.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9_$#]{0,127}", value):
        raise ValueError(f"Unsafe Oracle identifier: {value!r}")
    return value


def read_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)["oracle"]


def connect(config: dict) -> oracledb.Connection:
    password = os.environ.get(config["password_env"])
    if not password:
        raise RuntimeError(
            f"Set the environment variable {config['password_env']} before running this script."
        )

    wallet_dir = config["wallet_dir"]
    if config.get("connection_mode", "thin").lower() == "thick":
        # In Thick mode the Oracle Client must be told where tnsnames.ora is.
        oracledb.init_oracle_client(config_dir=wallet_dir)

    return oracledb.connect(
        user=config["user"],
        password=password,
        dsn=config["dsn"],
        config_dir=config.get("config_dir") or wallet_dir,
        wallet_location=wallet_dir,
    )


def fetch_dataframe(cursor: oracledb.Cursor, sql: str) -> pd.DataFrame:
    cursor.execute(sql)
    columns = [column[0] for column in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def table_exists(cursor: oracledb.Cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name",
        table_name=table_name,
    )
    return cursor.fetchone()[0] > 0


def make_synthetic_transfers(
    transfers: pd.DataFrame, valid_account_ids: set[int]
) -> pd.DataFrame:
    training_data = transfers[["SRC_ACCT_ID", "DST_ACCT_ID", "AMOUNT"]].copy()
    training_data["SRC_ACCT_ID"] = training_data["SRC_ACCT_ID"].astype(str)
    training_data["DST_ACCT_ID"] = training_data["DST_ACCT_ID"].astype(str)
    training_data["AMOUNT"] = pd.to_numeric(training_data["AMOUNT"])

    model = CTGAN(epochs=CTGAN_EPOCHS, verbose=True)
    # Avoid Windows process workers, which re-import Torch and fail to load c10.dll.
    with parallel_config(backend="threading", n_jobs=1):
        model.fit(training_data, discrete_columns=["SRC_ACCT_ID", "DST_ACCT_ID"])

    accepted_batches: list[pd.DataFrame] = []
    accepted_rows = 0
    for _ in range(10):
        # Generate a little extra in case invalid/non-positive values are rejected.
        requested_rows = max(SYNTHETIC_ROWS - accepted_rows, 1) * 2
        generated = model.sample(requested_rows)
        generated["SRC_ACCT_ID"] = pd.to_numeric(generated["SRC_ACCT_ID"], errors="coerce")
        generated["DST_ACCT_ID"] = pd.to_numeric(generated["DST_ACCT_ID"], errors="coerce")
        generated["AMOUNT"] = pd.to_numeric(generated["AMOUNT"], errors="coerce")
        generated = generated.dropna()
        generated["SRC_ACCT_ID"] = generated["SRC_ACCT_ID"].round().astype("int64")
        generated["DST_ACCT_ID"] = generated["DST_ACCT_ID"].round().astype("int64")
        generated["AMOUNT"] = generated["AMOUNT"].clip(lower=0.01).round(2)
        generated = generated[
            generated["SRC_ACCT_ID"].isin(valid_account_ids)
            & generated["DST_ACCT_ID"].isin(valid_account_ids)
        ]
        accepted_batches.append(generated)
        accepted_rows += len(generated)
        if accepted_rows >= SYNTHETIC_ROWS:
            break

    synthetic = pd.concat(accepted_batches, ignore_index=True).head(SYNTHETIC_ROWS)
    if len(synthetic) != SYNTHETIC_ROWS:
        raise RuntimeError(
            f"Only generated {len(synthetic)} valid transfers; expected {SYNTHETIC_ROWS}."
        )

    next_txn_id = int(transfers["TXN_ID"].max()) + 1
    synthetic.insert(0, "TXN_ID", range(next_txn_id, next_txn_id + SYNTHETIC_ROWS))
    return synthetic[["TXN_ID", "SRC_ACCT_ID", "DST_ACCT_ID", "AMOUNT"]]


def create_output_table(cursor: oracledb.Cursor) -> None:
    output = identifier(OUTPUT_TABLE)
    owner = identifier(GRAPH_OWNER)
    accounts = identifier(ACCOUNT_TABLE)
    cursor.execute(
        f"""
        CREATE TABLE {output} (
            TXN_ID       NUMBER       NOT NULL,
            SRC_ACCT_ID  NUMBER       NOT NULL,
            DST_ACCT_ID  NUMBER       NOT NULL,
            AMOUNT       NUMBER(18,2) NOT NULL,
            CONSTRAINT BTSYNTH_PK PRIMARY KEY (TXN_ID),
            CONSTRAINT BTSYNTH_SRC_FK FOREIGN KEY (SRC_ACCT_ID)
                REFERENCES {owner}.{accounts}(ID),
            CONSTRAINT BTSYNTH_DST_FK FOREIGN KEY (DST_ACCT_ID)
                REFERENCES {owner}.{accounts}(ID)
        )
        """
    )


def main() -> None:
    config = read_config()
    owner = identifier(GRAPH_OWNER)
    accounts = identifier(ACCOUNT_TABLE)
    transfers = identifier(TRANSFER_TABLE)
    output = identifier(OUTPUT_TABLE)

    with connect(config) as connection:
        with connection.cursor() as cursor:
            # Read-only source queries.
            account_df = fetch_dataframe(cursor, f"SELECT ID FROM {owner}.{accounts}")
            transfer_df = fetch_dataframe(
                cursor,
                f"""
                SELECT TXN_ID, SRC_ACCT_ID, DST_ACCT_ID, AMOUNT
                FROM {owner}.{transfers}
                """,
            )

            if transfer_df.empty:
                raise RuntimeError("BANK_TRANSFERS has no rows to train CTGAN.")
            if table_exists(cursor, output):
                raise RuntimeError(
                    f"{output} already exists. The script will not overwrite or truncate it. "
                    "Choose a new OUTPUT_TABLE name if you want another run."
                )

            valid_account_ids = set(pd.to_numeric(account_df["ID"]).astype(int))
            synthetic = make_synthetic_transfers(transfer_df, valid_account_ids)

            # Final relationship validation before any new table is created.
            if not (
                synthetic["SRC_ACCT_ID"].isin(valid_account_ids).all()
                and synthetic["DST_ACCT_ID"].isin(valid_account_ids).all()
                and synthetic["TXN_ID"].is_unique
            ):
                raise RuntimeError("Synthetic-data validation failed; no table was created.")

            create_output_table(cursor)
            cursor.executemany(
                f"""
                INSERT INTO {output} (TXN_ID, SRC_ACCT_ID, DST_ACCT_ID, AMOUNT)
                VALUES (:1, :2, :3, :4)
                """,
                list(synthetic.itertuples(index=False, name=None)),
            )
            connection.commit()

    print(f"Created {OUTPUT_TABLE} with {SYNTHETIC_ROWS:,} validated synthetic transfers.")
    print("BANK_ACCOUNTS and BANK_TRANSFERS were read only and were not changed.")


if __name__ == "__main__":
    main()
