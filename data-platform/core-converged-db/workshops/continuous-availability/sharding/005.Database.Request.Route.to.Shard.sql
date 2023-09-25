Database Request Rout to Shard

Routing Queries and DMLs Directly to Shards

Login to the catalog host, switch to oracle user.

For single-shard queries, direct routing to a shard with a given sharding_key.

. ./cata.sh
sqlplus app_schema/app_schema@'(description=(address=(protocol=tcp)(host=cata)(port=1522))(connect_data=(service_name=oltp_rw_srvc.orasdb.oradbcloud)(region=region1)(SHARDING_KEY=tom.edwards@y.bogus)))'

[oracle@cata ~]$ sqlplus app_schema/app_schema@'(description=(address=(protocol=tcp)(host=cata)(port=1522))(connect_data=(service_name=oltp_rw_srvc.orasdb.oradbcloud)(region=region1)(SHARDING_KEY=tom.edwards@y.bogus)))'

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Nov 18 11:10:43 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Thu Nov 18 2021 10:45:45 +00:00

Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> select instance_name from v$instance;

INSTANCE_NAME
----------------
shd1

You have been connected to shard1: this is because tom.edwards@y.bogus hash value corresponds to shard1 !!!

SQL> INSERT INTO Customers (CustId, FirstName, LastName, CustProfile, Class, Geo, Passwd) VALUES ('tom.edwards@y.bogus', 'Tom', 'Edwards', NULL, 'Gold', 'east', hextoraw('8d1c00e'));

1 row created.

SQL> commit;

Commit complete.

Select from the customer table. You can see there is one record which you just insert in the table.

SQL> select * from customers where custid like '%y.bogus';

CUSTID
------------------------------------------------------------
FIRSTNAME
------------------------------------------------------------
LASTNAME						     CLASS	GEO
------------------------------------------------------------ ---------- --------
CUSTPROFILE
--------------------------------------------------------------------------------
PASSWD
--------------------------------------------------------------------------------
tom.edwards@y.bogus
Tom
Edwards 						     Gold	east

CUSTID
------------------------------------------------------------
FIRSTNAME
------------------------------------------------------------
LASTNAME						     CLASS	GEO
------------------------------------------------------------ ---------- --------
CUSTPROFILE
--------------------------------------------------------------------------------
PASSWD
--------------------------------------------------------------------------------

08D1C00E

Connect to a shard with another shard key.

sqlplus app_schema/app_schema@'(description=(address=(protocol=tcp)(host=cata)(port=1522))(connect_data=(service_name=oltp_rw_srvc.orasdb.oradbcloud)(region=region1)(SHARDING_KEY=james.parker@y.bogus)))'

[oracle@cata ~]$ sqlplus app_schema/app_schema@'(description=(address=(protocol=tcp)(host=cata)(port=1522))(connect_data=(service_name=oltp_rw_srvc.orasdb.oradbcloud)(region=region1)(SHARDING_KEY=james.parker@y.bogus)))'

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Nov 18 11:13:58 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Thu Nov 18 2021 10:45:45 +00:00

Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> select instance_name from v$instance;

INSTANCE_NAME
----------------
shd2

SQL> INSERT INTO Customers (CustId, FirstName, LastName, CustProfile, Class, Geo, Passwd) VALUES ('james.parker@y.bogus', 'James', 'Parker', NULL, 'Gold', 'west', hextoraw('9a3b00c'));

1 row created.

SQL> commit;

Commit complete.

SQL> select * from customers where custid like '%y.bogus';

CUSTID
------------------------------------------------------------
FIRSTNAME
------------------------------------------------------------
LASTNAME						     CLASS	GEO
------------------------------------------------------------ ---------- --------
CUSTPROFILE
--------------------------------------------------------------------------------
PASSWD
--------------------------------------------------------------------------------
james.parker@y.bogus
James
Parker							     Gold	west

