https://<yourpublicip>/vnc.html?resize=remote

ssh -i /Users/stef/Documents/TSE/Workshops/006.WinningvsMongo.Demo/SSH/id_rsa_lab opc@<yourpublicip>

- Review and execute the python script !!!

cd /home/oracle
cat soda_basic.py
python3 soda_basic.py

--- SODA with SQLcL
unset ORACLE_HOME
cd /home/oracle/sqlcl/bin

./sql soe/soe@myoracledb:1521/orclpdb1

soda list
soda count mycollection
soda get mycollection -all
soda get mycollection -k <PUT YOUR KEY HERE FROM THE PREVIOUS STEP>
soda insert mycollection {"name" : "Alex"}
soda get mycollection -all
soda get mycollection -k <PUT YOUR KEY HERE FROM THE LAST INSERTED DOCUMENT>
soda remove mycollection -k <PUT YOUR KEY HERE FROM THE LAST INSERTED DOCUMENT>
soda get mycollection -all
soda insert mycollection {"name": "Mick", "address": {"city": "Sydney"}}
soda get mycollection -all

-- Query by Example:
soda get mycollection -f {"address": {"city": "Sydney"}}

--- We can create a new collection from sqlcl:
soda create mynewcollection
soda insert mynewcollection {"name": "Charlie", "address": {"city": "London"}}

--- Use database actions to create a new collection and insert a document: {"name": "Ron", "address": {"city": "London"}}
-- Create a collection named newcollection
-- Insert a doc {"name": "Ron", "address": {"city": "London"}}


https://<yourpublicip>/vnc.html?resize=remote

-- Access the list of collections through REST endpoint !!!
-- Use the following endpoints to manage collections and documents !

From a browser: http://<yourpublicip>:8080/ords/soe/soda/latest/
From the operating system: curl -X GET http://localhost:8080/ords/soe/soda/latest/ | jq

-- Create a new collection:
curl -X PUT http://localhost:8080/ords/soe/soda/latest/newcollection/

--- Insert a document in the new collection:

curl -X POST --data-binary '{"name": "Keith", "address": {"city": "London"}}' -H "Content-Type: application/json" http://localhost:8080/ords/soe/soda/latest/newcollection

--- Retrieve the document in the collection:

curl -X GET http://localhost:8080/ords/soe/soda/latest/newcollection | jq

--- Publish relational tables with ORDS:
cd /home/oracle
source .bashrc
sqlplus soe/soe@myoracledb:1521/orclpdb1

-- Publish the CUSTOMERS table for REST access !!!
DECLARE
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN

    ORDS.ENABLE_OBJECT(p_enabled => TRUE,
                       p_schema => 'SOE',
                       p_object => 'CUSTOMERS',
                       p_object_type => 'TABLE',
                       p_object_alias => 'customers',
                       p_auto_rest_auth => FALSE);

    commit;

END;
/
exit

--- Now access your table through the REST endpoint:

curl -k http://<yourpublicip>:8080/ords/soe/customers/ | jq
curl -k http://<yourpublicip>:8080/ords/soe/customers/73 | jq

-- SQL access !!!

sqlplus soe/soe@myoracledb:1521/orclpdb1

set timing on

select json_object (
	'CUST_FIRST_NAME' value CUST_FIRST_NAME,
	'CUST_LAST_NAME' value CUST_LAST_NAME,
	'CUST_EMAIL' value CUST_EMAIL,
	'PREFERRED_CARD' value PREFERRED_CARD,
	'CREDIT_LIMIT' value CREDIT_LIMIT*1.21
	) as mijson
from customers
where rownum < 6;


select JSON_OBJECTAGG (
	KEY to_char(c.CHANNEL_ID) value c.CHANNEL_CLASS || '-' || c.CHANNEL_DESC
	) as canales
from channels c
order by c.CHANNEL_DESC;

select JSON_ARRAY (
	rownum,
	JSON_OBJECT (KEY 'Descripcion' value  CHANNEL_DESC),
	JSON_OBJECT (KEY 'ID canal' value  CHANNEL_ID)
	) as canales_array
from channels c;

-- Cross model query !!!

desc OI_JSON_ORDERS
desc WAREHOUSES

select W.WAREHOUSE_NAME, sum(to_number(json_value (OI.O_JSON, '$.ORDER_TOTAL'))) as TOTAL
from    OI_JSON_ORDERS OI,
        WAREHOUSES W
