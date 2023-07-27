sqlplus soe/soe@myoracledb:1521/orclpdb1

drop table OI_JSON_ORDERS purge;
drop table OI_JSON_ORDER_ITEMS purge;

create table OI_JSON_ORDERS
(
ID number(12),
O_JSON VARCHAR2(4000),
CONSTRAINT O_JSON_insert_pk primary Key (id),
CONSTRAINT O_JSON_check CHECK (O_JSON IS JSON)
);

alter session enable parallel DML;
alter session force parallel query parallel 2;
set timing on

insert /*+ APPEND NOLOGGING */ 
into OI_JSON_ORDERS (id,O_JSON)
select O.order_id,
       json_object (
	'ORDER_ID' value O.ORDER_ID,
	'ORDER_DATE' value O.ORDER_DATE,
	'ORDER_MODE' value O.ORDER_MODE,
	'CUSTOMER_ID' value O.CUSTOMER_ID,
	'ORDER_STATUS' value O.ORDER_STATUS,
	'ORDER_TOTAL' value O.ORDER_TOTAL,
	'SALES_REP_ID' value O.SALES_REP_ID,
	'PROMOTION_ID' value O.PROMOTION_ID,
	'WAREHOUSE_ID' value O.WAREHOUSE_ID,
	'DELIVERY_TYPE' value O.DELIVERY_TYPE,
	'COST_OF_DELIVERY' value O.COST_OF_DELIVERY,
    'WAIT_TILL_ALL_AVAILABLE' value O.WAIT_TILL_ALL_AVAILABLE,
    'DELIVERY_ADDRESS_ID' value O.DELIVERY_ADDRESS_ID,
    'CUSTOMER_CLASS' value O.CUSTOMER_CLASS,
    'CARD_ID' value O.CARD_ID,
    'INVOICE_ADDRESS_ID' value O.INVOICE_ADDRESS_ID
    ) as mijson
from orders O;

1429790 rows created.

Elapsed: 00:00:33.64
SQL> SQL> commit;

Commit complete.

Elapsed: 00:00:01.50

select W.WAREHOUSE_NAME, sum(O.ORDER_TOTAL)
from ORDERS O,
WAREHOUSES W
where W.WAREHOUSE_ID =  O.WAREHOUSE_ID
and     W.warehouse_name in  ('McsRxsWjRxXMFDcobjhEIDdEsO','5eH6XK38SRmNEZCUg43EDIjDICDhbV','PLlypy')
group by W.WAREHOUSE_NAME
order by 1
/

WAREHOUSE_NAME			    SUM(O.ORDER_TOTAL)
----------------------------------- ------------------
5eH6XK38SRmNEZCUg43EDIjDICDhbV		       7190505
McsRxsWjRxXMFDcobjhEIDdEsO		       7368607
PLlypy					       7197962

Elapsed: 00:00:00.29

select W.WAREHOUSE_NAME, sum(to_number(json_value (OI.O_JSON, '$.ORDER_TOTAL'))) as TOTAL
from    OI_JSON_ORDERS OI,
        WAREHOUSES W
where   W.WAREHOUSE_ID = json_value (OI.O_JSON, '$.WAREHOUSE_ID')
and     W.warehouse_name in  ('McsRxsWjRxXMFDcobjhEIDdEsO','5eH6XK38SRmNEZCUg43EDIjDICDhbV','PLlypy')
group by W.WAREHOUSE_NAME
order by 1;

WAREHOUSE_NAME				 TOTAL
----------------------------------- ----------
5eH6XK38SRmNEZCUg43EDIjDICDhbV	       7190505
McsRxsWjRxXMFDcobjhEIDdEsO	       7368607
PLlypy				       7197962

Elapsed: 00:00:12.84

create table OI_JSON_ORDER_ITEMS
(
ID number(12),
order_date DATE NOT NULL,
OI_json VARCHAR2(4000),
CONSTRAINT oi_json_insert_pk primary Key (id),
CONSTRAINT OI_json_check CHECK (OI_json IS JSON)
)
PARTITION BY RANGE (order_date)
INTERVAL(NUMTOYMINTERVAL(1,'MONTH'))
( 
    PARTITION OIJSON_P0 VALUES LESS THAN (TO_DATE('2007-02-01', 'YYYY-MM-DD'))
);

alter table OI_JSON_ORDER_ITEMS no inmemory;

alter session enable parallel DML;
alter session force parallel query parallel 2;
set timing on

