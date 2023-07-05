#!/bin/bash

sqlplus -s USUAQ2/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB2 << EOF
col queue_schema format a30
col queue_name format a30
set lines 120

select QUEUE_SCHEMA, QUEUE_NAME, ENQUEUED_MSGS,DEQUEUED_MSGS from V\$PERSISTENT_QUEUES;
exit
EOF
exit 0