where   W.WAREHOUSE_ID = json_value (OI.O_JSON, '$.WAREHOUSE_ID')
and     W.warehouse_name in  ('McsRxsWjRxXMFDcobjhEIDdEsO','5eH6XK38SRmNEZCUg43EDIjDICDhbV','PLlypy')
group by W.WAREHOUSE_NAME
order by 1;

set lines 120
set autotrace traceonly explain

select W.WAREHOUSE_NAME, sum(to_number(json_value (OI.O_JSON, '$.ORDER_TOTAL'))) as TOTAL
from    OI_JSON_ORDERS OI,
        WAREHOUSES W
where   W.WAREHOUSE_ID = json_value (OI.O_JSON, '$.WAREHOUSE_ID')
and     W.warehouse_name in  ('McsRxsWjRxXMFDcobjhEIDdEsO','5eH6XK38SRmNEZCUg43EDIjDICDhbV','PLlypy')
group by W.WAREHOUSE_NAME
order by 1;


-- SEARCH indexes

unset ORACLE_HOME
cd /home/oracle/sqlcl/bin

./sql soe/soe@myoracledb:1521/orclpdb1

soda create musiccollection
soda insert musiccollection {"name": "The Rolling Stones","Title": "Bridges of Babylon", "Description": "A Great album by the greatest band ever"}
soda insert musiccollection {"name": "The Rolling Stones","Title": "Jump Back", "Description": "An awesome compilation by the greatest band ever"}
soda insert musiccollection {"name": "Pink Floyd","Title": "Wish you were here", "Description": "A pretty good choice"}
soda insert musiccollection {"name": "Pink Floyd","Title": "Greatest hits", "Description": "A pretty good choice"}
soda insert musiccollection {"name": "Police","Title": "Every breath you take", "Description": "Breathtaking, their greatest album"}
! echo '{"name": "Eric Clapton","Title": "Unplugged", "Description": "Awesome unplugged concert"}' > /home/oracle/tt.json
!cat /home/oracle/tt.json
soda insert musiccollection /home/oracle/tt.json

info musiccollection

CREATE SEARCH INDEX music_search_idx ON musiccollection (JSON_DOCUMENT) FOR JSON;

SELECT m.json_document.name as "Band name", m.json_document."Title" as "Title", m.json_document."Description" as "Description" 
FROM   musiccollection m
WHERE  JSON_TEXTCONTAINS(json_document, '$.Description', 'greatest band');


-- Data redaction !!!

./sql soe/soe@myoracledb:1521/orclpdb1

SELECT JSON_QUERY(O_JSON,'$' WITH WRAPPER) from OI_JSON_ORDERS where ID = 12345;

-- We want to redact the card_number for USER2, but not for USER1 !!!

--- Need to create a view in front of the JSON table, as a DR policy cannot be created directly on the JSON table !!!

-- Now we re-create the view V_ORDERS:

create or replace view V_ORDERS
as
SELECT  	ID as ORDER_ID,
	        json_value(O_JSON, '$.ORDER_DATE' returning DATE) as ORDER_DATE,
	        json_value(O_JSON, '$.ORDER_MODE' returning VARCHAR2(8)) as ORDER_MODE,
	        json_value(O_JSON, '$.CUSTOMER_ID' returning NUMBER(12)) as CUSTOMER_ID,
	        json_value(O_JSON, '$.ORDER_STATUS' returning NUMBER(2)) as ORDER_STATUS,
	        json_value(O_JSON, '$.ORDER_TOTAL' returning NUMBER(8,2)) as ORDER_TOTAL,
	        json_value(O_JSON, '$.SALES_REP_ID' returning NUMBER(6)) as SALES_REP_ID,
	        json_value(O_JSON, '$.PROMOTION_ID' returning NUMBER(6)) as PROMOTION_ID,
	        json_value(O_JSON, '$.WAREHOUSE_ID' returning NUMBER(6)) as WAREHOUSE_ID,
	        json_value(O_JSON, '$.DELIVERY_TYPE' returning VARCHAR2(15)) as DELIVERY_TYPE,
	        json_value(O_JSON, '$.COST_OF_DELIVERY' returning NUMBER(6)) as COST_OF_DELIVERY,
            json_value(O_JSON, '$.WAIT_TILL_ALL_AVAILABLE' returning VARCHAR2(15)) as WAIT_TILL_ALL_AVAILABLE,
            json_value(O_JSON, '$.DELIVERY_ADDRESS_ID' returning NUMBER(12)) as DELIVERY_ADDRESS_ID,
            json_value(O_JSON, '$.CUSTOMER_CLASS' returning VARCHAR2(30)) as CUSTOMER_CLASS,
            json_value(O_JSON, '$.CARD_NUMBER' returning VARCHAR2(12)) as CARD_NUMBER,
            json_value(O_JSON, '$.INVOICE_ADDRESS_ID' returning NUMBER(12)) as INVOICE_ADDRESS_ID
