-- Test the resource plan
-- Create a user REDEF_USER and a script to burn CPU

drop user redef_user cascade;
create user redef_user identified by test;
grant connect, resource to redef_user;
alter user redef_user quota 100M on users;

-- script for CPU burn

CREATE OR REPLACE FUNCTION redef_user.burn_cpu (p_mins IN NUMBER)
  RETURN NUMBER
AS
  l_start_time DATE;
  l_number     NUMBER := 1;
BEGIN
  l_start_time := SYSDATE;
  LOOP
    EXIT WHEN SYSDATE - l_start_time > (p_mins/24/60);
    l_number := l_number + 1;
  END LOOP;
  RETURN 0;
END;
/
grant execute on redef_user.burn_cpu to public;

-- Use burns.sql to run the script
-- SELECT redef_burn.burn_cpu (5) FROM dual;
