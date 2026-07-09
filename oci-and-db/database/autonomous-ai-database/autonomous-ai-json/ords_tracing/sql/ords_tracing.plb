create or replace package body ords_trc_pkg
is

	procedure snapshot(p_username varchar2 := null)
	is
		v_plan clob := '';
		v_entries number(10) := 0;
	begin
		for r1 in (select * 
                   from gv$session 
                   where program = 'Oracle REST Data Services'
                   and username <> 'ORDS_PUBLIC_USER' 
				   and username = nvl(upper(p_username),username)) loop

			-- sql_id 
			if r1.sql_id is not null then
				select count(*)
				into v_entries
				from ords_trc_tab
				where inst_id = r1.inst_id
			  	and   sid     = r1.sid
			  	and   serial# = r1.serial#
			  	and   sql_id  = r1.sql_id;

				if v_entries = 0 then
					for r2 in (select * from dbms_xplan.display_cursor(r1.sql_id)) loop
						v_plan := v_plan || r2.plan_table_output || chr(10);
					end loop;							
					
					insert into ords_trc_tab
					(inst_id,sid,serial#,username,command,sql_exec_start,sql_id,sql_plan)
					values
					(r1.inst_id,r1.sid,r1.serial#,r1.username,r1.command,r1.sql_exec_start,r1.sql_id,v_plan);
				end if;
			end if;
			-- prev_sql_id
			if r1.prev_sql_id is not null then
				select count(*)
				into v_entries
				from ords_trc_tab
				where inst_id = r1.inst_id
			  	and   sid     = r1.sid
			  	and   serial# = r1.serial#
			  	and   sql_id  = r1.prev_sql_id;

				if v_entries = 0 then
				    for r2 in (select * from dbms_xplan.display_cursor(r1.prev_sql_id)) loop
					   v_plan := v_plan || r2.plan_table_output || chr(10);
				    end loop;	

					insert into ords_trc_tab
					(inst_id,sid,serial#,username,command,sql_exec_start,sql_id,sql_plan)
					values
					(r1.inst_id,r1.sid,r1.serial#,r1.username,r1.command,r1.prev_exec_start,r1.prev_sql_id,v_plan);
				end if;	
			end if;					
		end loop;
		commit;
	end;

	procedure create_job(freq integer, p_username varchar2 := null)
	is
		v_job varchar2(200) := 'ORDS_TRC_JOB';
		v_block varchar2(200) := 'BEGIN ORDS_TRC_PKG.SNAPSHOT';
		n_of_jobs number(10);
	begin
		if p_username is not null then
			v_job := v_job || '_' || upper(p_username);
			v_block := v_block || '(''' ||upper(p_username)||''')';
		end if;
		v_block := v_block||'; END;';

		select count(*)
		into n_of_jobs
		from user_scheduler_jobs
		where job_name = v_job;

		if n_of_jobs <> 0 then
			raise_application_error(-20001,'You cannot trace the same database user in more than one job');
		end if;

		dbms_scheduler.create_job(v_job,
                                  'PLSQL_BLOCK',
                                  v_block,
                                  enabled => true,
                                  repeat_interval => 'FREQ=SECONDLY;INTERVAL='||freq);
	end;

	procedure drop_job(p_username varchar2 := null)
	is
		v_job varchar2(200) := 'ORDS_TRC_JOB';
	begin		
		if p_username is not null then
			v_job := v_job || '_' || upper(p_username);
		end if;
		
		dbms_scheduler.drop_job(v_job,defer => true);
	end;

	function get_report (p_username varchar2 := null) return clob
	is
		v_rep clob := '';
		v_command varchar2(200);
		prev_username varchar2(30) := ' ';
		prev_session  varchar2(200):= ' ';
	begin
		for r in (select *
		          from ords_trc_tab
				  where username = nvl(upper(p_username),username)
				  order by username, inst_id, sid, serial#, sql_exec_start, sql_id ) loop
			if prev_username <> r.username then
			-- start of new user section
				prev_username := r.username;
				v_rep := v_rep||chr(10)||
				                  ' USERNAME : '||r.username                              ||chr(10)||
						          '======================================================'||chr(10);
			end if;

			if prev_session <> r.inst_id||':'||r.sid||':'||r.serial# then
			-- start of new sid section
				prev_session := r.inst_id||':'||r.sid||':'||r.serial#;
				v_rep := v_rep || chr(10) || 
				                  'inst_id:sid:serial# : ' || prev_session                || chr(10) ||
				                  '-----------------------------------------------------' || chr(10);
			end if;
			
			select command_name
			into v_command
			from v$sqlcommand
			where command_type = r.command;

			v_rep := v_rep || chr(10) ||
			                  'command type : '||r.command||' ('||v_command||')'||chr(10)||
			                  'plan         : '||chr(10) ||
							  r.sql_plan       || chr(10);
		end loop;
		return v_rep;
	end;

	procedure print_report(p_username varchar2 := null)
	is
		v_report clob := get_report(p_username);
	begin
		dbms_output.put_line(v_report);
	end;

	procedure purge_logs(p_username varchar2 := null)
	is
	begin
		delete from ords_trc_tab
		where username = nvl(upper(p_username),username);

		commit;
	end;
end;
/
