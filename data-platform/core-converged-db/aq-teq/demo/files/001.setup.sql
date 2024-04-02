-- rdbms19oniaas

-- UNDO steps:
sqlplus sys/Oracle_4U@rdbms19oniaas:1521/ORCLPDB1 as sysdba
drop user USUAQ1 cascade;
drop user appuser1 cascade;
drop user appuser2 cascade;
drop user appuser3 cascade;




SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 ORCLPDB1			  READ WRITE NO
	 4 ORCLPDB2			  READ WRITE NO
SQL>

-- In PDB ORCLPDB1, create a database user, owner of the queue:

sqlplus sys/Oracle_4U@rdbms19oniaas:1521/ORCLPDB1 as sysdba

create user USUAQ1 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;

grant connect, resource to USUAQ1;
grant execute on dbms_aqadm to USUAQ1;
grant execute on dbms_aqin to USUAQ1;
grant execute on dbms_aqjms to USUAQ1;
grant execute on dbms_aq to USUAQ1;
grant create type to USUAQ1;
grant select_catalog_role to USUAQ1;
alter user USUAQ1 quota unlimited on USERS;
grant create database link to USUAQ1;


-- Create application users, that will enqueue and dequeue from the queue

create user appuser1 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to appuser1;
alter user appuser1 quota unlimited on USERS;

create user appuser2 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to appuser2;
alter user appuser2 quota unlimited on USERS;

create user appuser3 identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to appuser3;
alter user appuser3 quota unlimited on USERS;

grant connect, resource to APPUSER1;
grant execute on dbms_aqadm to APPUSER1;
grant execute on dbms_aqin to APPUSER1;
grant execute on dbms_aqjms to APPUSER1;
grant execute on dbms_aq to APPUSER1;
grant create type to APPUSER1;
grant select_catalog_role to APPUSER1;
alter user APPUSER1 quota unlimited on USERS;

grant connect, resource to APPUSER2;
grant execute on dbms_aqadm to APPUSER2;
grant execute on dbms_aqin to APPUSER2;
grant execute on dbms_aqjms to APPUSER2;
grant execute on dbms_aq to APPUSER2;
grant create type to APPUSER2;
grant select_catalog_role to APPUSER2;
alter user APPUSER2 quota unlimited on USERS;

grant connect, resource to APPUSER3;
grant execute on dbms_aqadm to APPUSER3;
grant execute on dbms_aqin to APPUSER3;
grant execute on dbms_aqjms to APPUSER3;
grant execute on dbms_aq to APPUSER3;
grant create type to APPUSER3;
grant select_catalog_role to APPUSER3;
alter user APPUSER3 quota unlimited on USERS;

exit

-- With user USUAQ1, use package DBMS_AQADM to create a queue table:

sqlplus USUAQ1/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1

create or replace type T_MSG1 as OBJECT (
    f_subject varchar2(300),
    f_category varchar2(30),
    f_content varchar2(1000)
);
/

create or replace type TAB_MSG1 as table of T_MSG1;
/


--- Grant execute on the type to application users !!!

grant execute on T_MSG1 to APPUSER1;
grant execute on T_MSG1 to APPUSER2;
grant execute on T_MSG1 to APPUSER3;
grant execute on TAB_MSG1 to APPUSER1;
grant execute on TAB_MSG1 to APPUSER2;
grant execute on TAB_MSG1 to APPUSER3;

BEGIN
    DBMS_AQADM.CREATE_QUEUE_TABLE (
        queue_table => 'QTABLE1',
        queue_payload_type => 'T_MSG1',
        multiple_consumers => TRUE,
        auto_commit => FALSE
    );
END;
/