from SOE.OI_JSON_ORDERS;

exit

--- Now we would create a DR policy as SYSTEM:

./sql system/"Oracle_4U"@myoracledb:1521/orclpdb1

BEGIN
    SYS.DBMS_REDACT.DROP_POLICY (
        object_schema=> 'SOE',
        object_name => 'V_ORDERS',
        policy_name => 'POL_HIDE_ORDER_TOTAL');
END;
/

BEGIN
SYS.DBMS_REDACT.ADD_POLICY(
object_schema=> 'SOE',
object_name => 'V_ORDERS',
column_name => 'CARD_NUMBER',
column_description => 'Card Number',
policy_name => 'POL_HIDE_ORDER_TOTAL',
policy_description => 'Hide card number',
function_type => DBMS_REDACT.PARTIAL,
function_parameters => 'VVVVVVVVVVVV,VVVVVVVVVVVV,*,1,5',
expression => 'SYS_CONTEXT(''USERENV'',''SESSION_USER'') = ''USER2''');
end;
/
exit

--- Now we query the view as USER1 or USER2 !!!
unset ORACLE_HOME
cd sqlcl/bin
./sql user1/"Oracle_4U"@myoracledb:1521/orclpdb1

select * 
from soe.v_orders
where order_id = 12345;
exit

./sql user2/"Oracle_4U"@myoracledb:1521/orclpdb1

select * 
from soe.v_orders
where order_id = 12345;
exit

--- Data Redaction works also with ORDS !!!
--- Let's enable ORDS for USER1 and USER2 !!!

cd /home/oracle
source .bashrc

sqlplus system/"Oracle_4U"@myoracledb:1521/orclpdb1


BEGIN
    ords_admin.enable_schema (
        p_enabled               => TRUE,
        p_schema                => 'USER1',
        p_url_mapping_type      => 'BASE_PATH',
        p_url_mapping_pattern   => 'user1',
        p_auto_rest_auth        => TRUE   -- this flag says, don't expose my REST APIs
    );
    COMMIT;
END;
/

BEGIN
    ords_admin.enable_schema (
        p_enabled               => TRUE,
        p_schema                => 'USER2',
        p_url_mapping_type      => 'BASE_PATH',
        p_url_mapping_pattern   => 'user2',
        p_auto_rest_auth        => TRUE   -- this flag says, don't expose my REST APIs
    );
    COMMIT;
END;
/
exit


sqlplus USER2/"Oracle_4U"@myoracledb:1521/orclpdb1

create or replace view V_ORDERS as select * from soe.v_orders;


DECLARE
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN

    ORDS.ENABLE_OBJECT(p_enabled => TRUE,
                       p_schema => 'USER2',
                       p_object => 'V_ORDERS',
                       p_object_type => 'VIEW',
                       p_object_alias => 'v_orders',
                       p_auto_rest_auth => FALSE);

    commit;

END;
/

exit

Test your endpoint with: http://<yourpublicip>:8080/ords/user2/v_orders/

sqlplus USER1/"Oracle_4U"@myoracledb:1521/orclpdb1

create or replace view V_ORDERS as select * from soe.v_orders;


DECLARE
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN

    ORDS.ENABLE_OBJECT(p_enabled => TRUE,
                       p_schema => 'USER1',
                       p_object => 'V_ORDERS',
                       p_object_type => 'VIEW',
                       p_object_alias => 'v_orders',
                       p_auto_rest_auth => FALSE);

    commit;

END;
/
exit


Test your endpoint with: http://<yourpublicip>:8080/ords/user1/v_orders/