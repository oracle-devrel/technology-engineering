REM Script for 23c: 5-monitor-with-user-annotations-usage.sql
REM Use USER_ANNOTATIONS_USAGE to track the list of annotations and their usage across your schema objects

-- If the annotation is specified for a table column, view column, or domain column, the name of the column, filter on the column name otherwise on NULL
-- in our case to obtain object-level annotations for table, index, domain and view, we filter on NULL

set lines 200
set pages 200
col object_name format a25
col object_type format a15
col annotation_name format a15
col annotation_value format a25
col column_name format a20

select object_name, object_type, annotation_name, annotation_value 
from user_annotations_usage
where column_name is null order by 2,1;
