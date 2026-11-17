-- Run once as the test schema through SQLcl. Creates only CT_COLOCATION_* objects.
-- Hashing the sequential key distributes inserts among table and index partitions.
create table ct_colocation_insert_log (
  id number not null,
  payload varchar2(100) default rpad('x',100,'x') not null,
  created_at timestamp default systimestamp not null
)
partition by hash (id)
partitions 16;

-- A local PK index follows the same hash partitioning and avoids a single
-- right-edge index block becoming the buffer-busy contention point.
create unique index ct_colocation_insert_log_pk on ct_colocation_insert_log (id) local;

alter table ct_colocation_insert_log add constraint ct_colocation_insert_log_pk
  primary key (id) using index ct_colocation_insert_log_pk;

-- NOORDER/CACHE prevents sequence allocation itself becoming the RAC bottleneck.
-- NEXTVAL remains an increasing source for primary-key index inserts.
create sequence ct_colocation_seq start with 1 increment by 1 cache 1000 noorder;

create or replace package ct_colocation_workload as
  procedure run_worker(p_seconds number, p_commit_every number);
end;
/
create or replace package body ct_colocation_workload as
  procedure run_worker(p_seconds number, p_commit_every number) is
    l_until pls_integer := dbms_utility.get_time + p_seconds * 100;
    l_ops pls_integer := 0;
    l_start pls_integer := dbms_utility.get_time;
  begin
    dbms_application_info.set_module('CT_COLOCATION', 'SEQUENTIAL_PK_INSERT');
    while dbms_utility.get_time < l_until loop
      insert into ct_colocation_insert_log(id) values (ct_colocation_seq.nextval);
      l_ops := l_ops + 1;
      if mod(l_ops,p_commit_every)=0 then commit; end if;
    end loop;
    commit;
    dbms_output.put_line('RESULT|'||sys_context('USERENV','INSTANCE')||'|'||sys_context('USERENV','INSTANCE_NAME')||'|'||l_ops||'|'||(dbms_utility.get_time-l_start));
  end;
end;
/
