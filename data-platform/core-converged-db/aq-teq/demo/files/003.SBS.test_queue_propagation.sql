--- In ORCLPDB2, setup a new queue !

-- UNDO commands:
sqlplus sys/Oracle_4U@rdbms19oniaas:1521/ORCLPDB2 as sysdba
drop user USUAQ2 cascade;
drop user PDB2APPUSER1 cascade;


sqlplus sys/Oracle_4U@rdbms19oniaas:1521/ORCLPDB2 as sysdba

create user USUAQ2 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;

grant connect, resource to USUAQ2;
grant execute on dbms_aqadm to USUAQ2;
grant execute on dbms_aqin to USUAQ2;
grant execute on dbms_aqjms to USUAQ2;
grant execute on dbms_aq to USUAQ2;
grant create type to USUAQ2;
grant select_catalog_role to USUAQ2;
alter user USUAQ2 quota unlimited on USERS;


-- Create application users, that will enqueue and dequeue from the queue

create user PDB2APPUSER1 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to PDB2APPUSER1;
grant execute on dbms_aqadm to PDB2APPUSER1;
grant execute on dbms_aqin to PDB2APPUSER1;
grant execute on dbms_aqjms to PDB2APPUSER1;
grant execute on dbms_aq to PDB2APPUSER1;
grant create type to PDB2APPUSER1;
grant select_catalog_role to PDB2APPUSER1;
alter user PDB2APPUSER1 quota unlimited on USERS;

--- Setup a queue !!!
sqlplus USUAQ2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB2

create or replace type T_MSG1 as OBJECT (
    f_subject varchar2(300),
    f_category varchar2(30),
    f_content varchar2(1000)
);
/

create or replace type TAB_MSG1 as table of T_MSG1;
/


--- Grant execute on the type to application users !!!

grant execute on T_MSG1 to PDB2APPUSER1;
grant execute on TAB_MSG1 to PDB2APPUSER1;


BEGIN
    DBMS_AQADM.CREATE_QUEUE_TABLE (
        queue_table => 'QTABLE2',
        queue_payload_type => 'T_MSG1',
        multiple_consumers => TRUE,
        auto_commit => FALSE
    );
END;
/

BEGIN
    DBMS_AQADM.CREATE_QUEUE (
        queue_name => 'QUEUE2',
        queue_table => 'QTABLE2'
    );
END;
/

-- Start the queue:

BEGIN
    DBMS_AQADM.START_QUEUE (
        queue_name => 'QUEUE2'
    );
END;
/

-- Grant dequeue on QUEUE2 to PDB2APPUSER1


BEGIN
    DBMS_AQADM.GRANT_QUEUE_PRIVILEGE (
        privilege => 'DEQUEUE',
        queue_name => 'QUEUE2',
        grantee => 'PDB2APPUSER1',
        grant_option => FALSE
    );
END;
/

--- Create a subscriber on the queue:

--- subscall will dequeue any messages

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('SUBSCQUEUE2', null, null); 
   DBMS_AQADM.REMOVE_SUBSCRIBER(
      queue_name     => 'USUAQ2.QUEUE2', 
      subscriber     =>  subscriber);
END;
/

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('SUBSCQUEUE2', null, null); 
   DBMS_AQADM.ADD_SUBSCRIBER(
      queue_name     => 'USUAQ2.QUEUE2', 
      subscriber     =>  subscriber);
END;
/


---- Now define a propagation rule from QUEUE1 in database ORCLPDB1 to QUEUE2 in ORCLPDB2:

-- Connect to USUAQ1 in ORCLPDB1 to define the propagation:
--- This is a 3 steps method:
---    a. Create a db link between ORCLPDB1 and ORCLPDB2
---    b. Create a queue to queue subscriber between QUEUE1 and QUEUE2
---    c. Create a propagation schedule between the queues

sqlplus USUAQ1/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1

---    a. Create a db link between ORCLPDB1 and ORCLPDB2

create database link dbl_to_queue2 connect to USUAQ2 identified by "Oracle_4U" using 'rdbms19oniaas:1521/ORCLPDB2';

-- Test your db link:

select * from dual@dbl_to_queue2;
D
-
X

---    b. Create a queue to queue subscriber between QUEUE1 and QUEUE2: only URGENT messages with priority = 1 will be propagated !!!

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('SUBSCQUEUE2', 'USUAQ2.QUEUE2@dbl_to_queue2', null); 
   DBMS_AQADM.ADD_SUBSCRIBER(
      queue_name     => 'USUAQ1.QUEUE1', 
      subscriber     =>  subscriber, 
      rule => 'tab.user_data.f_category=''URGENT'' and priority=1',
      queue_to_queue => true);
END;
/

--- NB: messages are propagated to subscriber SUBSCQUEUE2 in queue USUAQ2.QUEUE2@dbl_to_queue2. We'll need to define this subscriber in the destination queue, if it does not exist !!!


