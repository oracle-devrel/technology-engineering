# Architecture

```text
AWS FOCUS Data Export
        |
        v
Amazon S3 (daily .csv.gz files)
        |
        v
AWS Lambda (scan, flatten, upload)
        |
        +----------------------+
        |                      |
        v                      v
OCI Object Storage       CloudWatch Logs
        |
        v
Monthly S3 audit log (transfer-logs/)
```

## Core entities

- AWS Data Export job
- S3 bucket: `aws-oci-focus-daily`
- S3 source prefix: `Dataexport/AWSDataExportDailyFocus/data/`
- Lambda function: `s3-to-oci-focus-daily-flat-transfer`
- EventBridge Scheduler
- OCI bucket: `LabBucket`
- CloudWatch log group: `/aws/lambda/s3-to-oci-focus-daily-flat-transfer`
- S3 audit log prefix: `transfer-logs/`
