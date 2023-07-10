[opc@rdbmsfree ~]$ docker exec -it my23free sqlplus OE/Oracle_4U@localhost:1521/freepdb1

SQL*Plus: Release 23.0.0.0.0 - Developer-Release on Tue Apr 11 11:59:22 2023
Version 23.2.0.0.0

Copyright (c) 1982, 2023, Oracle.  All rights reserved.

Last Successful login time: Tue Apr 11 2023 10:33:02 +00:00

Connected to:
Oracle Database 23c Free, Release 23.0.0.0.0 - Developer-Release
Version 23.2.0.0.0

SQL> select table_name from user_tables;

TABLE_NAME
--------------------------------------------------------------------------------
CUSTOMERS
WAREHOUSES
ORDER_ITEMS
ORDERS
INVENTORIES
PRODUCT_INFORMATION
PRODUCT_DESCRIPTIONS
PROMOTIONS
PRODUCT_REF_LIST_NESTEDTAB
SUBCATEGORY_REF_LIST_NESTEDTAB

10 rows selected.

SQL> desc customers
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 CUSTOMER_ID				   NOT NULL NUMBER(6)
 CUST_FIRST_NAME			   NOT NULL VARCHAR2(20)
 CUST_LAST_NAME 			   NOT NULL VARCHAR2(20)
 CUST_ADDRESS					    CUST_ADDRESS_TYP
 PHONE_NUMBERS					    PHONE_LIST_TYP
 NLS_LANGUAGE					    VARCHAR2(3)
 NLS_TERRITORY					    VARCHAR2(30)
 CREDIT_LIMIT					    NUMBER(9,2)
 CUST_EMAIL					    VARCHAR2(40)
 ACCOUNT_MGR_ID 				    NUMBER(6)
 CUST_GEO_LOCATION				    MDSYS.SDO_GEOMETRY
 DATE_OF_BIRTH					    DATE
 MARITAL_STATUS 				    VARCHAR2(20)
 GENDER 					    VARCHAR2(1)
 INCOME_LEVEL					    VARCHAR2(20)

SQL> desc orders
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 ORDER_ID				   NOT NULL NUMBER(12)
 ORDER_DATE				   NOT NULL TIMESTAMP(6) WITH LOCAL TIME
						     ZONE
 ORDER_MODE					    VARCHAR2(8)
 CUSTOMER_ID				   NOT NULL NUMBER(6)
 ORDER_STATUS					    NUMBER(2)
 ORDER_TOTAL					    NUMBER(8,2)
 SALES_REP_ID					    NUMBER(6)
 PROMOTION_ID					    NUMBER(6)

SQL> desc order_items
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 ORDER_ID				   NOT NULL NUMBER(12)
 LINE_ITEM_ID				   NOT NULL NUMBER(3)
 PRODUCT_ID				   NOT NULL NUMBER(6)
 UNIT_PRICE					    NUMBER(8,2)
 QUANTITY					    NUMBER(8)

SQL>

CREATE or replace JSON RELATIONAL DUALITY VIEW CUST_ORDERS 
AS 
SELECT JSON {'CUSTOMER_ID' : C.CUSTOMER_ID,
             'CUST_FIRST_NAME' : C.CUST_FIRST_NAME,
             'CUST_LAST_NAME' : C.CUST_LAST_NAME,
             'CREDIT_LIMIT' : C.CREDIT_LIMIT,
             'CUST_EMAIL' : C.CUST_EMAIL,
'orders' :
[ SELECT JSON {'ORDER_ID' : O.ORDER_ID,
              'ORDER_STATUS' : O.ORDER_STATUS,
              'ORDER_TOTAL' : O.ORDER_TOTAL,
              'items' :
              [ select JSON {'ORDER_ID' : OI.ORDER_ID,
                             'LINE_ITEM_ID' : OI.LINE_ITEM_ID,
                             'PRODUCT_ID' : OI.PRODUCT_ID,
                             'UNIT_PRICE' : OI.UNIT_PRICE,
                             'QUANTITY' : OI.QUANTITY } 
                from order_items OI WITH INSERT UPDATE DELETE
                where OI.ORDER_ID = O.ORDER_ID ]
             }
FROM ORDERS O WITH INSERT UPDATE NODELETE
WHERE O.CUSTOMER_ID = C.CUSTOMER_ID ]}
FROM CUSTOMERS C WITH INSERT UPDATE DELETE;



SQL> desc CUST_ORDERS
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 DATA						    JSON