insert /*+ APPEND NOLOGGING */ 
into OI_JSON_ORDER_ITEMS (id,order_date,OI_json)
select O.order_id, O.order_date,
       json_object (
	'ORDER_ID' value O.ORDER_ID,
	'ORDER_DATE' value O.ORDER_DATE,
	'ORDER_MODE' value O.ORDER_MODE,
	'CUSTOMER_ID' value O.CUSTOMER_ID,
	'ORDER_STATUS' value O.ORDER_STATUS,
	'ORDER_TOTAL' value O.ORDER_TOTAL,
	'SALES_REP_ID' value O.SALES_REP_ID,
	'PROMOTION_ID' value O.PROMOTION_ID,
	'WAREHOUSE_ID' value O.WAREHOUSE_ID,
	'DELIVERY_TYPE' value O.DELIVERY_TYPE,
	'COST_OF_DELIVERY' value O.COST_OF_DELIVERY,
    'WAIT_TILL_ALL_AVAILABLE' value O.WAIT_TILL_ALL_AVAILABLE,
    'DELIVERY_ADDRESS_ID' value O.DELIVERY_ADDRESS_ID,
    'CUSTOMER_CLASS' value O.CUSTOMER_CLASS,
    'CARD_ID' value O.CARD_ID,
    'INVOICE_ADDRESS_ID' value O.INVOICE_ADDRESS_ID,
    'ITEMS' value json_arrayagg (
        json_object (
         'ORDER_ID' value  OI.ORDER_ID,
         'LINE_ITEM_ID' value  OI.LINE_ITEM_ID,
         'PRODUCT_ID' value  OI.PRODUCT_ID,
         'UNIT_PRICE' value  OI.UNIT_PRICE,
         'QUANTITY' value  OI.QUANTITY,
         'DISPATCH_DATE' value  OI.DISPATCH_DATE,
         'RETURN_DATE' value  OI.RETURN_DATE,
         'GIFT_WRAP' value  OI.GIFT_WRAP,
         'CONDITION' value  OI.CONDITION,
         'SUPPLIER_ID' value  OI.SUPPLIER_ID,
         'ESTIMATED_DELIVERY' value  OI.ESTIMATED_DELIVERY
    )
    )
    ) as mijson
from orders O, 
    order_items OI
where O.order_id = OI.order_id(+)
group by 
O.ORDER_ID,
O.ORDER_DATE,
O.ORDER_MODE,
O.CUSTOMER_ID,
O.ORDER_STATUS,
O.ORDER_TOTAL,
O.SALES_REP_ID,
O.PROMOTION_ID,
O.WAREHOUSE_ID,
O.DELIVERY_TYPE,
O.COST_OF_DELIVERY,
O.WAIT_TILL_ALL_AVAILABLE,
O.DELIVERY_ADDRESS_ID,
O.CUSTOMER_CLASS,
O.CARD_ID,
O.INVOICE_ADDRESS_ID;


1429790 rows created.

Elapsed: 00:01:47.06
SQL> SQL> commit;

Commit complete.

Elapsed: 00:00:00.13

exit

--- Performance tests !!!

--- Lookup on ORDER_DATE and CUSTOMER_ID

-- Customer_ID = 733116
-- ORDER_DATE = 24-FEB-09

sqlplus soe/soe@myoracledb:1521/ORCLPDB1

set timing on

alter table orders no inmemory;
alter table order_items no inmemory;

select sum(OI.unit_price)
from orders O, order_items OI
where O.customer_id = 733116
and trunc(O.order_date) = to_date('24-FEB-09','DD-MON-RR')
and O.order_id = OI.order_id;

SUM(OI.UNIT_PRICE)
------------------
	      5146

Elapsed: 00:00:01.16
SQL>

set autotrace traceonly explain statistics

select sum(OI.unit_price)
from orders O, order_items OI
where O.customer_id = 733116
and trunc(O.order_date) = to_date('24-FEB-09','DD-MON-RR')
and O.order_id = OI.order_id;


set autotrace off


select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

SUM(ARR.UNIT_PRICE)
-------------------
	       5146

Elapsed: 00:00:03.25


set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');


Execution Plan
----------------------------------------------------------
Plan hash value: 1435571113

--------------------------------------------------------------------------------
-------------------------------