SQL> desc USUAQ1.QTABLE1
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 Q_NAME 					    VARCHAR2(128)
 MSGID					   NOT NULL RAW(16)
 CORRID 					    VARCHAR2(128)
 PRIORITY					    NUMBER
 STATE						    NUMBER
 DELAY						    TIMESTAMP(6)
 EXPIRATION					    NUMBER
 TIME_MANAGER_INFO				    TIMESTAMP(6)
 LOCAL_ORDER_NO 				    NUMBER
 CHAIN_NO					    NUMBER
 CSCN						    NUMBER
 DSCN						    NUMBER
 ENQ_TIME					    TIMESTAMP(6)
 ENQ_UID					    VARCHAR2(128)
 ENQ_TID					    VARCHAR2(30)
 DEQ_TIME					    TIMESTAMP(6)
 DEQ_UID					    VARCHAR2(128)
 DEQ_TID					    VARCHAR2(30)
 RETRY_COUNT					    NUMBER
 EXCEPTION_QSCHEMA				    VARCHAR2(128)
 EXCEPTION_QUEUE				    VARCHAR2(128)
 STEP_NO					    NUMBER
 RECIPIENT_KEY					    NUMBER
 DEQUEUE_MSGID					    RAW(16)
 SENDER_NAME					    VARCHAR2(128)
 SENDER_ADDRESS 				    VARCHAR2(1024)
 SENDER_PROTOCOL				    NUMBER
 USER_DATA					    T_MSG1
 USER_PROP					    SYS.ANYDATA

-- Create a queue on top of the queue table:

BEGIN
    DBMS_AQADM.CREATE_QUEUE (
        queue_name => 'QUEUE1',
        queue_table => 'QTABLE1'
    );
END;
/

-- Start the queue:

BEGIN
    DBMS_AQADM.START_QUEUE (
        queue_name => 'QUEUE1'
    );
END;
/

--- Grant privs on the queue to other users:

--- Grant enqueue on QUEUE1 to APPUSER1:

BEGIN
    DBMS_AQADM.GRANT_QUEUE_PRIVILEGE (
        privilege => 'ENQUEUE',
        queue_name => 'QUEUE1',
        grantee => 'APPUSER1',
        grant_option => FALSE
    );
END;
/

-- Grant dequeue on QUEUE1 to APPUSER2 and APPUSER3:


BEGIN
    DBMS_AQADM.GRANT_QUEUE_PRIVILEGE (
        privilege => 'DEQUEUE',
        queue_name => 'QUEUE1',
        grantee => 'APPUSER2',
        grant_option => FALSE
    );
    DBMS_AQADM.GRANT_QUEUE_PRIVILEGE (
        privilege => 'DEQUEUE',
        queue_name => 'QUEUE1',
        grantee => 'APPUSER3',
        grant_option => FALSE
    );
END;
/

--- Create subscribers on the queue:

--- subscapp2 will dequeue messages with priority 1 and category = 'URGENT'.
--- Note that f_category is a field of the message payload !!!

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('subscapp2', null, null); 
   DBMS_AQADM.ADD_SUBSCRIBER(
      queue_name     => 'USUAQ1.QUEUE1', 
      subscriber     =>  subscriber, 
      rule => 'tab.user_data.f_category=''URGENT'' and priority=1');
END;
/

--- subscapp3 will dequeue messages with priority greater than 1 and category = 'NON URGENT'.
--- Note that f_category is a field of the message payload !!!

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('subscapp3', null, null); 
   DBMS_AQADM.ADD_SUBSCRIBER(
      queue_name     => 'USUAQ1.QUEUE1', 
      subscriber     =>  subscriber, 
      rule => 'tab.user_data.f_category=''NON URGENT'' and priority>1');
END;
/

--- subscall will dequeue any messages
--- Note that f_category is a field of the message payload !!!

DECLARE 
   subscriber       sys.aq$_agent; 
BEGIN 
   subscriber := sys.aq$_agent('subscall', null, null); 
   DBMS_AQADM.ADD_SUBSCRIBER(
      queue_name     => 'USUAQ1.QUEUE1', 
      subscriber     =>  subscriber
      );
END;
/



----
--- Code used to enqueue !!!
---

sqlplus APPUSER1/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1

DECLARE
   enqueue_options     DBMS_AQ.enqueue_options_t;
   message_properties  DBMS_AQ.message_properties_t;
   message_handle      RAW(16);
   message             USUAQ1.T_MSG1;
BEGIN
    --- Format the message !!!
   message := USUAQ1.T_MSG1(
        f_subject => 'Message 1',
    f_category => 'URGENT',
    f_content => 'This is an urgent message'
   );
   -- Setting message properties: enqueue by APPUSER1 (APP1)
    message_properties := DBMS_AQ.message_properties_t (
        priority => 1,
        delay => 0,
        expiration => 3600,
        correlation => 'APP1'
    );
   --
   DBMS_AQ.ENQUEUE(
      queue_name              => 'USUAQ1.QUEUE1', 
      enqueue_options         => enqueue_options,
      message_properties      => message_properties,
      payload                 => message,
      msgid                   => message_handle);
   COMMIT;
