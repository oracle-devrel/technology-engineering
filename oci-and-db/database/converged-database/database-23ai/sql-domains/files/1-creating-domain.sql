REM Script for 23c: 1-creating-domain.sql 

-- optional drop the domain.
-- Using FORCE in contrast to PRESERVE disassociates the domain from all its dependent columns

drop domain myemail_domain;

-- create a domain to describe an email

create domain if not exists myemail_domain AS VARCHAR2(100)
default on null 'XXXX' || '@missingmail.com'
constraint email_c CHECK (regexp_like (myemail_domain, '^(\S+)\@(\S+)\.(\S+)$'))
display substr(myemail_domain, instr(myemail_domain, '@') + 1);
