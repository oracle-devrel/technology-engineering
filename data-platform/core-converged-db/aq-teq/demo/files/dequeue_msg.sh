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
