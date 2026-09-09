create or replace package body utl_json_cloud
is
	function is_autonomous return boolean
	is
		num_of_rows number(1);
	begin
		select count(*)
		into   num_of_rows
		from dba_pdbs
		where cloud_identity like '%AUTONOMOUS%';
		
		if num_of_rows > 0 then
			return true;
		end if;
		return false;
	end;
	
	procedure create_credential(p_credential_name varchar2,
	                            p_username        varchar2,
	                            p_password        varchar2)
	is
	begin
		if is_autonomous then
			dbms_cloud.create_credential(credential_name => p_credential_name,
                                      username           => p_username,
                                      password           => p_password);
		else
			dbms_credential.create_credential(credential_name => p_credential_name,
                                      		  username        => p_username,
                                      		  password        => p_password);                                     
		end if;
	end;
	
    procedure drop_credential(p_credential_name varchar2)
    is
    begin
    	if is_autonomous then
    		dbms_cloud.drop_credential(credential_name => p_credential_name);
    	else
    		dbms_credential.drop_credential(credential_name => p_credential_name);
    	end if;
    end;
    
	procedure create_or_replace_credential(p_credential_name varchar2,
   	                                       p_username        varchar2,
	                                       p_password        varchar2)
    is
    begin
       begin
       	  drop_credential(p_credential_name);
       exception
          when e_non_existing_credential then
          	null;
       end;
       create_credential(p_credential_name,p_username,p_password);
    end;
    
    procedure create_external_json_collection(p_collection_name varchar2,
                                              p_credential_name varchar2,
                                              p_file_list       clob)
	is
	begin
       dbms_cloud.create_external_table(table_name      => p_collection_name||'_ext',
                                        credential_name => p_credential_name,
                                        file_uri_list   => p_file_list,
                                        format          => json_object('type' value 'jsondoc'));
       execute immediate 'create or replace json collection view '||p_collection_name||' as select DATA from '||p_collection_name||'_ext';
    end;
    
    procedure drop_external_json_collection(p_collection_name varchar2)
    is
    begin
    	execute immediate 'drop view '||p_collection_name;
    	execute immediate 'drop table '||p_collection_name||'_ext';
    end;    	
   
end;
/