CUSTID
------------------------------------------------------------
FIRSTNAME
------------------------------------------------------------
LASTNAME						     CLASS	GEO
------------------------------------------------------------ ---------- --------
CUSTPROFILE
--------------------------------------------------------------------------------
PASSWD
--------------------------------------------------------------------------------

09A3B00C


Routing Queries and DMLs by Proxy

Connect to the shardcatalog (coordinator database) using the GDS$CATALOG service (from catalog or any shard host):

Select records from customers table. You can see all the records are selected.

[oracle@cata ~]$ sqlplus app_schema/app_schema@cata:1522/GDS\$CATALOG.oradbcloud

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Nov 18 11:22:30 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Thu Nov 18 2021 11:22:24 +00:00

Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> select instance_name from v$instance;

INSTANCE_NAME
----------------
cata

SQL> select custid from customers where custid like '%y.bogus';

CUSTID
------------------------------------------------------------
tom.edwards@y.bogus
james.parker@y.bogus

Multi-Shard Query

A multi-shard query is a query that must scan data from more than one shard, and the processing on each shard is independent of any other shard.

A multi-shard query maps to more than one shard and the coordinator might need to do some processing before sending the result to the client. 
The inline query block is mapped to every shard just as a remote mapped query block. 
The coordinator performs further aggregation and GROUP BY on top of the result set from all shards. The unit of execution on every shard is the inline query block.

sqlplus app_schema/app_schema@catapdb

Let’s run a multi-shard query which joins sharded and duplicated table (join on non sharding key) to get the fast moving products (qty sold > 10). 
The output that you will observe will be different (due to data load randomization).

set echo on
column name format a40
explain plan for SELECT name, SUM(qty) qtysold FROM lineitems l, products p WHERE l.productid = p.productid GROUP BY name HAVING sum(qty) > 10 ORDER BY qtysold desc;

SQL> set echo off
SQL> select * from table(dbms_xplan.display());

PLAN_TABLE_OUTPUT
--------------------------------------------------------------------------------
Plan hash value: 2044377012

--------------------------------------------------------------------------------
------------------------

| Id  | Operation	   | Name	       | Rows  | Bytes | Cost (%CPU)| Ti
me     | Inst	|IN-OUT|

--------------------------------------------------------------------------------
------------------------


PLAN_TABLE_OUTPUT
--------------------------------------------------------------------------------
|   0 | SELECT STATEMENT   |		       |     1 |    79 |     4	(50)| 00
:00:01 |	|      |

|   1 |  SORT ORDER BY	   |		       |     1 |    79 |     4	(50)| 00
:00:01 |	|      |

|*  2 |   HASH GROUP BY    |		       |     1 |    79 |     4	(50)| 00
:00:01 |	|      |

|   3 |    VIEW 	   | VW_SHARD_372F2D25 |     1 |    79 |     4	(50)| 00
:00:01 |	|      |

PLAN_TABLE_OUTPUT
--------------------------------------------------------------------------------

|   4 |     SHARD ITERATOR |		       |       |       |	    |
       |	|      |

|   5 |      REMOTE	   |		       |       |       |	    |
       | ORA_S~ | R->S |

--------------------------------------------------------------------------------
------------------------



PLAN_TABLE_OUTPUT
--------------------------------------------------------------------------------
Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(SUM("ITEM_1")>10)

Remote SQL Information (identified by operation id):
----------------------------------------------------

   5 - EXPLAIN PLAN INTO PLAN_TABLE@! FOR SELECT SUM("A2"."QTY"),"A1"."NAME" FRO
M "LINEITEMS"


PLAN_TABLE_OUTPUT
--------------------------------------------------------------------------------
       "A2","PRODUCTS" "A1" WHERE "A2"."PRODUCTID"="A1"."PRODUCTID" GROUP BY "A1
