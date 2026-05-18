-- required credential creation
begin
	utl_json_cloud.create_or_replace_credential(p_credential_name => 'JSON_DEMO_CREDENTIAL',
	                                            p_username        => 'username',
	                                            p_password        => 'authentication_token');
end;
/


-- "external json collection" i.e. pair of external table pointing to some json data and json collection view on top of this
begin
	utl_json_cloud.create_external_json_collection(p_collection_name => 'iot_events_external',
	                                               p_credential_name => 'JSON_DEMO_CREDENTIAL',
	                                               p_file_list       => 'bucket_url/dir*/*.json');
end;
/

select *
from iot_events_external;

select *
from iot_events_external_ext;

select *
from iot_events;

drop table if exists iot_events_part;


-- json collection partitioned table
create json collection table iot_events_part
partition by range (json_value(DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR)) 
interval (numtodsinterval(1,'DAY'))
( 
	partition p_before_2025 values less than (DATE '2025-01-01')
);

-- loading data from "external json collection"
insert /*+ append parallel(16) */ into iot_events_part
select *
from iot_events_external;

 select * from iot_events_part iot
 WHERE json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) >= DATE '2025-01-30'
   AND json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) <  DATE '2025-01-31';
   
select partition_name, high_value 
from user_tab_partitions where table_name = 'IOT_EVENTS_PART';

declare
  part_URL VARCHAR2(4000);
begin
  part_URL := 'bucket_url/year=2025/month=01';
  dbms_cloud.export_data(
    credential_name => 'JSON_DEMO_CREDENTIAL',
    file_uri_list    => part_URL || '/day=01/2025-01-01_events.json',
    query            => q'[
                            select  
                                  DATA
                                  FROM iot_events_part c
                              WHERE json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) >= DATE '2025-01-01'
                                AND json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) <  DATE '2025-01-02'
                          ]',
   format          => json_object('type' VALUE 'json')
  );
end;
/

-- data export 

declare
  part_URL VARCHAR2(4000);
begin
  part_URL := '  part_URL := 'bucket_url/year=2025/month=01';
  dbms_cloud.export_data(
    credential_name => 'JSON_DEMO_CREDENTIAL',
    file_uri_list    => part_URL || '/day=02/2025-01-02_events.json',
    query            => q'[
                            select  
                                  DATA
                                  FROM iot_events_part iot
                              WHERE json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) >= DATE '2025-01-02'
                                AND json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) <  DATE '2025-01-03'
                          ]',
   format          => json_object('type' VALUE 'json')
  );
end;
/

declare
  part_URL VARCHAR2(4000);
begin
  part_URL :=   part_URL := 'bucket_url/year=2025/month=01';
  dbms_cloud.export_data(
    credential_name => 'JSON_DEMO_CREDENTIAL',
    file_uri_list    => part_URL || '/day=03/2025-01-03_events.json',
    query            => q'[
                            select  
                                  DATA
                                  FROM iot_events_part iot
                              WHERE json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) >= DATE '2025-01-03'
                                AND json_value(iot.DATA, '$.eventDate' RETURNING DATE ERROR ON ERROR) <  DATE '2025-01-04'
                          ]',
   format          => json_object('type' VALUE 'json')
  );
end;
/

-- cold data "external json collection view" creation
begin
	utl_json_cloud.create_external_json_collection(p_collection_name => 'iot_events_cold_data',
	                                               p_credential_name => 'JSON_DEMO_CREDENTIAL',
	                                               p_file_list       => 'bucket_url/year*/month*/day*/*.json');
end;
/

select *
from iot_events_cold_data;

-- old data removal
alter table iot_events_part
drop partition for (DATE '2025-01-01')
update indexes;

alter table iot_events_part
drop partition for (DATE '2025-01-02')
update indexes;

alter table iot_events_part
drop partition for (DATE '2025-01-03')
update indexes;

-- create a view on top of "external" and "internal" json collections
create or replace json collection view iot_events
as
select *
from iot_events_part
union all
select *
from iot_events_cold_data;

select *
from iot_events;



