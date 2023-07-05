-- Enqueue some messages !!!

--- 15 Non urgent messages !!!

for i in $(seq 15)
do
    ./enqueue_msg.sh "Message $i" "NON URGENT" "This is a non urgent message" 2
done


--- 15  urgent messages !!!
for i in $(seq 15)
do
    ./enqueue_msg.sh "Message $i" "URGENT" "This is an urgent message" 1
done

--- Check the messages:


[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Dec 28 11:36:58 2022
Version 19.14.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.

Last Successful login time: Wed Dec 28 2022 11:36:30 +00:00

Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.14.0.0.0

SQL> SQL> SQL> SQL> SQL>
QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 32		1

-- Dequeue with subscapp3: this will dequeue only messages with: tab.user_data.f_category=''NON URGENT'' and priority>1
--
--- Dequeue one:

./dequeue_msg.sh APPUSER3 subscapp3

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg.sh APPUSER3 subscapp3

Subject: Message 1
Category: NON URGENT
Content: This is a non urgent message

-- Dequeue another one:

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg.sh APPUSER3 subscapp3
Subject: Message 2
Category: NON URGENT
Content: This is a non urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$

-- Now dequeue one with subscapp2: this will dequeue only messages with: tab.user_data.f_category=''URGENT'' and priority=1

./dequeue_msg.sh APPUSER2 subscapp2

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg.sh APPUSER2 subscapp2
Subject: Message 1
Category: URGENT
Content: This is an urgent message

-- Dequeue another one:

[oracle@rdbms19oniaas AQ]$ ./dequeue_msg.sh APPUSER2 subscapp2
Subject: Message 2
Category: URGENT
Content: This is an urgent message

PL/SQL procedure successfully completed.

--- Now let's dequeue with array processing:

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER3 subscapp3 10
Number of messages dequeued: 10
Message number 1 Message 3 NON URGENT This is a non urgent message
Message number 2 Message 4 NON URGENT This is a non urgent message
Message number 3 Message 5 NON URGENT This is a non urgent message
Message number 4 Message 6 NON URGENT This is a non urgent message
Message number 5 Message 7 NON URGENT This is a non urgent message
Message number 6 Message 8 NON URGENT This is a non urgent message
Message number 7 Message 9 NON URGENT This is a non urgent message
Message number 8 Message 10 NON URGENT This is a non urgent message
Message number 9 Message 11 NON URGENT This is a non urgent message
Message number 10 Message 12 NON URGENT This is a non urgent message

--- Let's array dequeue again:

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER3 subscapp3 10
Number of messages dequeued: 3
Message number 1 Message 13 NON URGENT This is a non urgent message
Message number 2 Message 14 NON URGENT This is a non urgent message
Message number 3 Message 15 NON URGENT This is a non urgent message

PL/SQL procedure successfully completed.

--- If there are no messages waiting to be dequeued:

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER3 subscapp3 10
Nothing to fetch

PL/SQL procedure successfully completed.

--- Array dequeue with subscapp2:
[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscapp2 10
Number of messages dequeued: 10
Message number 1 Message 3 URGENT This is an urgent message
Message number 2 Message 4 URGENT This is an urgent message
Message number 3 Message 5 URGENT This is an urgent message
Message number 4 Message 6 URGENT This is an urgent message
Message number 5 Message 7 URGENT This is an urgent message
Message number 6 Message 8 URGENT This is an urgent message
Message number 7 Message 9 URGENT This is an urgent message
Message number 8 Message 10 URGENT This is an urgent message
Message number 9 Message 11 URGENT This is an urgent message
Message number 10 Message 12 URGENT This is an urgent message

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscapp2 10
Number of messages dequeued: 3
Message number 1 Message 13 URGENT This is an urgent message
Message number 2 Message 14 URGENT This is an urgent message
Message number 3 Message 15 URGENT This is an urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscapp2 10
Nothing to fetch

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 32	       31


--- Add a new subscriber: subscall will dequeue any messages
sqlplus USUAQ1/"Oracle_4U"@rdbms19oniaas:1521/ORCLPDB1

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


--- Enqueue some messages again:

--- 15 Non urgent messages !!!

for i in $(seq 15)
do
    ./enqueue_msg.sh "Message $i" "NON URGENT" "This is a non urgent message" 2
done


--- 15  urgent messages !!!
for i in $(seq 15)
do
    ./enqueue_msg.sh "Message $i" "URGENT" "This is an urgent message" 1
done

--- Check the messages:

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 62	       31


-- Now dequeue all the messages with subscall !!!
--- We use an array size of 30:

./dequeue_array_msg.sh APPUSER2 subscall 30

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscall 30
Number of messages dequeued: 30
Message number 1 Message 1 NON URGENT This is a non urgent message
Message number 2 Message 2 NON URGENT This is a non urgent message
Message number 3 Message 3 NON URGENT This is a non urgent message
Message number 4 Message 4 NON URGENT This is a non urgent message
Message number 5 Message 5 NON URGENT This is a non urgent message
Message number 6 Message 6 NON URGENT This is a non urgent message
Message number 7 Message 7 NON URGENT This is a non urgent message
Message number 8 Message 8 NON URGENT This is a non urgent message
Message number 9 Message 9 NON URGENT This is a non urgent message
Message number 10 Message 10 NON URGENT This is a non urgent message
Message number 11 Message 11 NON URGENT This is a non urgent message
Message number 12 Message 12 NON URGENT This is a non urgent message
Message number 13 Message 13 NON URGENT This is a non urgent message
Message number 14 Message 14 NON URGENT This is a non urgent message
Message number 15 Message 15 NON URGENT This is a non urgent message
Message number 16 Message 1 URGENT This is an urgent message
Message number 17 Message 2 URGENT This is an urgent message
Message number 18 Message 3 URGENT This is an urgent message
Message number 19 Message 4 URGENT This is an urgent message
Message number 20 Message 5 URGENT This is an urgent message
Message number 21 Message 6 URGENT This is an urgent message
Message number 22 Message 7 URGENT This is an urgent message
Message number 23 Message 8 URGENT This is an urgent message
Message number 24 Message 9 URGENT This is an urgent message
Message number 25 Message 10 URGENT This is an urgent message
Message number 26 Message 11 URGENT This is an urgent message
Message number 27 Message 12 URGENT This is an urgent message
Message number 28 Message 13 URGENT This is an urgent message
Message number 29 Message 14 URGENT This is an urgent message
Message number 30 Message 15 URGENT This is an urgent message

PL/SQL procedure successfully completed.


-- Now use subscapp2 to dequeue urgent messages only, with an array size of 15:

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscapp2 15
Number of messages dequeued: 15
Message number 1 Message 1 URGENT This is an urgent message
Message number 2 Message 2 URGENT This is an urgent message
Message number 3 Message 3 URGENT This is an urgent message
Message number 4 Message 4 URGENT This is an urgent message
Message number 5 Message 5 URGENT This is an urgent message
Message number 6 Message 6 URGENT This is an urgent message
Message number 7 Message 7 URGENT This is an urgent message
Message number 8 Message 8 URGENT This is an urgent message
Message number 9 Message 9 URGENT This is an urgent message
Message number 10 Message 10 URGENT This is an urgent message
Message number 11 Message 11 URGENT This is an urgent message
Message number 12 Message 12 URGENT This is an urgent message
Message number 13 Message 13 URGENT This is an urgent message
Message number 14 Message 14 URGENT This is an urgent message
Message number 15 Message 15 URGENT This is an urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER2 subscapp2 15
Nothing to fetch

PL/SQL procedure successfully completed.

-- And use subscapp3 to dequeue non urgent messages:

./dequeue_array_msg.sh APPUSER3 subscapp3 15

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER3 subscapp3 15
Number of messages dequeued: 15
Message number 1 Message 1 NON URGENT This is a non urgent message
Message number 2 Message 2 NON URGENT This is a non urgent message
Message number 3 Message 3 NON URGENT This is a non urgent message
Message number 4 Message 4 NON URGENT This is a non urgent message
Message number 5 Message 5 NON URGENT This is a non urgent message
Message number 6 Message 6 NON URGENT This is a non urgent message
Message number 7 Message 7 NON URGENT This is a non urgent message
Message number 8 Message 8 NON URGENT This is a non urgent message
Message number 9 Message 9 NON URGENT This is a non urgent message
Message number 10 Message 10 NON URGENT This is a non urgent message
Message number 11 Message 11 NON URGENT This is a non urgent message
Message number 12 Message 12 NON URGENT This is a non urgent message
Message number 13 Message 13 NON URGENT This is a non urgent message
Message number 14 Message 14 NON URGENT This is a non urgent message
Message number 15 Message 15 NON URGENT This is a non urgent message

PL/SQL procedure successfully completed.

[oracle@rdbms19oniaas AQ]$ ./dequeue_array_msg.sh APPUSER3 subscapp3 15
Nothing to fetch

PL/SQL procedure successfully completed.


[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh  (note the view refresh is asyncronous)

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 62	       46

[oracle@rdbms19oniaas AQ]$ ./check_queue_QUEUE1.sh

QUEUE_SCHEMA		       QUEUE_NAME		      ENQUEUED_MSGS DEQUEUED_MSGS
------------------------------ ------------------------------ ------------- -------------
USUAQ1			       AQ$_QTABLE1_E				  1		0
USUAQ1			       QUEUE1					 62	       61