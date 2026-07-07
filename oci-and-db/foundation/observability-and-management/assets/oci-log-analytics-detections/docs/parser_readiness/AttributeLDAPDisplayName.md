# Parser Readiness: AttributeLDAPDisplayName

**Status:** pending parser extraction
**Phase:** 9

`AttributeLDAPDisplayName` is present in directory-service EventData and needs parser extraction before it can be used safely. The shard maps it to the real `Object Type` field and marks it `parser_change_required: true`.

Required next step: add EventData parser extraction for `AttributeLDAPDisplayName`, refresh the field dictionary, and validate with synthetic and live OCI evidence.

