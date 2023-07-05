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
