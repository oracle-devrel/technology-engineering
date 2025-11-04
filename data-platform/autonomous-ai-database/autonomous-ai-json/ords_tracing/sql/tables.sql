
drop table if exists ords_trc_tab;
create table ords_trc_tab (inst_id        number(10),
                           sid            number(10), 
                           serial#        number(10), 
                           username       varchar2(30),
                           sql_exec_start date,
                           command        number(10),
                           sql_id         varchar2(200),
                           sql_plan       clob);
