# Third-Party Detection Content Policy

This repository can convert third-party detection query languages into OCI Log
Analytics QL, but it must not become an unreviewed mirror of third-party rule
content.

## Elastic Detection Rules

Elastic's public `elastic/detection-rules` repository states that its rules,
code, and related content are licensed under Elastic License v2. The project may
use that repository as an interoperability reference and may analyze a local
checkout to produce aggregate compatibility metrics.

Do not commit copied Elastic rule bodies, rule names, descriptions, notes,
investigation guides, TOML files, hunting queries, EQL, ES|QL, Kuery, Lucene, or
derived converted Logan QL from Elastic source content unless legal approval has
explicitly cleared the import and notice requirements.

Allowed without additional approval:

- Aggregate counts by rule type, language, operator marker, or field name.
- Self-authored synthetic examples that demonstrate language syntax.
- Converter support for user-pasted Elastic TOML or query snippets.
- References to the upstream repository URL and license name.

Not allowed without approval:

- Vendoring `elastic/detection-rules` files or generated exports.
- Committing Elastic rule text, query text, descriptions, notes, or rule IDs.
- Promoting converted Elastic rules into `queries/**` as project detection
  content.
- Training examples that are copied from Elastic rule or hunting TOML.

## Converter Behavior

Backend converters should return metadata that identifies source language,
support level, warnings, and dependency requirements. For third-party inputs,
they should not persist source content. Generated repository artifacts should
store only capability summaries and self-authored examples.

## Review Checklist

Before committing work that mentions third-party detection repositories:

1. Confirm generated JSON does not contain third-party rule bodies or queries.
2. Confirm examples are synthetic and self-authored.
3. Confirm license names and source URLs are retained in docs or metadata.
4. Run the sensitive-value scan and the third-party artifact tests.
