# AWS FOCUS 1.2 Daily Export to OCI Object Storage

This repository contains a reusable reference implementation for moving AWS FOCUS 1.2 daily billing export files from Amazon S3 into OCI Object Storage using AWS Lambda and EventBridge Scheduler.

The solution is designed for internal review and reuse. It includes:

- AWS Data Export setup notes
- Lambda code
- Environment variable examples
- IAM policy examples
- EventBridge payload examples
- Logging and audit guidance
- Troubleshooting notes
- Sanitized screenshots / diagrams can be added later if needed

## High-level flow

AWS Billing and Cost Management Data Export -> Amazon S3 -> AWS Lambda -> OCI Object Storage

CloudWatch Logs capture runtime logs, and the Lambda also writes a monthly JSONL audit log back to S3.

## Repository layout

```text
aws-focus-to-oci-object-storage/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── setup-runbook.md
│   └── troubleshooting.md
├── examples/
│   ├── eventbridge-payload.json
│   ├── iam-policy.json
│   └── lambda-env-vars.example
└── src/
    └── lambda_function_focus_daily_flat_transfer.py
```

## What this solution does

- Reads AWS FOCUS 1.2 daily `.csv.gz` files from S3.
- Uses a configurable lookback window to identify recently modified files.
- Flattens the S3 path into a single OCI object name so OCI does not create nested folder structure.
- Uploads the file to OCI Object Storage using a pre-authenticated request (PAR) URL.
- Writes structured execution logs to CloudWatch.
- Appends a monthly transfer audit log into an S3 `transfer-logs/` prefix.

## Notes for internal review

Before sharing more broadly, confirm the applicable Oracle review path with the PM / OGHO / Legal / CorpArch teams. Sanitize all secrets, tokens, customer names, private account IDs, and screenshots before publishing.

## Quick start

1. Copy `examples/lambda-env-vars.example` into Lambda environment variables.
2. Deploy `src/lambda_function_focus_daily_flat_transfer.py` as the Lambda handler.
3. Create an EventBridge schedule to run the Lambda daily.
4. Verify CloudWatch logs and the S3 audit log file.
5. Confirm OCI receives flat file names at the bucket root (or with a blank destination prefix).

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