END;
/

--- This can be used in a shell script:

cd /home/oracle/AQ

[oracle@rdbms19oniaas AQ]$ cat enqueue_msg.sh
#!/bin/bash
## Enqueue a message in USUAQ1.QUEUE1 !!!
## Usage: enqueue_msg.sh subject category content priority

subject=$1
category=$2
content=$3
priority=$4

sqlplus -s APPUSER1/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1 << EOF
DECLARE
   enqueue_options     DBMS_AQ.enqueue_options_t;
   message_properties  DBMS_AQ.message_properties_t;
   message_handle      RAW(16);
   message             USUAQ1.T_MSG1;
BEGIN
    --- Format the message !!!
   message := USUAQ1.T_MSG1(
        f_subject => '$subject',
    f_category => '$category',
    f_content => '$content'
   );
   -- Setting message properties: enqueue by APPUSER1 (APP1)
    message_properties := DBMS_AQ.message_properties_t (
        priority => $priority,
        delay => 0,
        expiration => 3600,
        correlation => 'APP1'
    );
   --
   DBMS_AQ.ENQUEUE(
      queue_name              => 'USUAQ1.QUEUE1',
      enqueue_options         => enqueue_options,
      message_properties      => message_properties,
      payload                 => message,
      msgid                   => message_handle);
   COMMIT;
END;
/
exit
EOF

exit 0

col queue_schema format a30
col queue_name format a30

select QUEUE_SCHEMA, QUEUE_NAME, ENQUEUED_MSGS,DEQUEUED_MSGS from GV$PERSISTENT_QUEUES

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					  2		0


-- Dequeue messages !!!

--- Code used to dequeue messages !!!

sqlplus -s APPUSER2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1

SET SERVEROUTPUT ON
DECLARE
e_nothing_to_fetch EXCEPTION;
PRAGMA EXCEPTION_INIT(e_nothing_to_fetch, -25228);
--
dequeue_options     DBMS_AQ.dequeue_options_t;
message_properties  DBMS_AQ.message_properties_t;
message_handle      RAW(16);
message             USUAQ1.T_MSG1;
BEGIN

   dequeue_options.consumer_name := 'subscapp3';
	dequeue_options.dequeue_mode := DBMS_AQ.REMOVE;
	dequeue_options.navigation := DBMS_AQ.FIRST_MESSAGE;
	dequeue_options.wait := DBMS_AQ.NO_WAIT;

   DBMS_AQ.DEQUEUE(
      queue_name          =>     'USUAQ1.QUEUE1',
      dequeue_options     =>     dequeue_options,
      message_properties  =>     message_properties,
      payload             =>     message,
      msgid               =>     message_handle);
   DBMS_OUTPUT.PUT_LINE('Subject: '||message.f_subject);
   DBMS_OUTPUT.PUT_LINE('Category: '||message.f_category);
   DBMS_OUTPUT.PUT_LINE('Content: '||message.f_content);
   COMMIT;
EXCEPTION
    WHEN e_nothing_to_fetch
    THEN
        DBMS_OUTPUT.PUT_LINE ('Nothing to fetch');
END;
/

--- We can dequeue in an array instead of one by one !!!

SET SERVEROUTPUT ON
DECLARE
e_nothing_to_fetch EXCEPTION;
PRAGMA EXCEPTION_INIT(e_nothing_to_fetch, -25228);
  dequeue_options       DBMS_AQ.dequeue_options_t;
  msg_prop_array        DBMS_AQ.message_properties_array_t := 
                        DBMS_AQ.message_properties_array_t();
  payload_array         USUAQ1.TAB_MSG1;
  msgid_array           DBMS_AQ.msgid_array_t;
  retval                PLS_INTEGER;
BEGIN
   dequeue_options.consumer_name := 'subscapp3';
	dequeue_options.dequeue_mode := DBMS_AQ.REMOVE;
	dequeue_options.navigation := DBMS_AQ.FIRST_MESSAGE;
	dequeue_options.wait := DBMS_AQ.NO_WAIT;

  retval := DBMS_AQ.DEQUEUE_ARRAY( 
              queue_name               => 'USUAQ1.QUEUE1',
              dequeue_options          => dequeue_options,
              array_size               => 10,
              message_properties_array => msg_prop_array,
              payload_array            => payload_array,
              msgid_array              => msgid_array);
  commit;
  DBMS_OUTPUT.PUT_LINE('Number of messages dequeued: ' || retval);
  EXCEPTION
    WHEN e_nothing_to_fetch
    THEN
        DBMS_OUTPUT.PUT_LINE ('Nothing to fetch');
