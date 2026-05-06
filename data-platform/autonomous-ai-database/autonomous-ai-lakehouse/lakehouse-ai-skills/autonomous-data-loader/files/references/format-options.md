# Format options

Use this reference when building the `format => json_object(...)` argument for `DBMS_CLOUD.COPY_DATA` or `DBMS_CLOUD.COPY_COLLECTION`.

## Contents

- General rules
- CSV baseline
- CSV embedded newlines
- JSON for COPY_DATA
- JSON or EJSON for COPY_COLLECTION
- Parquet
- ORC
- Avro
- XML caution
- Troubleshooting-driven adjustments

## General rules

- Keep format options minimal unless the user has a specific issue.
- Include `enablelogs => true` and a deliberate `logretention` value for troubleshooting-friendly workflows.
- Match the format type to the selected files. Do not mix formats in one load operation.
- Use official Oracle documentation for exact option availability and restrictions in the user's database version.

## CSV baseline

```sql
format => json_object(
  'type' value 'csv',
  'skipheaders' value 1,
  'delimiter' value ',',
  'quote' value '"',
  'blankasnull' value 'true',
  'rejectlimit' value 100,
  'enablelogs' value 'true',
  'logretention' value 7
)
```

Common CSV adjustments:

- `delimiter`: set comma, pipe, tab, semicolon, or HEX value for special delimiters.
- `quote` and `endquote`: set when fields are quoted.
- `skipheaders`: skip header lines.
- `ignoreblanklines`: ignore blank lines when supported for the format.
- `blankasnull`: treat blank fields as null.
- `dateformat` and `timestampformat`: use explicit formats when date parsing fails.
- `conversionerrors`: consider `store_null` only when losing invalid values is acceptable.
- `truncatecol`: use only when truncation is acceptable and documented.
- `rejectlimit`: set an intentional threshold.
- `detectfieldorder`: use only for clean header-based mapping against existing target columns.
- `regexuri`: use when the URI contains regular expression patterns.
- `compression`: use `auto` or a specific supported compression when files are compressed.
- `encryption`: use only when files require documented decryption options.

## CSV embedded newlines

When CSV data may contain embedded newlines in quoted fields, use the documented CSV option for embedded record handling in the user's database version. Be explicit about the risk: record delimiters and quote handling must be correct.

## JSON for COPY_DATA

Use when loading JSON into an existing relational table.

```sql
format => json_object(
  'type' value 'json',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

If mapping JSON fields to relational columns, use documented JSON options such as `columnpath` where applicable.

## JSON or EJSON for COPY_COLLECTION

Use `json` for normal JSON document loading. Use `ejson` only when extended scalar values are needed.

```sql
format => json_object(
  'type' value 'json',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

## Parquet

```sql
format => json_object(
  'type' value 'parquet',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

Parquet has embedded metadata. Still verify the target table columns before `COPY_DATA`.

## ORC

```sql
format => json_object(
  'type' value 'orc',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

ORC has embedded metadata. Still verify target table compatibility.

## Avro

```sql
format => json_object(
  'type' value 'avro',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

Avro has embedded metadata. Still verify target table compatibility.

## XML caution

Treat XML as version-specific. Do not generate XML `COPY_DATA` workflows unless the user's Autonomous documentation explicitly confirms the supported load pattern and the expected relational mapping.

## Troubleshooting-driven adjustments

When a load fails, do not randomly add options. Inspect log and badfile tables first, then suggest targeted changes:

- date errors: add explicit `dateformat` or `timestampformat`.
- extra/missing fields: review delimiter, quote, `ignoremissingcolumns`, `detectfieldorder`, or column mapping.
- values too long: profile lengths before suggesting `truncatecol`.
- numeric conversion errors: confirm decimal/group separators and target column type.
- unreadable compressed file: set correct `compression`.
