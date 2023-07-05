drop table if exists test;
create table test ( id         number(10) primary key,
                    timestamp# date,
                    val        varchar2(2000));

drop sequence if exists test_seq;                   
create sequence test_seq;


create or replace trigger test_tr
before insert on test for each row
begin
    select test_seq.nextval
    into :new.id;
    
    :new.timestamp# := sysdate;
end;
/

insert into test(val) values (DBMS_RANDOM.STRING('a',2000));

commit;

    
