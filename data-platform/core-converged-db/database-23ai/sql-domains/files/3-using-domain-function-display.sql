REM script for 23c: 3-using-domain-function-display.sql

-- use domain function domain_display 

col p_name format a25
col DISPLAY format a25
select p_name, domain_display(p_email) "Display" from person;
