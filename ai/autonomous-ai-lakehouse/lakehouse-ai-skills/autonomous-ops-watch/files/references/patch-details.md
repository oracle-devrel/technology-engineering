# Patch Details

Use this reference only when the user asks about patch contents, bug fixes, patch versions, components affected by a patch, or whether a specific bug was fixed.

## Source

Primary source: `DBA_CLOUD_PATCH_INFO`

Official docs:
- Autonomous maintenance and patching: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/maintenance-windows-patching.html

## Behavior

- Do not include full patch details in the default ops summary.
- In summaries, show patch ids from `DB_NOTIFICATIONS` only.
- Query `DBA_CLOUD_PATCH_INFO` only when the user explicitly asks for details.
- Do not treat this view as complete release notes. It may contain customer bug fix information, not every internal change.
- If the query fails due to privileges, say that patch details are not visible to the connected user.

## Query patterns

Patch version details:

```sql
select bug_num,
       bug_title,
       component_name,
       patch_version
from dba_cloud_patch_info
where patch_version = :patch_version
order by component_name, bug_num;
```

Find a bug:

```sql
select bug_num,
       bug_title,
       component_name,
       patch_version
from dba_cloud_patch_info
where bug_num = :bug_num
order by patch_version desc;
```

Patch versions visible:

```sql
select patch_version,
       count(*) as visible_bug_fix_count
from dba_cloud_patch_info
group by patch_version
order by patch_version desc;
```