SQL> select count(*) from CUST_ORDERS dv where dv.data.customer_id = 101;

  COUNT(*)
----------
	 0

SQL> select count(*) from CUST_ORDERS dv where json_value(data, '$.CUSTOMER_ID') = 101;

  COUNT(*)
----------
	 1
(!!!)

select * from CUST_ORDERS dv where json_value(data, '$.CUSTOMER_ID') = 101;

--- Create a new customer using regular table:

insert into customers (
 CUSTOMER_ID
 ,CUST_FIRST_NAME
 ,CUST_LAST_NAME
 ,CUST_ADDRESS
 ,PHONE_NUMBERS
 ,NLS_LANGUAGE
 ,NLS_TERRITORY
 ,CREDIT_LIMIT
 ,CUST_EMAIL
 ,ACCOUNT_MGR_ID
 ,CUST_GEO_LOCATION
 ,DATE_OF_BIRTH
 ,MARITAL_STATUS
 ,GENDER
 ,INCOME_LEVEL
)
values (
    9999,
    'Ron',
    'Wood',
    CUST_ADDRESS_TYP('Picadilly Circus','AS567','LONDON','LONDON','UK'),
    PHONE_LIST_TYP('123456789'),
    'ENG',
    'UNITED KINGDOM',
    2000,
    'ron.wood@beggarsbanquet.com',
    null,
    null,
    to_date('01/03/1954','DD/MM/YYYY'),
    'married',
    'M',
    'B: 30,000 - 49,999'
);

commit;

insert into orders (
ORDER_ID
,ORDER_DATE
,ORDER_MODE
,CUSTOMER_ID
,ORDER_STATUS
,ORDER_TOTAL
,SALES_REP_ID
,PROMOTION_ID
)
values (
    1000,
    sysdate,
    'online',
    9999,
    10,
    2000,
    163,
    1
);

SQL> select order_id from orders where customer_id = 9999;

  ORDER_ID
----------
      1000

insert into order_items (
ORDER_ID
,LINE_ITEM_ID
,PRODUCT_ID	
,UNIT_PRICE	
,QUANTITY
)
values (
    1000,
    1,
    3350,
    1000,
    1
);

commit;


--- View the data through the Duality View:

SQL> set pages 200
SQL> r
  1* select json_serialize(data PRETTY) from CUST_ORDERS dv where json_value(data, '$.CUSTOMER_ID') = 9999

JSON_SERIALIZE(DATAPRETTY)
--------------------------------------------------------------------------------
{
  "_metadata" :
  {
    "etag" : "08DF598D3A606376C73BB7804EDE718B",
    "asof" : "000000000038B92F"
  },
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}



SQL> update CUST_ORDERS
set data = '{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}'
where json_value(data, '$.CUSTOMER_ID') = 9999; 

1 row updated.

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      2       2236	 1000	       1

SQL> roll
Rollback complete.
SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1

SQL> update CUST_ORDERS
set data = JSON_MERGEPATCH (data,'{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}')
where json_value(data, '$.CUSTOMER_ID') = 9999;
  2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20   21   22   23   24   25   26   27   28   29   30   31   32   33   34
1 row updated.

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      2       2236	 1000	       1

SQL> roll
Rollback complete.
SQL> update CUST_ORDERS
set data = JSON_TRANSFORM(data,
               APPEND '$.orders.items' =
                   JSON('{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}'))
WHERE json_value(data, '$.CUSTOMER_ID') = 9999;
  2    3    4    5    6    7    8    9   10   11
1 row updated.

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      2       2236	 1000	       1

SQL> roll
Rollback complete.
SQL>

--- Add a new order item from the DV:

insert into CUST_ORDERS (data)
values (
    '{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}'
);

ERROR at line 1:
ORA-42692: Cannot insert into JSON Relational Duality View 'CUST_ORDERS': Error
while inserting into table 'CUSTOMERS'
ORA-00001: unique constraint (OE.CUSTOMERS_PK) violated

=> OK.

--- Update with JSON_MERGEPATCH:

update CUST_ORDERS
set data = JSON_MERGEPATCH (data,'{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}')
where json_value(data, '$.CUSTOMER_ID') = 9999;

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      2       2236	 1000	       1

SQL> roll
Rollback complete.

--- create a new customer through the view:

