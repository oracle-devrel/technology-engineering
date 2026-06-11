# Example: Table Access Stats

## User prompt

Which tables are being scanned the most?

## Expected response style

Source: `ALL_TABLE_ACCESS_STATS` or another available table access stats view.

Summarize the top 20 objects by read count. Explain that the counts are accumulated since instance startup, not over a selected time window.

Do not run this in the default ops summary because it can be noisy on systems with many tables.
