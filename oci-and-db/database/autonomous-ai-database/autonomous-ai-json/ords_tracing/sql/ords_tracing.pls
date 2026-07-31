create or replace package ords_trc_pkg
is
	type session_array_type is table of gv$session%rowtype;
	
	procedure snapshot(p_username varchar2 := null);

	procedure create_job(freq integer, p_username varchar2 := null);

	procedure drop_job(p_username varchar2 := null);

	function get_report(p_username varchar2 := null) return clob;

	procedure print_report(p_username varchar2 := null);

	procedure purge_logs(p_username varchar2 := null);
end;
/