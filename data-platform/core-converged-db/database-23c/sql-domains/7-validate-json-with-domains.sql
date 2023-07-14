REM script for 23c: 7-validate-json-with-domains.sql

-- create a domain p_recorddomain to validate a given JSON schema

drop domain p_recorddomain;

create domain p_recorddomain AS JSON VALIDATE USING '{
"type": "object",
"properties": {
    "first_name": { "type": "string" },
    "last_name": { "type": "string" },
    "birthday": { "type": "string", "format": "date" },
     "address": {
       "type": "object",
       "properties": {
           "street_address": { "type": "string" },
                  "city": { "type": "string" },
                  "state": { "type": "string" },
                  "country": { "type" : "string" }
                      } 
                 } 
              } 
 }' ;


-- a check constraint is automatically created.

set long 1000
col name format a20
select name, generated, constraint_type, search_condition   
     from user_domain_constraints where domain_name like 'P_RECORD%';


-- create a table person_json

drop table person;

create table person (id NUMBER, 
               p_record JSON DOMAIN p_recorddomain);


-- insert valid and invalid data

insert into person values (1, '{
"first_name": "George",
"last_name": "Washington",
"birthday": "1732-02-22",
"address": {
            "street_address": "3200 Mount Vernon Memorial Highway",
             "city": "Mount Vernon",
             "state": "Virginia",
             "country": "United States"
           }
                                 }');

-- try to insert invalid data

insert into person values (2, '{
"name": "George Washington",
"birthday": "February 22, 1732",
"address": "Mount Vernon, Virginia, United States"
     }');  




