-- This procedure signals all connected sessions to stop the workload capture and stops future requests to the database from being captured.

execute dbms_workload_capture.finish_capture();

/*
By default, FINISH_CAPTURE waits for 30 seconds to receive a successful acknowledgement from all sessions in the database cluster before timing out.
All sessions that either were in the middle of executing a user request or received a new user request, while FINISH_CAPTURE
was waiting for acknowledgements, flush their buffers and send back their acknowledgement to FINISH_CAPTURE.
If a database session remains idle (waiting for the next user request) throughout the duration of FINISH_CAPTURE, the session might have unflushed capture buffers and does not send it's acknowledgement to FINISH_CAPTURE. To avoid this, do not have sessions that remain idle (waiting for the next user request) while invoking FINISH_CAPTURE. Either close the database session(s) before running FINISH_CAPTURE or send new database requests to those sessions during FINISH_CAPTURE.
*/
~