insert into CUST_ORDERS (data)
values ('{
  "CUSTOMER_ID" : 9998,
  "CUST_FIRST_NAME" : "Keith",
  "CUST_LAST_NAME" : "Richards",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "keith.richards@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1001,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1001,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1001,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}');

ERROR at line 1:
ORA-42692: Cannot insert into JSON Relational Duality View 'CUST_ORDERS': Error
while inserting into table 'ORDERS'
ORA-01400: cannot insert NULL into ("OE"."ORDERS"."ORDER_DATE")


--- 

CREATE TABLE orders3
    ( order_id           NUMBER(12)
    , order_date         DATE CONSTRAINT order3_date_nn NOT NULL
    , order_mode         VARCHAR2(8)
    , customer_id        NUMBER(6) CONSTRAINT order3_customer_id_nn NOT NULL
    , order_status       NUMBER(2)
    , order_total        NUMBER(8,2)
    , sales_rep_id       NUMBER(6)
    , promotion_id       NUMBER(6)
    , CONSTRAINT         order3_mode_lov CHECK (order_mode in ('direct','online'))
    , constraint         order3_total_min check (order_total >= 0)
    ) ;

alter table orders3 add constraint C_ORDERS3_PK primary key (order_id);
alter table orders3 add constraint C_ORDERS3_CUST_FK foreign key (customer_id) references CUSTOMERS;

CREATE TABLE order_items3
    ( order_id           NUMBER(12)
    , line_item_id       NUMBER(3)  NOT NULL
    , product_id         NUMBER(6)  NOT NULL
    , unit_price         NUMBER(8,2)
    , quantity           NUMBER(8)
    ) ;

CREATE UNIQUE INDEX order_items3_pk
ON order_items (order_id, line_item_id) ;

CREATE UNIQUE INDEX order_items3_uk
ON order_items (order_id, product_id) ;

ALTER TABLE order_items3
ADD ( CONSTRAINT order_items3_pk PRIMARY KEY (order_id, line_item_id)
    );


CREATE or replace JSON RELATIONAL DUALITY VIEW CUST_ORDERS3
AS 
SELECT JSON {'CUSTOMER_ID' : C.CUSTOMER_ID,
             'CUST_FIRST_NAME' : C.CUST_FIRST_NAME,
             'CUST_LAST_NAME' : C.CUST_LAST_NAME,
             'CREDIT_LIMIT' : C.CREDIT_LIMIT,
             'CUST_EMAIL' : C.CUST_EMAIL,
'orders' :
[ SELECT JSON {'ORDER_ID' : O.ORDER_ID,
              'ORDER_STATUS' : O.ORDER_STATUS,
              'ORDER_TOTAL' : O.ORDER_TOTAL,
              'ORDER_DATE' : O.ORDER_DATE,
              'items' :
              [ select JSON {'ORDER_ID' : OI.ORDER_ID,
                             'LINE_ITEM_ID' : OI.LINE_ITEM_ID,
                             'PRODUCT_ID' : OI.PRODUCT_ID,
                             'UNIT_PRICE' : OI.UNIT_PRICE,
                             'QUANTITY' : OI.QUANTITY } 
                from order_items3 OI WITH INSERT UPDATE DELETE
                where OI.ORDER_ID = O.ORDER_ID ]
             }
FROM ORDERS3 O WITH INSERT UPDATE NODELETE
WHERE O.CUSTOMER_ID = C.CUSTOMER_ID ]}
FROM CUSTOMERS C WITH INSERT UPDATE DELETE;

insert into CUST_ORDERS3 (data)
values ('{
  "CUSTOMER_ID" : 9998,
  "CUST_FIRST_NAME" : "Keith",
  "CUST_LAST_NAME" : "Richards",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "keith.richards@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1001,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "ORDER_DATE" : "2023-04-13",
      "items" :
      [
	{
	  "ORDER_ID" : 1001,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1001,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}');

1 row created.

SQL> commit;

Commit complete.

SQL> select * from orders3;

  ORDER_ID ORDER_DAT ORDER_MO CUSTOMER_ID ORDER_STATUS ORDER_TOTAL SALES_REP_ID
---------- --------- -------- ----------- ------------ ----------- ------------
PROMOTION_ID
------------
      1001 13-APR-23		     9998	    10	      2000



SQL> select * from order_items3;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1001	      1       3350	 1000	       1
      1001	      2       2236	 1000	       1

SQL> select count(*) from customers where customer_id = 9998;

  COUNT(*)
----------
	 1

SQL>
--- Delete through the JDV:

update CUST_ORDERS
set data = JSON_MERGEPATCH (data,'{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	},
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 2,
	  "PRODUCT_ID" : 2236,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}')
where json_value(data, '$.CUSTOMER_ID') = 9999;

1 row updated.

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      2       2236	 1000	       1

update CUST_ORDERS
set data = JSON_MERGEPATCH (data,'{
  "CUSTOMER_ID" : 9999,
  "CUST_FIRST_NAME" : "Ron",
  "CUST_LAST_NAME" : "Wood",
  "CREDIT_LIMIT" : 2000,
  "CUST_EMAIL" : "ron.wood@beggarsbanquet.com",
  "orders" :
  [
    {
      "ORDER_ID" : 1000,
      "ORDER_STATUS" : 10,
      "ORDER_TOTAL" : 2000,
      "items" :
      [
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 1,
	  "PRODUCT_ID" : 3350,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}')
where json_value(data, '$.CUSTOMER_ID') = 9999;

1 row updated.

SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1

SQL> commit;

Commit complete.

--- Try to delete the order through the JDV: it should not work, as table ORDERS was included as NODELETE in the view:

delete CUST_ORDERS
where json_value(data, '$.CUSTOMER_ID') = 9999;

ERROR at line 1:
ORA-42692: Cannot delete from JSON Relational Duality View 'CUST_ORDERS': Error
while updating table 'ORDERS'
ORA-01407: cannot update ("OE"."ORDERS"."CUSTOMER_ID") to NULL


--- Modify the view:

CREATE or replace JSON RELATIONAL DUALITY VIEW CUST_ORDERS 
AS 
SELECT JSON {'CUSTOMER_ID' : C.CUSTOMER_ID,
             'CUST_FIRST_NAME' : C.CUST_FIRST_NAME,
             'CUST_LAST_NAME' : C.CUST_LAST_NAME,
             'CREDIT_LIMIT' : C.CREDIT_LIMIT,
             'CUST_EMAIL' : C.CUST_EMAIL,
'orders' :
[ SELECT JSON {'ORDER_ID' : O.ORDER_ID,
              'ORDER_STATUS' : O.ORDER_STATUS,
              'ORDER_TOTAL' : O.ORDER_TOTAL,
              'items' :
              [ select JSON {'ORDER_ID' : OI.ORDER_ID,
                             'LINE_ITEM_ID' : OI.LINE_ITEM_ID,
                             'PRODUCT_ID' : OI.PRODUCT_ID,
                             'UNIT_PRICE' : OI.UNIT_PRICE,
                             'QUANTITY' : OI.QUANTITY } 
                from order_items OI WITH INSERT UPDATE DELETE
                where OI.ORDER_ID = O.ORDER_ID ]
             }
FROM ORDERS O WITH INSERT UPDATE DELETE
WHERE O.CUSTOMER_ID = C.CUSTOMER_ID ]}
FROM CUSTOMERS C WITH INSERT UPDATE DELETE;

delete CUST_ORDERS
where json_value(data, '$.CUSTOMER_ID') = 9999;

1 row deleted.

SQL> select * from customers where customer_id = 9999;

no rows selected

SQL> roll
Rollback complete.
SQL> select * from customers where customer_id = 9999;

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
       9999 Ron 		 Wood

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
CUST_ADDRESS_TYP('Picadilly Circus', 'AS567', 'LONDON', 'LONDON', 'UK')

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
PHONE_LIST_TYP('123456789')

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
ENG UNITED KINGDOM			   2000

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
ron.wood@beggarsbanquet.com

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------


CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------
01-MAR-54 married	       M B: 30,000 - 49,999

CUSTOMER_ID CUST_FIRST_NAME	 CUST_LAST_NAME
----------- -------------------- --------------------
CUST_ADDRESS(STREET_ADDRESS, POSTAL_CODE, CITY, STATE_PROVINCE, COUNTRY_ID)
--------------------------------------------------------------------------------
PHONE_NUMBERS
--------------------------------------------------------------------------------
NLS NLS_TERRITORY		   CREDIT_LIMIT
--- ------------------------------ ------------
CUST_EMAIL				 ACCOUNT_MGR_ID
---------------------------------------- --------------
CUST_GEO_LOCATION(SDO_GTYPE, SDO_SRID, SDO_POINT(X, Y, Z), SDO_ELEM_INFO, SDO_OR
--------------------------------------------------------------------------------
DATE_OF_B MARITAL_STATUS       G INCOME_LEVEL
--------- -------------------- - --------------------


SQL>