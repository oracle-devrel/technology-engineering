#!/bin/bash
## Enqueue a message in USUAQ2.QUEUE2 !!!
## Usage: enqueue_msg.sh subject category content priority

subject=$1
category=$2
content=$3
priority=$4

sqlplus -s USUAQ2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB2 << EOF
DECLARE
   enqueue_options     DBMS_AQ.enqueue_options_t;
   message_properties  DBMS_AQ.message_properties_t;
   message_handle      RAW(16);
   message             USUAQ2.T_MSG1;
BEGIN
    --- Format the message !!!
   message := USUAQ2.T_MSG1(
        f_subject => '$subject',
    f_category => '$category',
    f_content => '$content'
   );
   -- Setting message properties: enqueue by APPUSER1 (APP1)
    message_properties := DBMS_AQ.message_properties_t (
        priority => $priority,
        delay => 0,
        expiration => 3600,
        correlation => 'APP2'
    );
   --
   DBMS_AQ.ENQUEUE(
      queue_name              => 'USUAQ2.QUEUE2', 
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
