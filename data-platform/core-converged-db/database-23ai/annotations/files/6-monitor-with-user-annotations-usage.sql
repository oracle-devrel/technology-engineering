REM Script for 23c: 6-monitor-with-user-annotations-usage.sql
REM Use USER_ANNOTATIONS_USAGE to track the list of annotations and their usage across your schema objects

-- Obtain column-level annotations

set lines 200
set pages 200
col object_name format a25
col object_type format a15
col annotation_name format a15
col annotation_value format a25
col column_name format a20

select object_name, object_type, column_name, annotation_name, annotation_value 
from user_annotations_usage
where column_name is not null order by 2,1;

-- Display annotations as a single JSON collection per column
select object_type, object_name, column_Name, JSON_ARRAYAGG(JSON_OBJECT(Annotation_Name, Annotation_Value)) in_jsonformat 
from user_annotations_usage
where column_name is not null group by object_type, object_name, column_name;
