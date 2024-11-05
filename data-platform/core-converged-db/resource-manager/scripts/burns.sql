-- Connect to REDEF_USER and run the script to burn CPU
-- First execute burn.sql to create the function and the required user

SELECT redef_user.burn_cpu (5) FROM dual;
