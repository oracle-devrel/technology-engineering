# Oracle ADB Python Fetch Size Testcase

Small testcase for measuring the impact of `python-oracledb` `cursor.arraysize`
when fetching large result sets from **Oracle Autonomous Database Serverless**.

The testcase uses:

- `python-oracledb` in **Thin mode**
- Autonomous Database **mTLS wallet**
- A single generated table: `FETCH_SIZE_DEMO`
- A default test volume of **50,000 rows**

## Why this exists

When an application retrieves many rows, fetching too few rows per round-trip can
hurt throughput. In Python, the main setting to test is:

```python
cursor.arraysize = 1000
```

This script lets you test the performance of different `arraysize` values against the same
query and compare elapsed fetch times.

## Repository contents

```text
.
├── adb_fetch_size_demo.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Python 3.9 or later
- Access to an Oracle Autonomous Database Serverless instance
- A downloaded Autonomous Database wallet
- A database user that can create/drop a test table
- Network access from your client machine to ADB

Install dependencies:

```bash
python3 -m pip install --user -r requirements.txt
```

If `pip` is missing:

```bash
sudo dnf install -y python3-pip
```

or on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-pip
```

## Wallet requirements

For Thin mode with an Autonomous Database mTLS wallet, the wallet directory must
contain at least:

```text
tnsnames.ora
ewallet.pem
```

Example:

```bash
unzip Wallet_MYADB.zip -d /home/opc/Wallet_MYADB
ls -l /home/opc/Wallet_MYADB/tnsnames.ora /home/opc/Wallet_MYADB/ewallet.pem
```

## Configuration

You can configure the script with environment variables:

```bash
export ADB_USER='AITEST'
export ADB_PASSWORD='your_database_password'
export ADB_WALLET_PASSWORD='your_wallet_password'
export ADB_WALLET_DIR='/home/opc/Wallet_MYADB'
export ADB_DSN='myadb_tpurgent'
```

`ADB_DSN` must be one of the aliases found in the wallet's `tnsnames.ora`, for
example:

```text
myadb_high
myadb_medium
myadb_low
myadb_tp
myadb_tpurgent
```

To list aliases:

```bash
grep -i "^[a-z0-9_].*=" "$ADB_WALLET_DIR/tnsnames.ora"
```

You can also use command-line arguments instead of environment variables.

## Run the default test

```bash
python3 adb_fetch_size_demo.py
```

Default behavior:

- Drops table `FETCH_SIZE_DEMO` if it exists
- Recreates it
- Inserts **50,000 rows**
- Fetches all rows repeatedly using these `arraysize` values:

```text
1,10,50,100,500,1000,5000,10000
```

Example output:

```text
Connected to Autonomous Database Serverless using python-oracledb Thin mode
Created FETCH_SIZE_DEMO with 50,000 rows

arraysize | rows fetched | avg seconds | runs
----------+--------------+-------------+----------------
        1 |       50,000 |      10.842 | 10.901, 10.790, 10.835
       10 |       50,000 |       1.748 | 1.731, 1.762, 1.751
      100 |       50,000 |       0.401 | 0.399, 0.405, 0.398
     1000 |       50,000 |       0.242 | 0.240, 0.245, 0.241
     5000 |       50,000 |       0.238 | 0.239, 0.236, 0.240
    10000 |       50,000 |       0.251 | 0.250, 0.252, 0.251
```

Your results will vary depending on client CPU, network latency, row width,
database load, service name, and cache effects.

## Run with custom arraysize values

```bash
python3 adb_fetch_size_demo.py \
  --arraysizes 100,500,1000,2000,5000 \
  --repeats 5
```

## Run with a different row count

```bash
python3 adb_fetch_size_demo.py --rows 100000
```

## Reuse an existing populated demo table

After the first run, you can avoid dropping/reloading the table:

```bash
python3 adb_fetch_size_demo.py --skip-setup
```

## Print connection diagnostics

This prints non-secret configuration values before connecting:

```bash
python3 adb_fetch_size_demo.py --debug
```

It does not print passwords.

## Safety note

The script drops and recreates this table by default:

```text
FETCH_SIZE_DEMO
```

Run it only in a test schema where this table name is safe to use.

## Thin mode connection pattern

The testcase connects like this:

```python
conn = oracledb.connect(
    user=args.user,
    password=db_password,
    dsn=args.dsn,
    config_dir=args.wallet_dir,
    wallet_location=args.wallet_dir,
    wallet_password=wallet_password,
)
```

Make sure the wallet password is correct. A wrong wallet password can produce
connection failures even when tools such as SQLcl connect successfully using the
same wallet directory and TNS alias.
