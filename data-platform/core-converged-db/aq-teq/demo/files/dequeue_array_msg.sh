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
