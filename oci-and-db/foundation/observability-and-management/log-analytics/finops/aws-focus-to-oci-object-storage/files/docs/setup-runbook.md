# Setup Runbook

## 1. Prerequisites

- AWS permissions to manage Billing and Cost Management Data Exports
- AWS permissions for the Lambda execution role to read S3 and write audit logs
- AWS permission to create and manage EventBridge schedules
- OCI PAR URL with write access to the target bucket
- OCI Object Storage bucket

## 2. AWS Data Export

Use the AWS console:

```text
AWS Console -> Billing and Cost Management -> Data Exports
```

Configure or verify:

- Export type: AWS Billing and Cost Management Data Export
- Specification: FOCUS 1.2 with AWS columns
- Granularity: Daily
- File format: `text/csv`
- Compression: `Gzip`
- Behavior: create new daily files instead of overwriting previous files
- S3 destination path: `s3://aws-oci-focus-daily/Dataexport/AWSDataExportDailyFocus/data/`

## 3. Lambda function

Recommended function name:

```text
s3-to-oci-focus-daily-flat-transfer
```

Use the code in `src/lambda_function_focus_daily_flat_transfer.py`.

Recommended runtime settings:

- Python 3.x
- Timeout: 15 minutes
- Memory: 1024 MB
- Ephemeral storage: 1024 MB

## 4. Environment variables

Copy the values from `examples/lambda-env-vars.example`.

Important behavior:

- `DEST_PREFIX` is left blank so OCI does not create folder-like structure.
- `LOOKBACK_HOURS` is used because no DynamoDB / external state store is used.
- `PROCESS_ALL=false` is recommended for scheduled runs.
- `PROCESS_ALL=true` should be used only for backfill or testing.

## 5. OCI destination

The OCI base URL must use the PAR token format:

```text
https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/<PAR_TOKEN>/n/<namespace>/b/<bucket>/o
```

Do not store the real PAR token in source control.

## 6. Scheduling

Use EventBridge Scheduler to run the Lambda daily.

Example cron:

```text
cron(0 8 * * ? *)
```

Example payload:

```json
{
  "trigger": "eventbridge_daily_scan",
  "lookback_hours": 24,
  "process_all": false
}
```

## 7. Logging

- CloudWatch log group: `/aws/lambda/s3-to-oci-focus-daily-flat-transfer`
- S3 audit log prefix: `s3://aws-oci-focus-daily/transfer-logs/`
- Monthly log example: `focus-transfer-log-2026-06.jsonl`
