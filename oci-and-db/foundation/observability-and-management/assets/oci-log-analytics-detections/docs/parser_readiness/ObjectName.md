# Parser Readiness: ObjectName

**Status:** pending parser extraction
**Phase:** 9

`ObjectName` is another EventData-derived object field. The shard maps it to the real `Target Object` display field and marks it `parser_change_required: true` to prevent silent use before parser extraction exists.

Required next step: add parser extraction and synthetic fixture coverage for EventData `ObjectName`, then live-validate a candidate that uses the field before clearing the pending flag.