| Id  | Operation		| Name		      | Rows  | Bytes | Cost (%C
PU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
-------------------------------

|   0 | SELECT STATEMENT	|		      |     1 |  1124 |   468K
(3)| 00:00:19 |       |       |

|   1 |  SORT AGGREGATE 	|		      |     1 |  1124 |
   |	      |       |       |

|   2 |   NESTED LOOPS		|		      |  1167K|  1251M|   468K
(3)| 00:00:19 |       |       |

|   3 |    PARTITION RANGE ALL	|		      | 14298 |    15M| 69606
(1)| 00:00:03 |     1 |1048575|

|*  4 |     TABLE ACCESS FULL	| OI_JSON_ORDER_ITEMS | 14298 |    15M| 69606
(1)| 00:00:03 |     1 |1048575|

|*  5 |    JSONTABLE EVALUATION |		      |       |       |
   |	      |       |       |

--------------------------------------------------------------------------------
-------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   4 - filter(TO_NUMBER(JSON_VALUE("OIJ"."OI_JSON" FORMAT JSON , '$.CUSTOMER_ID'
 RETURNING

	      VARCHAR2(4000) NULL ON ERROR))=733116)
   5 - filter(TRUNC("P"."ORDER_DATE")=TO_DATE('24-FEB-09','DD-MON-RR'))


Statistics
----------------------------------------------------------
	 44  recursive calls
	  0  db block gets
     252515  consistent gets
     252160  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  3  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

exit

sqlplus soe/soe@myoracledb:1521/ORCLPDB1

set autotrace traceonly explain statistics

--- WE should use RELATIONAL ORDER_DATE to leverage partition pruning !!!

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and OIJ.ORDER_DATE between to_date('24-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

SUM(ARR.UNIT_PRICE)
-------------------
	       5146

Elapsed: 00:00:00.06

Execution Plan
----------------------------------------------------------
Plan hash value: 229940177

--------------------------------------------------------------------------------
-----------------------------------

| Id  | Operation		    | Name		  | Rows  | Bytes | Cost
 (%CPU)| Time	  | Pstart| Pstop |

--------------------------------------------------------------------------------
-----------------------------------

|   0 | SELECT STATEMENT	    |			  |	1 |  1130 | 6982
5   (1)| 00:00:03 |	  |	  |

|   1 |  SORT AGGREGATE 	    |			  |	1 |  1130 |
       |	  |	  |	  |

|*  2 |   FILTER		    |			  |	  |	  |
       |	  |	  |	  |

|   3 |    NESTED LOOPS 	    |			  | 64991 |    70M| 6982
5   (1)| 00:00:03 |	  |	  |

|   4 |     PARTITION RANGE ITERATOR|			  |	8 |  9024 | 6960
6   (1)| 00:00:03 |   KEY |   KEY |

|*  5 |      TABLE ACCESS FULL	    | OI_JSON_ORDER_ITEMS |	8 |  9024 | 6960
6   (1)| 00:00:03 |   KEY |   KEY |

|   6 |     JSONTABLE EVALUATION    |			  |	  |	  |
       |	  |	  |	  |

--------------------------------------------------------------------------------
-----------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_DATE('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS')>=TO_DATE('24-
FEB-09

	      00:00:00','DD-MON-RR HH24:MI:SS'))
   5 - filter(TO_NUMBER(JSON_VALUE("OIJ"."OI_JSON" FORMAT JSON , '$.CUSTOMER_ID'
 RETURNING VARCHAR2(4000)

	      NULL ON ERROR))=733116 AND "OIJ"."ORDER_DATE"<=TO_DATE('24-FEB-09
23:59:59','DD-MON-RR HH24:MI:SS') AND

	      "OIJ"."ORDER_DATE">=TO_DATE('24-FEB-09 00:00:00','DD-MON-RR HH24:M
I:SS'))



Statistics
----------------------------------------------------------
	 21  recursive calls
	  0  db block gets
       3660  consistent gets
       3646  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

exit

-- We can index a json field to speed-up the query !!!
--- We would tipically index CUSTOMER_ID !!!

sqlplus soe/soe@myoracledb:1521/ORCLPDB1
set timing on

create index I_CUST_ID  on
OI_JSON_ORDER_ITEMS 
(
    json_value (OI_JSON, '$.CUSTOMER_ID'  returning NUMBER(12) error on error null on empty)
) LOCAL;

Index created.

Elapsed: 00:00:05.14

exec dbms_stats.gather_index_stats ('SOE','I_CUST_ID')

SQL> 

--- Repeat the same query !!!

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CUSTOMER_ID'  returning NUMBER(12) error on error null on empty) = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

SUM(ARR.UNIT_PRICE)
-------------------
	       5146

Elapsed: 00:00:00.01


set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CUSTOMER_ID'  returning NUMBER(12) error on error null on empty) = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

Execution Plan
----------------------------------------------------------
Plan hash value: 1296896600

--------------------------------------------------------------------------------
----------------------------------------------------

| Id  | Operation				     | Name		   | Row
s  | Bytes | Cost (%CPU)| Time	   | Pstart| Pstop |

--------------------------------------------------------------------------------
----------------------------------------------------

|   0 | SELECT STATEMENT			     |			   |
 1 |  1136 |   404K  (3)| 00:00:16 |	   |	   |

|   1 |  SORT AGGREGATE 			     |			   |
 1 |  1136 |		|	   |	   |	   |

|   2 |   NESTED LOOPS				     |			   |  11
67K|  1265M|   404K  (3)| 00:00:16 |	   |	   |

|   3 |    PARTITION RANGE ALL			     |			   | 142
98 |	15M|  5785   (1)| 00:00:01 |	 1 |1048575|

|   4 |     TABLE ACCESS BY LOCAL INDEX ROWID BATCHED| OI_JSON_ORDER_ITEMS | 142
98 |	15M|  5785   (1)| 00:00:01 |	 1 |1048575|

|*  5 |      INDEX RANGE SCAN			     | I_CUST_ID	   |  57
19 |	   |	65   (0)| 00:00:01 |	 1 |1048575|

|*  6 |    JSONTABLE EVALUATION 		     |			   |
   |	   |		|	   |	   |	   |

--------------------------------------------------------------------------------
----------------------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   5 - access(JSON_VALUE("OI_JSON" FORMAT JSON , '$.CUSTOMER_ID' RETURNING NUMBE
R(12,0) ERROR ON ERROR NULL ON

	      EMPTY)=733116)
   6 - filter(TRUNC("P"."ORDER_DATE")=TO_DATE('24-FEB-09','DD-MON-RR'))


Statistics
----------------------------------------------------------
	 61  recursive calls
	  0  db block gets
	194  consistent gets
	  2  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

set autotrace traceonly explain statistics

select /*+ INDEX (OIJ I_CUST_ID) */ sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CUSTOMER_ID'  returning NUMBER(12) error on error null on empty) = 733116
and OIJ.ORDER_DATE between to_date('24-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

Execution Plan
----------------------------------------------------------
Plan hash value: 3101916861

--------------------------------------------------------------------------------
-----------------------------------------------------

| Id  | Operation				      | Name		    | Ro
ws  | Bytes | Cost (%CPU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
-----------------------------------------------------

|   0 | SELECT STATEMENT			      | 		    |
  1 |  1134 |	240   (2)| 00:00:01 |	    |	    |

|   1 |  SORT AGGREGATE 			      | 		    |
  1 |  1134 |		 |	    |	    |	    |

|*  2 |   FILTER				      | 		    |
    |	    |		 |	    |	    |	    |

|   3 |    NESTED LOOPS 			      | 		    | 64
991 |	 70M|	240   (2)| 00:00:01 |	    |	    |

|   4 |     PARTITION RANGE ITERATOR		      | 		    |
  8 |  9056 |	 21  (15)| 00:00:01 |	KEY |	KEY |

|*  5 |      TABLE ACCESS BY LOCAL INDEX ROWID BATCHED| OI_JSON_ORDER_ITEMS |
  8 |  9056 |	 21  (15)| 00:00:01 |	KEY |	KEY |

|*  6 |       INDEX RANGE SCAN			      | I_CUST_ID	    |  5
719 |	    |	 65   (0)| 00:00:01 |	KEY |	KEY |

|   7 |     JSONTABLE EVALUATION		      | 		    |
    |	    |		 |	    |	    |	    |

--------------------------------------------------------------------------------
-----------------------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_DATE('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS')>=TO_DATE('24-
FEB-09 00:00:00','DD-MON-RR HH24:MI:SS'))

   5 - filter("OIJ"."ORDER_DATE"<=TO_DATE('24-FEB-09 23:59:59','DD-MON-RR HH24:M
I:SS') AND

	      "OIJ"."ORDER_DATE">=TO_DATE('24-FEB-09 00:00:00','DD-MON-RR HH24:M
I:SS'))

   6 - access(JSON_VALUE("OI_JSON" FORMAT JSON , '$.CUSTOMER_ID' RETURNING NUMBE
R(12,0) ERROR ON ERROR NULL ON EMPTY)=733116)



Statistics
----------------------------------------------------------
	 12  recursive calls
	  4  db block gets
	 15  consistent gets
	  0  physical reads
	868  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

exit



--- Partition the table on a JSON attribute

sqlplus soe/soe@myoracledb:1521/ORCLPDB1

CREATE TABLE OI_JSON_ORDER_ITEMS_PART
(id NUMBER(12) NOT NULL PRIMARY KEY,
   OI_JSON VARCHAR2(4000),
   ORDER_DATE DATE GENERATED ALWAYS AS
     (json_value (OI_JSON, '$.ORDER_DATE' RETURNING DATE))
)
PARTITION BY RANGE (ORDER_DATE) INTERVAL(NUMTOYMINTERVAL(1, 'MONTH'))
  (
    PARTITION OIJSONPART_P0 VALUES LESS THAN (TO_DATE('2007-02-01', 'YYYY-MM-DD'))
  );

desc OI_JSON_ORDER_ITEMS_PART

alter table OI_JSON_ORDER_ITEMS_PART no inmemory;
alter session enable parallel DML;
alter session force parallel query parallel 2;

set timing on

insert /*+ APPEND NOLOGGING */ 
into OI_JSON_ORDER_ITEMS_PART (id,OI_json)
select O.order_id, 
       json_object (
	'ORDER_ID' value O.ORDER_ID,
	'ORDER_DATE' value O.ORDER_DATE,
	'ORDER_MODE' value O.ORDER_MODE,
	'CUSTOMER_ID' value O.CUSTOMER_ID,
	'ORDER_STATUS' value O.ORDER_STATUS,
	'ORDER_TOTAL' value O.ORDER_TOTAL,
	'SALES_REP_ID' value O.SALES_REP_ID,
	'PROMOTION_ID' value O.PROMOTION_ID,
	'WAREHOUSE_ID' value O.WAREHOUSE_ID,
	'DELIVERY_TYPE' value O.DELIVERY_TYPE,
	'COST_OF_DELIVERY' value O.COST_OF_DELIVERY,
    'WAIT_TILL_ALL_AVAILABLE' value O.WAIT_TILL_ALL_AVAILABLE,
    'DELIVERY_ADDRESS_ID' value O.DELIVERY_ADDRESS_ID,
    'CUSTOMER_CLASS' value O.CUSTOMER_CLASS,
    'CARD_ID' value O.CARD_ID,
    'INVOICE_ADDRESS_ID' value O.INVOICE_ADDRESS_ID,
    'ITEMS' value json_arrayagg (
        json_object (
         'ORDER_ID' value  OI.ORDER_ID,
         'LINE_ITEM_ID' value  OI.LINE_ITEM_ID,
         'PRODUCT_ID' value  OI.PRODUCT_ID,
         'UNIT_PRICE' value  OI.UNIT_PRICE,
         'QUANTITY' value  OI.QUANTITY,
         'DISPATCH_DATE' value  OI.DISPATCH_DATE,
         'RETURN_DATE' value  OI.RETURN_DATE,
         'GIFT_WRAP' value  OI.GIFT_WRAP,
         'CONDITION' value  OI.CONDITION,
         'SUPPLIER_ID' value  OI.SUPPLIER_ID,
         'ESTIMATED_DELIVERY' value  OI.ESTIMATED_DELIVERY
    )
    )
    ) as mijson
from orders O, 
    order_items OI
where O.order_id = OI.order_id(+)
group by 
O.ORDER_ID,
O.ORDER_DATE,
O.ORDER_MODE,
O.CUSTOMER_ID,
O.ORDER_STATUS,
O.ORDER_TOTAL,
O.SALES_REP_ID,
O.PROMOTION_ID,
O.WAREHOUSE_ID,
O.DELIVERY_TYPE,
O.COST_OF_DELIVERY,
O.WAIT_TILL_ALL_AVAILABLE,
O.DELIVERY_ADDRESS_ID,
O.CUSTOMER_CLASS,
O.CARD_ID,
O.INVOICE_ADDRESS_ID;

commit;

exit
sqlplus soe/soe@myoracledb:1521/ORCLPDB1
set timing on

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');


select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and OIJ.ORDER_DATE between to_date('24-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

exit


--- Let's modify the query to use CARD_ID instead of customer id:

sqlplus soe/soe@myoracledb:1521/ORCLPDB1
set timing on


select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CARD_ID'  returning NUMBER(12) error on error null on empty) = 1465982
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

SUM(ARR.UNIT_PRICE)
-------------------
	       5146

Elapsed: 00:00:07.22

set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CARD_ID'  returning NUMBER(12) error on error null on empty) = 1465982
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

Elapsed: 00:00:06.28

Execution Plan
----------------------------------------------------------
Plan hash value: 1435571113

--------------------------------------------------------------------------------
-------------------------------

| Id  | Operation		| Name		      | Rows  | Bytes | Cost (%C
PU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
-------------------------------

|   0 | SELECT STATEMENT	|		      |     1 |  1124 |   468K
(3)| 00:00:19 |       |       |

|   1 |  SORT AGGREGATE 	|		      |     1 |  1124 |
   |	      |       |       |

|   2 |   NESTED LOOPS		|		      |  1167K|  1251M|   468K
(3)| 00:00:19 |       |       |

|   3 |    PARTITION RANGE ALL	|		      | 14298 |    15M| 69598
(1)| 00:00:03 |     1 |1048575|

|*  4 |     TABLE ACCESS FULL	| OI_JSON_ORDER_ITEMS | 14298 |    15M| 69598
(1)| 00:00:03 |     1 |1048575|

|*  5 |    JSONTABLE EVALUATION |		      |       |       |
   |	      |       |       |

--------------------------------------------------------------------------------
-------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   4 - filter(JSON_VALUE("OI_JSON" FORMAT JSON , '$.CARD_ID' RETURNING NUMBER(12
,0) ERROR ON ERROR

	      NULL ON EMPTY)=1465982)
   5 - filter(TRUNC("P"."ORDER_DATE")=TO_DATE('24-FEB-09','DD-MON-RR'))


Statistics
----------------------------------------------------------
	 66  recursive calls
	  0  db block gets
     252357  consistent gets
     252160  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

=> We get a FTS plan again, as CARD_ID is not indexed.

-- As we don't know which field of the JSON column will be used in the predicate, we choose a SEARCH INDEX !!!

set autotrace off

create search index I_JSON_SEARCH on OI_JSON_ORDER_ITEMS(OI_JSON) for JSON;


Index created.

Elapsed: 00:08:29.14

set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OI_JSON, '$.CARD_ID') = 1465982
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

Elapsed: 00:00:00.03

Execution Plan
----------------------------------------------------------
Plan hash value: 1938435827

--------------------------------------------------------------------------------
--------------------------------------------

| Id  | Operation			     | Name		   | Rows  | Byt
es | Cost (%CPU)| Time	   | Pstart| Pstop |

--------------------------------------------------------------------------------
--------------------------------------------

|   0 | SELECT STATEMENT		     |			   |	 1 |  11
36 |   521   (1)| 00:00:01 |	   |	   |

|   1 |  SORT AGGREGATE 		     |			   |	 1 |  11
36 |		|	   |	   |	   |

|   2 |   NESTED LOOPS			     |			   |   584 |   6
47K|   521   (1)| 00:00:01 |	   |	   |

|*  3 |    TABLE ACCESS BY GLOBAL INDEX ROWID| OI_JSON_ORDER_ITEMS |	 7 |  79
24 |   325   (0)| 00:00:01 | ROWID | ROWID |

|*  4 |     DOMAIN INDEX		     | I_JSON_SEARCH	   |	   |
   |	 4   (0)| 00:00:01 |	   |	   |

|*  5 |    JSONTABLE EVALUATION 	     |			   |	   |
   |		|	   |	   |	   |

--------------------------------------------------------------------------------
--------------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   3 - filter(TO_NUMBER(JSON_VALUE("OI_JSON" FORMAT JSON , '$.CARD_ID' RETURNING
 VARCHAR2(4000) NULL ON

	      ERROR))=1465982)
   4 - access("CTXSYS"."CONTAINS"("OIJ"."OI_JSON",'(sdata(FNUM_14173D25B4DD102AB
9B6F2851AEE2420_CARD_ID  = 1465982

	      ))')>0)
   5 - filter(TRUNC("P"."ORDER_DATE")=TO_DATE('24-FEB-09','DD-MON-RR'))


Statistics
----------------------------------------------------------
	216  recursive calls
	  5  db block gets
	176  consistent gets
	  0  physical reads
       1112  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  2  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

-- We can also use the dotted notation !!!

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where OIJ.OI_JSON.CARD_ID = 1465982
and trunc(ARR.ORDER_DATE) = to_date('24-FEB-09','DD-MON-RR');

-- JSON and analytical queries
--- Now let's try analytical queries !!!

sqlplus soe/soe@myoracledb:1521/ORCLPDB1
set timing on

select sum(ARR.UNIT_PRICE*ARR.QUANTITY) as "GrantTotal"
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]'
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE',
                                         QUANTITY NUMBER path '$.QUANTITY'))
                ) as ARR
where OIJ.ORDER_DATE between to_date('01-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('28-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

GrantTotal
----------
 278913547

Elapsed: 00:00:00.40

set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE*ARR.QUANTITY) as "GrantTotal"
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]'
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE',
                                         QUANTITY NUMBER path '$.QUANTITY'))
                ) as ARR
where OIJ.ORDER_DATE between to_date('01-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('28-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');


Execution Plan
----------------------------------------------------------
Plan hash value: 229940177

--------------------------------------------------------------------------------
-----------------------------------

| Id  | Operation		    | Name		  | Rows  | Bytes | Cost
 (%CPU)| Time	  | Pstart| Pstop |

--------------------------------------------------------------------------------
-----------------------------------

|   0 | SELECT STATEMENT	    |			  |	1 |  1132 |   63
0K  (1)| 00:00:25 |	  |	  |

|   1 |  SORT AGGREGATE 	    |			  |	1 |  1132 |
       |	  |	  |	  |

|*  2 |   FILTER		    |			  |	  |	  |
       |	  |	  |	  |

|   3 |    NESTED LOOPS 	    |			  |   168M|   177G|   63
0K  (1)| 00:00:25 |	  |	  |

|   4 |     PARTITION RANGE ITERATOR|			  | 20624 |    22M| 6953
8   (1)| 00:00:03 |   KEY |   KEY |

|*  5 |      TABLE ACCESS FULL	    | OI_JSON_ORDER_ITEMS | 20624 |    22M| 6953
8   (1)| 00:00:03 |   KEY |   KEY |

|   6 |     JSONTABLE EVALUATION    |			  |	  |	  |
       |	  |	  |	  |

--------------------------------------------------------------------------------
-----------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_DATE('28-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS')>=TO_DATE('01-
FEB-09

	      00:00:00','DD-MON-RR HH24:MI:SS'))
   5 - filter("OIJ"."ORDER_DATE"<=TO_DATE('28-FEB-09 23:59:59','DD-MON-RR HH24:M
I:SS') AND

	      "OIJ"."ORDER_DATE">=TO_DATE('01-FEB-09 00:00:00','DD-MON-RR HH24:M
I:SS'))



Statistics
----------------------------------------------------------
	  0  recursive calls
	  0  db block gets
       3648  consistent gets
       3646  physical reads
	  0  redo size
	574  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>


-- Populate In-memory column store
-- We can use IMC for the current partition !!!

--- Use the following query to get the name of the partitions for 2009-02:
set autotrace off
select PARTITION_NAME, HIGH_VALUE from user_tab_partitions where table_name = 'OI_JSON_ORDER_ITEMS';

SYS_P2582
TO_DATE(' 2009-03-01 00:00:00', 'SYYYY-MM-DD HH24:MI:SS', 'NLS_CALENDAR=GREGORIA'

alter table OI_JSON_ORDER_ITEMS modify partition SYS_P2582 inmemory priority critical;

Table altered.

Elapsed: 00:00:00.01
SQL>

set autotrace traceonly explain statistics

select sum(ARR.UNIT_PRICE*ARR.QUANTITY) as "GrantTotal"
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]'
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE',
                                         QUANTITY NUMBER path '$.QUANTITY'))
                ) as ARR
where OIJ.ORDER_DATE between to_date('01-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('28-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

Execution Plan
----------------------------------------------------------
Plan hash value: 229940177

--------------------------------------------------------------------------------
--------------------------------------

| Id  | Operation		       | Name		     | Rows  | Bytes | C
ost (%CPU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
--------------------------------------

|   0 | SELECT STATEMENT	       |		     |	   1 |	1132 |
 629K  (1)| 00:00:25 |	     |	     |

|   1 |  SORT AGGREGATE 	       |		     |	   1 |	1132 |
	  |	     |	     |	     |

|*  2 |   FILTER		       |		     |	     |	     |
	  |	     |	     |	     |

|   3 |    NESTED LOOPS 	       |		     |	 168M|	 177G|
 629K  (1)| 00:00:25 |	     |	     |

|   4 |     PARTITION RANGE ITERATOR   |		     | 20624 |	  22M| 6
8575   (1)| 00:00:03 |	 KEY |	 KEY |

|*  5 |      TABLE ACCESS INMEMORY FULL| OI_JSON_ORDER_ITEMS | 20624 |	  22M| 6
8575   (1)| 00:00:03 |	 KEY |	 KEY |

|   6 |     JSONTABLE EVALUATION       |		     |	     |	     |
	  |	     |	     |	     |

--------------------------------------------------------------------------------
--------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_DATE('28-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS')>=TO_DATE('01-
FEB-09 00:00:00','DD-MON-RR

	      HH24:MI:SS'))
   5 - inmemory("OIJ"."ORDER_DATE"<=TO_DATE('28-FEB-09 23:59:59','DD-MON-RR HH24
:MI:SS') AND

	      "OIJ"."ORDER_DATE">=TO_DATE('01-FEB-09 00:00:00','DD-MON-RR HH24:M
I:SS'))

       filter("OIJ"."ORDER_DATE"<=TO_DATE('28-FEB-09 23:59:59','DD-MON-RR HH24:M
I:SS') AND

	      "OIJ"."ORDER_DATE">=TO_DATE('01-FEB-09 00:00:00','DD-MON-RR HH24:M
I:SS'))



Statistics
----------------------------------------------------------
	 10  recursive calls
	  0  db block gets
	 10  consistent gets
	  0  physical reads
	  0  redo size
	574  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

SQL>

exit

-- JSON and materialized views
--- We can create materialized views on top of JSON documents !!!

sqlplus soe/soe@myoracledb:1521/ORCLPDB1


create materialized view fast_mv
build immediate
refresh complete on demand
as
select to_char(OIJ.ORDER_DATE,'YYYYMM') as "Month", sum(ARR.UNIT_PRICE*ARR.QUANTITY) as "GrantTotal"
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]'
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE',
                                         QUANTITY NUMBER path '$.QUANTITY'))
                ) as ARR
group by to_char(OIJ.ORDER_DATE,'YYYYMM');

set autotrace traceonly explain statistics
set timing on

select to_char(OIJ.ORDER_DATE,'YYYYMM') as "Month", sum(ARR.UNIT_PRICE*ARR.QUANTITY) as "GrantTotal"
from OI_JSON_ORDER_ITEMS OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]'
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE',
                                         QUANTITY NUMBER path '$.QUANTITY'))
                ) as ARR
group by to_char(OIJ.ORDER_DATE,'YYYYMM');

64 rows selected.

Elapsed: 00:00:38.50

Execution Plan
----------------------------------------------------------
Plan hash value: 2840653318

--------------------------------------------------------------------------------
---------------------------------------------

| Id  | Operation		      | Name		    | Rows  | Bytes |Tem
pSpc| Cost (%CPU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
---------------------------------------------

|   0 | SELECT STATEMENT	      | 		    | 46640 |	 50M|
    |  1987M  (1)| 21:34:11 |	    |	    |

|   1 |  HASH GROUP BY		      | 		    | 46640 |	 50M|
 12T|  1987M  (1)| 21:34:11 |	    |	    |

|   2 |   NESTED LOOPS		      | 		    |	 11G|	 12T|
    |	 38M  (1)| 00:25:23 |	    |	    |

|   3 |    PARTITION RANGE ALL	      | 		    |  1429K|  1538M|
    | 69555   (1)| 00:00:03 |	  1 |1048575|

|   4 |     TABLE ACCESS INMEMORY FULL| OI_JSON_ORDER_ITEMS |  1429K|  1538M|
    | 69555   (1)| 00:00:03 |	  1 |1048575|

|   5 |    JSONTABLE EVALUATION       | 		    |	    |	    |
    |		 |	    |	    |	    |

--------------------------------------------------------------------------------
---------------------------------------------



Statistics
----------------------------------------------------------
	 57  recursive calls
	  5  db block gets
     252342  consistent gets
     252160  physical reads
       1032  redo size
       2519  bytes sent via SQL*Net to client
	 96  bytes received via SQL*Net from client
	  6  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	 64  rows processed

SQL>

-- If we access directly to the MV, obviously we'll be much faster !!

select * from fast_mv;

64 rows selected.

Elapsed: 00:00:00.01

Execution Plan
----------------------------------------------------------
Plan hash value: 140868995

--------------------------------------------------------------------------------
---------

| Id  | Operation		      | Name	| Rows	| Bytes | Cost (%CPU)| T
ime	|

--------------------------------------------------------------------------------
---------

|   0 | SELECT STATEMENT	      | 	|    64 |   896 |     3   (0)| 0
0:00:01 |

|   1 |  MAT_VIEW ACCESS INMEMORY FULL| FAST_MV |    64 |   896 |     3   (0)| 0
0:00:01 |

--------------------------------------------------------------------------------
---------



Statistics
----------------------------------------------------------
	  1  recursive calls
	  0  db block gets
	  7  consistent gets
	  0  physical reads
	  0  redo size
       2519  bytes sent via SQL*Net to client
	 96  bytes received via SQL*Net from client
	  6  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	 64  rows processed

SQL>

