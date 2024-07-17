--- Let's try the MEMOPTIMIZE for WRITE 19c feature with JSON documents !!!
-- We will compare unitary inserts into a regular table and into a MEMOPTIMIZE FOR WRITE table
-- MEMOPTIMIZE FOR WRITE may be very suitable for IOT based workloads !!!

-- Create a regular table with a JSON column !!!

sqlplus soe/soe@myoracledb:1521/orclpdb1

create table OI_JSON_REGULAR
(
ID number(12),
OI_json VARCHAR2(4000),
CONSTRAINT oi_json_regular_pk primary Key (id),
CONSTRAINT OI_json_regular_check CHECK (OI_json IS JSON)
);

-- Create a MEMOPTIMIZE FOR WRITE table with JSON column !!!

create table OI_JSON_MEMOPT4WRITE 
(
    ID number(12), 
    OI_JSON varchar2(4000),
    CONSTRAINT oi_json_MEMOPT_pk primary Key (id),
    CONSTRAINT OI_json_MEMOPT_check CHECK (OI_json IS JSON)
) segment creation immediate memoptimize for write;


-- Now we create a PL/SQL block that inserts row by row:

create or replace procedure PC_INS_REGULAR (p_num_rows IN PLS_INTEGER)
IS
    CURSOR c_oi (p_num IN PLS_INTEGER)
    IS
        select id, OI_json
        from OI_JSON_ORDER_ITEMS
        where rownum <= p_num;
begin
    FOR cur in c_oi (p_num_rows)
    LOOP
        insert into OI_JSON_REGULAR (id,oi_json) values (cur.id,cur.oi_json);
        commit;
    END LOOP;
END;
/

create or replace procedure PC_INS_MEMOPT4WRITE (p_num_rows IN PLS_INTEGER)
IS
    CURSOR c_oi (p_num IN PLS_INTEGER)
    IS
        select id, OI_json
        from OI_JSON_ORDER_ITEMS
        where rownum <= p_num;
begin
    FOR cur in c_oi (p_num_rows)
    LOOP
        insert /*+ memoptimize_write */ into OI_JSON_MEMOPT4WRITE (id,oi_json) values (cur.id,cur.oi_json);
        commit;
    END LOOP;
END;
/

-- Let's compare !!!
set timing on
--- 1000 rows !!!
truncate table OI_JSON_REGULAR;
truncate table OI_JSON_MEMOPT4WRITE;


SQL> exec PC_INS_REGULAR(1000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:00.23
SQL> exec PC_INS_MEMOPT4WRITE(1000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:18.12

-- => The first time we use the table, we get a pretty slow result. This is because a memory allocation occurs in the large pool (might be tuned for correct sizing !!!)
-- But subsequent executions are much faster !!!

SQL> exec PC_INS_MEMOPT4WRITE(1000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:00.05
SQL> truncate table OI_JSON_MEMOPT4WRITE;

Table truncated.

Elapsed: 00:00:00.07
SQL> exec PC_INS_MEMOPT4WRITE(1000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:00.04
SQL>


-- 10.000 rows !!!
truncate table OI_JSON_REGULAR;
truncate table OI_JSON_MEMOPT4WRITE;


SQL> exec PC_INS_REGULAR(10000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:05.30
SQL> exec PC_INS_MEMOPT4WRITE(10000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:00.70

-- => MEMOPTIMIZE FOR WRITE is way faster !!!

--- 100.000 rows !!!

truncate table OI_JSON_REGULAR;
truncate table OI_JSON_MEMOPT4WRITE;

SQL> exec PC_INS_REGULAR(100000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:24.83
SQL> exec PC_INS_MEMOPT4WRITE(100000)

PL/SQL procedure successfully completed.

Elapsed: 00:00:08.00
SQL>

-- Count the rows in each table and check:

select count(*) from OI_JSON_REGULAR;

  COUNT(*)
----------
    100000

select count(*) from OI_JSON_MEMOPT4WRITE

  COUNT(*)
----------
     99390

-- This is because rows are committed asynchronously in the MEMOPTIMIZE FOR WRITE table !!! We could use DBMS_MEMOPTIMIZE.WRITE_END procedure to force an immediate flush of the large pool to the table !!!
-- This is important to understand, and might be suitable for your IOT business case (or not).

--- After some seconds, the missing rows are flushed and we can see them in the table !!!

SQL> select count(*) from OI_JSON_MEMOPT4WRITE;

  COUNT(*)
----------
    100000


--- 1.000.000 rows !!!

truncate table OI_JSON_REGULAR;
truncate table OI_JSON_MEMOPT4WRITE;


SQL> exec PC_INS_REGULAR(1000000)

PL/SQL procedure successfully completed.

Elapsed: 00:04:28.81
SQL> select count(*) from OI_JSON_REGULAR;

  COUNT(*)
----------
   1000000


SQL> exec PC_INS_MEMOPT4WRITE(1000000)

PL/SQL procedure successfully completed.

Elapsed: 00:01:29.13
SQL> select count(*) from OI_JSON_MEMOPT4WRITE;

  COUNT(*)
----------
    999875

Elapsed: 00:00:00.15
SQL> exec DBMS_MEMOPTIMIZE.WRITE_END

PL/SQL procedure successfully completed.

Elapsed: 00:00:00.04
SQL> select count(*) from OI_JSON_MEMOPT4WRITE;

  COUNT(*)
----------
   1000000

Elapsed: 00:00:00.03
SQL>

