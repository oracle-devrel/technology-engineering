drop table if exists JSONFLIGHTS_COL_LARGE;
create json collection table JSONFLIGHTS_COL_LARGE;

begin
dbms_cloud.copy_collection(collection_name => 'JSONFLIGHTS_COL_LARGE', 
                           credential_name => 'ajd_cred', 
                           file_uri_list   => 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/fro8fl9kuqli/b/json_demo/o/flights-150m.json', 
                           format => json_object('recorddelimiter' value '''\n'''));
end;
/

drop table if exists jsonflights_col_19c;
create table jsonflights_col_19c
(id          varchar2(32) primary key,
 data        clob);

insert /*+parallel append */ into jsonflights_col_19c(id, data)
select j.data."_id", j.data
from jsonflights_col_large j
where rownum <= 1000000;

commit;

alter table jsonflights_col_19c add (constraint ensure_json check(doc is json));



-- migration from clob to json datatype
 drop table if exists jsonflights_col_23ai;
 create json collection table jsonflights_col_23ai;

 begin 
    dbms_json.json_type_convertible_check(
                   owner => 'ORADEV',
                   tableName => 'JSONFLIGHTS_COL_19C',
                   columnName => 'DATA',
                   statusTableName => 'CHECK_TABLE');
 end;

 select * from check_table;

 insert /*+ parallel append */
 into jsonflights_col_23ai (data)
 select json(data)
 from jsonflights_col_19c;

 commit;

 begin
    dbms_stats.gather_table_stats('ORADEV','JSONFLIGHTS_COL_19C');
    dbms_stats.gather_table_stats('ORADEV','JSONFLIGHTS_COL_23AI');
 end;

 select *
 from user_tables
 where table_name in ('JSONFLIGHTS_COL_19C','JSONFLIGHTS_COL_23AI');


select json_serialize(data pretty) as data from jsonflights_col_23ai;

select json_serialize(data pretty) as data from jsonflights_col_19c;

select json_serialize(data pretty) as data from jsonflights_col_23ai j
where j.data."DEP_DELAY" > 12

select json_serialize(data pretty) as data from jsonflights_col_19c j
where j.data."DEP_DELAY" > 12