---    c. Create a propagation schedule between the queues: latency = 0 means "propagate ASAP" !!!

BEGIN
   DBMS_AQADM.SCHEDULE_PROPAGATION(
      queue_name         =>    'USUAQ1.QUEUE1', 
      destination        =>    'dbl_to_queue2',
      destination_queue  =>    'USUAQ2.QUEUE2',
      latency            => 0);
END;
/


---- Testing the queue propagation !!!

--- Enqueue an urgent message with priority = 1 in QUEUE1
--- Observe that the message is forwarded to QUEUE2
--- Dequeue the message from QUEUE2

[oracle@rdbms19oniaas AQ]$ ./enqueue_msg.sh "Message 1" "URGENT" "This is a very urgent message" 1

PL/SQL procedure successfully completed.

-- Check QUEUE1:
[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 63	       61

-- Check QUEUE2:
[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE2.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ2			       QUEUE2					  1		0

-- Dequeue from QUEUE2:

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg_QUEUE2.sh PDB2APPUSER1 SUBSCQUEUE2
Subject: Message 1
Category: URGENT
Content: This is a very urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg_QUEUE2.sh PDB2APPUSER1 SUBSCQUEUE2
Subject: Message 2
Category: URGENT
Content: This is a very urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg_QUEUE2.sh PDB2APPUSER1 SUBSCQUEUE2
Subject: Message 3
Category: URGENT
Content: This is a very urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg_QUEUE2.sh PDB2APPUSER1 SUBSCQUEUE2
Nothing to fetch

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE2.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ2			       QUEUE2					  3		1

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE2.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ2			       QUEUE2					  3		3

--- Implement PL/SQL notification:

https://docs.oracle.com/en/database/oracle/oracle-database/19/adque/aq-operations-using-pl-sql.html#GUID-3FD95C26-D2FF-49CF-BBCF-A6E40468D55E

--- First create a PL/SQL that will be invoked each time a message is enqueued:

sqlplus USUAQ2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB2

create table TEST_LOG (txt varchar2(200));


--
CREATE OR REPLACE PROCEDURE
   PC_CALLBACK
   (
      context           RAW,
      reginfo           sys.aq$_reg_info,
      descr             sys.aq$_descriptor,
      payload           T_MSG1,
      payloadl          NUMBER
   )
AS
    id             RAW(16);
    e_nothing_to_fetch EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_nothing_to_fetch, -25228);
    dequeue_options     DBMS_AQ.dequeue_options_t;
    message_properties  DBMS_AQ.message_properties_t;
    message_handle      RAW(16);
    message             USUAQ2.T_MSG1;
BEGIN
   id := descr.msg_id;
   dequeue_options.msgid         := descr.msg_id;
   dequeue_options.consumer_name := descr.consumer_name;
   dequeue_options.dequeue_mode := DBMS_AQ.REMOVE;
   dequeue_options.navigation := DBMS_AQ.FIRST_MESSAGE;
   dequeue_options.wait := DBMS_AQ.NO_WAIT;

   DBMS_AQ.DEQUEUE(
      queue_name          =>     'USUAQ2.QUEUE2',
      dequeue_options     =>     dequeue_options,
      message_properties  =>     message_properties,
      payload             =>     message,
      msgid               =>     message_handle);

   INSERT INTO test_log (txt)
      VALUES ('Message with subject=' || message.f_subject || ' dequeued.');
   commit;
EXCEPTION
    WHEN e_nothing_to_fetch
    THEN
        --- Do nothing when no messages to dequeue !!!
        NULL;
END PC_CALLBACK;
/


DECLARE
   reginfo1 sys.aq$_reg_info;
   reginfolist sys.aq$_reg_info_list;
BEGIN
   reginfo1 := sys.aq$_reg_info('USUAQ2.QUEUE2:SUBSCQUEUE2', DBMS_AQ.NAMESPACE_AQ, 'plsql://USUAQ2.PC_CALLBACK',HEXTORAW('FF'));
   
   reginfolist := sys.aq$_reg_info_list(reginfo1);
   sys.dbms_aq.register(reginfolist, 1);
   
   commit;
END;
/


---- Testing the queue notification !!!

--- Enqueue an urgent message with priority = 1 in QUEUE1
--- Observe that the message is forwarded to QUEUE2
--- Observe that the notification PL/SQL routine was triggered, querying table TEST_LOG


[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE2.sh

no rows selected

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

no rows selected

[oracle@rdbms19oniaas AQ]$ ./enqueue_msg.sh "Message 1" "URGENT" "This is a very urgent message" 1

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$
[oracle@rdbms19oniaas AQ]$
[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       QUEUE1					  1		0

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE2.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ2			       QUEUE2					  1		0
SYS			       AQ$_AQ_SRVNTFN_TABLE_1_E 		  1		0
SYS			       AQ_SRVNTFN_TABLE_Q_1			  1		0


sqlplus USUAQ2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB2

select * from test_log;