# Parser Readiness: ObjectDN

**Status:** pending parser extraction
**Phase:** 9

`ObjectDN` appears inside Windows directory-service EventData payloads. The shard maps it to the real `Target Object` display field but marks it `parser_change_required: true`; converter attempts should skip with `parser_readiness:pending:ObjectDN` until the parser extracts this value from EventData.

Required next step: add a synthetic Windows directory-service fixture containing `ObjectDN`, update the SOC parser contract, refresh `queries/log_source_field_dictionary.json`, and validate against OCI Log Analytics.

