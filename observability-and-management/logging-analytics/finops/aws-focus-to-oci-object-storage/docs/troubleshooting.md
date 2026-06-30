# Troubleshooting

## AccessDenied for `s3:ListBucket`

**Cause:** The Lambda execution role does not have permission to list the S3 bucket or prefixes.

**Fix:** Add `s3:ListBucket` to the Lambda role for:

- `arn:aws:s3:::aws-oci-focus-daily`
- `Dataexport/AWSDataExportDailyFocus/data/`
- `transfer-logs/`

## Wrong `SOURCE_PREFIX`

**Cause:** The Lambda is pointing at an older export path.

**Fix:** Use the current daily export path:

```text
Dataexport/AWSDataExportDailyFocus/data/
```

## OCI shows folders

**Cause:** The OCI object name contains `/` characters.

**Fix:** Keep `DEST_PREFIX` blank and flatten the source path into a single object name.

## Files are overwritten in OCI

**Cause:** The same destination object name is reused.

**Fix:** Keep the unique hash suffix in the output filename.

## No files are picked up

**Cause:** The lookback window is too small, or the export has not delivered files yet.

**Fix:** Increase `LOOKBACK_HOURS` temporarily or run with `PROCESS_ALL=true` for a one-time test/backfill.

## OCI upload fails

**Cause:** The PAR URL is expired, incorrect, or does not allow writes.

**Fix:** Regenerate the OCI PAR URL with write access and update the Lambda environment variable.
