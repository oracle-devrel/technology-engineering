create or replace package utl_json_cloud
is
	e_non_existing_credential exception;
	pragma exception_init(e_non_existing_credential,-20004);
	
	function is_autonomous return boolean;
	
	procedure create_credential(p_credential_name varchar2,
	                            p_username        varchar2,
	                            p_password        varchar2);
    
    procedure drop_credential(p_credential_name varchar2);
	
	procedure create_or_replace_credential(p_credential_name varchar2,
   	                                       p_username        varchar2,
	                                       p_password        varchar2);
	                                       
    procedure create_external_json_collection(p_collection_name varchar2,
                                              p_credential_name varchar2,
                                              p_file_list       clob);
                                              
    procedure drop_external_json_collection(p_collection_name varchar2);
   
end;
/
	              