END;
/

--- Use shell scripts !!!

[oracle@rdbms19oniaas AQ]$ cat dequeue_msg.sh
#!/bin/bash
## Dequeue a message in USUAQ1.QUEUE1 !!!
## Usage: dequeue_msg.sh schema subscriber

schema=$1
subscriber=$2

sqlplus -s $schema/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1 << EOF
SET SERVEROUTPUT ON
DECLARE
e_nothing_to_fetch EXCEPTION;
PRAGMA EXCEPTION_INIT(e_nothing_to_fetch, -25228);
--
dequeue_options     DBMS_AQ.dequeue_options_t;
message_properties  DBMS_AQ.message_properties_t;
message_handle      RAW(16);
message             USUAQ1.T_MSG1;
BEGIN

   dequeue_options.consumer_name := '$subscriber';
	dequeue_options.dequeue_mode := DBMS_AQ.REMOVE;
	dequeue_options.navigation := DBMS_AQ.FIRST_MESSAGE;
	dequeue_options.wait := DBMS_AQ.NO_WAIT;

   DBMS_AQ.DEQUEUE(
      queue_name          =>     'USUAQ1.QUEUE1',
      dequeue_options     =>     dequeue_options,
      message_properties  =>     message_properties,
      payload             =>     message,
      msgid               =>     message_handle);
   DBMS_OUTPUT.PUT_LINE('Subject: '||message.f_subject);
   DBMS_OUTPUT.PUT_LINE('Category: '||message.f_category);
   DBMS_OUTPUT.PUT_LINE('Content: '||message.f_content);
   COMMIT;
EXCEPTION
    WHEN e_nothing_to_fetch
    THEN
        DBMS_OUTPUT.PUT_LINE ('Nothing to fetch');
END;
/

exit
EOF

exit 0

[oracle@rdbms19oniaas AQ]$ cat dequeue_array_msg.sh
#!/bin/bash
## Dequeue a message in an array, from USUAQ1.QUEUE1 !!!
## Usage: dequeue_array_msg.sh schema subscriber array_size

schema=$1
subscriber=$2
asize=$3

sqlplus -s $schema/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1 << EOF
SET SERVEROUTPUT ON
DECLARE
e_nothing_to_fetch EXCEPTION;
PRAGMA EXCEPTION_INIT(e_nothing_to_fetch, -25228);
  dequeue_options       DBMS_AQ.dequeue_options_t;
  msg_prop_array        DBMS_AQ.message_properties_array_t :=
                        DBMS_AQ.message_properties_array_t();
  payload_array         USUAQ1.TAB_MSG1;
  msgid_array           DBMS_AQ.msgid_array_t;
  retval                PLS_INTEGER;
BEGIN
   dequeue_options.consumer_name := '$subscriber';
	dequeue_options.dequeue_mode := DBMS_AQ.REMOVE;
	dequeue_options.navigation := DBMS_AQ.FIRST_MESSAGE;
	dequeue_options.wait := DBMS_AQ.NO_WAIT;

  retval := DBMS_AQ.DEQUEUE_ARRAY(
              queue_name               => 'USUAQ1.QUEUE1',
              dequeue_options          => dequeue_options,
              array_size               => $asize,
              message_properties_array => msg_prop_array,
              payload_array            => payload_array,
              msgid_array              => msgid_array);
 commit;
  DBMS_OUTPUT.PUT_LINE('Number of messages dequeued: ' || retval);
  for i in 1..retval
  loop
	DBMS_OUTPUT.PUT_LINE('Message number ' || i || ' ' || payload_array(i).f_subject ||
		' ' || payload_array(i).f_category || ' ' || payload_array(i).f_content );
  end loop;

  EXCEPTION
    WHEN e_nothing_to_fetch
    THEN
        DBMS_OUTPUT.PUT_LINE ('Nothing to fetch');
END;
/

exit
EOF

exit 0
