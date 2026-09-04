# Oracle Database connection configuration

The script reads `config.json` from the same folder. Keep database passwords out
of this file: set the password in the environment variable named by
`password_env`.

## Autonomous Database (ADB) with a wallet

Unzip the ADB wallet locally. Use the wallet folder path and a TNS alias from
the wallet's `tnsnames.ora` file, such as `myadb_high`.

```json
{
  "oracle": {
    "user": "YOUR_USER",
    "password_env": "DB_PASSWORD",
    "dsn": "myadb_high",
    "wallet_dir": "C:\\path\\to\\Wallet_myadb",
    "config_dir": "",
    "connection_mode": "thin"
  }
}
```

## On-premises or local Oracle Database (no wallet)

Use this configuration for a direct database connection without an ADB wallet:

```json
{
  "oracle": {
    "user": "YOUR_USER",
    "password_env": "DB_PASSWORD",
    "dsn": "localhost:1521/FREEPDB1"
  }
}

Replace `localhost:1521/FREEPDB1` with your own host, listener port, and
service name when the database is not local.

Rectifying the Python code is required for the on-premises, no-wallet configuration.

## Set the password and run the script

In PowerShell, set the password only for the current session:

```powershell
$env:DB_PASSWORD = "your-database-password"
python ctgan_augment_bank_transfers.py
```

Do not commit a real password, wallet, `tnsnames.ora`, or generated bank data to
GitHub.