"."NAME" /*

       coord_sql_id=g415vyfr9rg2a */  (accessing 'ORA_SHARD_POOL@ORA_MULTI_TARGE
T' )



25 rows selected.

SQL> SELECT name, SUM(qty) qtysold FROM lineitems l, products p WHERE l.productid = p.productid GROUP BY name HAVING sum(qty) > 10 ORDER BY qtysold desc;

NAME					    QTYSOLD
---------------------------------------- ----------
Fuel tank				       1823
Thermostat				       1772
Distributor				       1734
Radiator				       1718
Fastener				       1704
Center console				       1698
Master cylinder 			       1685
seal					       1677
Starter motor				       1672
Battery 				       1607
Engine block				       1558
[...]
NAME					    QTYSOLD
---------------------------------------- ----------
Pinion bearing					722
Ammeter 					721
Power steering					717
Oil pump					715
Suspension link and bolt			705
Engine shake damper and vibration absorb	691
er

Coil wire					685

469 rows selected.

Let’s run a multi-shard query which runs an IN subquery to get orders that includes product with price > 900000.

set echo on
column name format a20
explain plan for SELECT COUNT(orderid) FROM orders o WHERE orderid IN (SELECT orderid FROM lineitems l, products p WHERE l.productid = p.productid AND o.custid = l.custid AND p.lastprice > 900000);

set echo off lines 120
select * from table(dbms_xplan.display());

PLAN_TABLE_OUTPUT
------------------------------------------------------------------------------------------------------------------------
Plan hash value: 2403723386

-------------------------------------------------------------------------------------------------------
| Id  | Operation	  | Name	      | Rows  | Bytes | Cost (%CPU)| Time     | Inst   |IN-OUT|
-------------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT  |		      |     1 |    13 |     2	(0)| 00:00:01 |        |      |
|   1 |  SORT AGGREGATE   |		      |     1 |    13 | 	   |	      |        |      |
|   2 |   VIEW		  | VW_SHARD_72AE2D8F |     1 |    13 |     2	(0)| 00:00:01 |        |      |
|   3 |    SHARD ITERATOR |		      |       |       | 	   |	      |        |      |
|   4 |     REMOTE	  |		      |       |       | 	   |	      | ORA_S~ | R->S |
-------------------------------------------------------------------------------------------------------

PLAN_TABLE_OUTPUT
------------------------------------------------------------------------------------------------------------------------

Remote SQL Information (identified by operation id):
----------------------------------------------------

   4 - EXPLAIN PLAN INTO PLAN_TABLE@! FOR SELECT COUNT(*) FROM "ORDERS" "A1" WHERE
       "A1"."ORDERID"=ANY (SELECT "A3"."ORDERID" FROM "LINEITEMS" "A3","PRODUCTS" "A2" WHERE
       "A3"."PRODUCTID"="A2"."PRODUCTID" AND "A1"."CUSTID"="A3"."CUSTID" AND "A2"."LASTPRICE">900000)
       /* coord_sql_id=ff5nrpzr2ddnf */  (accessing 'ORA_SHARD_POOL@ORA_MULTI_TARGET' )


20 rows selected.

SQL> SELECT COUNT(orderid) FROM orders o WHERE orderid IN (SELECT orderid FROM lineitems l, products p WHERE l.productid = p.productid AND o.custid = l.custid AND p.lastprice > 900000);

COUNT(ORDERID)
--------------
	  7860

Let’s run a multi-shard query that calculates customer distribution based on the number of orders placed. Please wait several minutes for the results return.

set echo off
column name format a40
explain plan for SELECT ordercount, COUNT(*) as custdist
    FROM (SELECT c.custid, COUNT(orderid) ordercount
           FROM customers c LEFT OUTER JOIN orders o
           ON c.custid = o.custid AND
           orderdate BETWEEN sysdate-4 AND sysdate GROUP BY c.custid)
    GROUP BY ordercount
    ORDER BY custdist desc, ordercount desc;

select * from table(dbms_xplan.display());


PLAN_TABLE_OUTPUT
------------------------------------------------------------------------------------------------------------------------
Plan hash value: 313106859

----------------------------------------------------------------------------------------------------------
| Id  | Operation	     | Name		 | Rows  | Bytes | Cost (%CPU)| Time	 | Inst   |IN-OUT|
----------------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT     |			 |     1 |    13 |     5  (20)| 00:00:01 |	  |	 |
|   1 |  SORT ORDER BY	     |			 |     1 |    13 |     5  (20)| 00:00:01 |	  |	 |
|   2 |   HASH GROUP BY      |			 |     1 |    13 |     5  (20)| 00:00:01 |	  |	 |
|   3 |    VIEW 	     |			 |     1 |    13 |     5  (20)| 00:00:01 |	  |	 |
|   4 |     HASH GROUP BY    |			 |     1 |    45 |     5  (20)| 00:00:01 |	  |	 |
|   5 |      VIEW	     | VW_SHARD_28C476E6 |     1 |    45 |     5  (20)| 00:00:01 |	  |	 |

PLAN_TABLE_OUTPUT
------------------------------------------------------------------------------------------------------------------------
|   6 |       SHARD ITERATOR |			 |	 |	 |	      | 	 |	  |	 |
|   7 |        REMOTE	     |			 |	 |	 |	      | 	 | ORA_S~ | R->S |
----------------------------------------------------------------------------------------------------------

Remote SQL Information (identified by operation id):
----------------------------------------------------

   7 - EXPLAIN PLAN INTO PLAN_TABLE@! FOR SELECT COUNT("A1"."ORDERID"),"A2"."CUSTID" FROM
       "CUSTOMERS" "A2","ORDERS" "A1" WHERE "A2"."CUSTID"="A1"."CUSTID"(+) AND
       "A1"."ORDERDATE"(+)>=CAST(SYSDATE@!-4 AS TIMESTAMP) AND "A1"."ORDERDATE"(+)<=CAST(SYSDATE@! AS
       TIMESTAMP) GROUP BY "A2"."CUSTID" /* coord_sql_id=972ysbafqgcav */  (accessing

PLAN_TABLE_OUTPUT
------------------------------------------------------------------------------------------------------------------------
       'ORA_SHARD_POOL@ORA_MULTI_TARGET' )


Note
-----
   - dynamic statistics used: dynamic sampling (level=2)

28 rows selected.

SQL> SELECT ordercount, COUNT(*) as custdist
    FROM (SELECT c.custid, COUNT(orderid) ordercount
           FROM customers c LEFT OUTER JOIN orders o
           ON c.custid = o.custid AND
           orderdate BETWEEN sysdate-4 AND sysdate GROUP BY c.custid)
    GROUP BY ordercount
    ORDER BY custdist desc, ordercount desc;

ORDERCOUNT   CUSTDIST
---------- ----------
	 1	58516
	 2	21298
	 3	 8151
	 4	 3335
	 5	 1468
	 6	  752
	 7	  417
	 8	  242
	 9	  160
	10	  120
	11	   69

ORDERCOUNT   CUSTDIST
---------- ----------
	12	   67
	13	   50
	16	   27
	15	   27
	14	   18
	18	   16
	17	   13
	19	   11
	20	   10
	21	    7
	32	    6

ORDERCOUNT   CUSTDIST
---------- ----------
	 0	    6
	22	    5
	24	    4
	38	    3
	27	    3
	26	    3
	25	    3
	47	    2
	42	    2
	40	    2
	37	    2

ORDERCOUNT   CUSTDIST
---------- ----------
	28	    2
	23	    2
	59	    1
	58	    1
	54	    1
	51	    1
	46	    1
	41	    1
	39	    1
	36	    1
	35	    1

ORDERCOUNT   CUSTDIST
---------- ----------
	33	    1
	30	    1
	29	    1

47 rows selected.

SQL>




