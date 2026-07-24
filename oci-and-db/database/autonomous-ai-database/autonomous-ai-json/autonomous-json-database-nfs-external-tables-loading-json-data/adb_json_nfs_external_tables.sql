-- demonstration of how to load and query JSON data into an Autonomous Database using NFS share and external table API
-- requirements
-- OCI FSS NFS mount target with exported volume and assigned hostname (attaching the nfs volume in ADB accepts only hostnames and not IP addresses)
-- EMPLOYEES_COL.json file stored in this volume: it can be downloaded from the following URL 
--     https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/fro8fl9kuqli/b/HR_SAMPLE_DATA/o/EMPLOYEES_COL.json

drop table if exists employees_col;

drop directory if exists hr_sample_data_dir;

create directory hr_sample_data_dir as 'hr_sample_data_dir';

begin
    dbms_cloud_admin.attach_file_system(
	file_system_name => 'hr_sample_data_fs',
	file_system_location => '<fqdn_of_the_mount_target>:/<file_system_name>',
	directory_name => 'hr_sample_data_dir');
end;
/	

select file_system_name, file_system_location, directory_path 
from dba_cloud_file_systems;

select object_name 
from dbms_cloud.list_files('hr_sample_data_dir');

begin
    dbms_cloud.create_external_table(
    table_name =>'employees_json_ext',
    format => json_object('type' value 'jsondoc'),
    file_uri_list =>'hr_sample_data_dir:EMPLOYEES_COL.json');
end;
/

begin
   dbms_cloud.validate_external_table(
   table_name => 'employees_json_ext');
end;
/

select *
from employees_json_ext;

create json collection table employees_col;

insert into employees_col(data)
select data
from employees_json_ext;

commit;

select *
from employees_col;

create or replace json collection view employees_col_view
as
select data
from employees_json_ext;

drop table if exists employees_json_ext_2;

create table employees_json_ext_2
(data json);

declare 
   job_id number(10);
begin
   dbms_cloud.copy_data(
       table_name => 'employees_json_ext_2',
       file_uri_list =>'hr_sample_data_dir:EMPLOYEES_COL.json');
end;
/

select *
from employees_json_ext_2;	
	