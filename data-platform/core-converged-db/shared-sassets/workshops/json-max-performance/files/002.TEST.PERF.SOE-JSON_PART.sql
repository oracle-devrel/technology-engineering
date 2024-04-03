-- Partitionning on JSON field: unlike OI_JSON_ORDER_ITEMS, that has been partitionned on a regular column, we will create a new JSON table
-- partitioned on a JSON field (virtual column).

-- This is the original table
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

-- This is the new table:

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

Table created.

SQL>
SQL>
SQL> desc OI_JSON_ORDER_ITEMS_PART
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 ID					   NOT NULL NUMBER(12)
 OI_JSON					    VARCHAR2(4000)
 ORDER_DATE					    DATE

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


1429790 rows created.

Elapsed: 00:01:44.14
SQL> SQL> SQL> SQL> commit;

Commit complete.

Elapsed: 00:00:00.07

-- Now let's repeat the same tests as before:

select ARR.* 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
              '$'  COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE')
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116;

ORDER_DAT
---------
24-FEB-09
18-OCT-10
15-NOV-10

Elapsed: 00:00:03.53

select ARR.* 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116;

ORDER_DAT UNIT_PRICE
--------- ----------
24-FEB-09	1141
24-FEB-09	1223
24-FEB-09	1427
24-FEB-09	1355
18-OCT-10	1403
18-OCT-10	 989
18-OCT-10	 763
18-OCT-10	1094
15-NOV-10	 973
15-NOV-10	 975
15-NOV-10	 963

11 rows selected.

Elapsed: 00:00:03.08

-- Reconnect to avaoid parallel query execution !!!

sqlplus soe/soe@myoracledb:1521/orclpdb1
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

SUM(ARR.UNIT_PRICE)
-------------------
	       5146

Elapsed: 00:00:04.70

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

Elapsed: 00:00:04.68

Execution Plan
----------------------------------------------------------
Plan hash value: 939613720

--------------------------------------------------------------------------------
------------------------------------

| Id  | Operation		| Name			   | Rows  | Bytes | Cos
t (%CPU)| Time	   | Pstart| Pstop |

--------------------------------------------------------------------------------
------------------------------------

|   0 | SELECT STATEMENT	|			   |	 1 |  2006 |   4
92K  (3)| 00:00:20 |	   |	   |

|   1 |  SORT AGGREGATE 	|			   |	 1 |  2006 |
	|	   |	   |	   |

|   2 |   NESTED LOOPS		|			   |  1239K|  2372M|   4
92K  (3)| 00:00:20 |	   |	   |

|   3 |    PARTITION RANGE ALL	|			   | 15180 |	28M| 697
81   (1)| 00:00:03 |	 1 |1048575|

|*  4 |     TABLE ACCESS FULL	| OI_JSON_ORDER_ITEMS_PART | 15180 |	28M| 697
81   (1)| 00:00:03 |	 1 |1048575|

|*  5 |    JSONTABLE EVALUATION |			   |	   |	   |
	|	   |	   |	   |

--------------------------------------------------------------------------------
------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   4 - filter(TO_NUMBER(JSON_VALUE("OIJ"."OI_JSON" FORMAT JSON , '$.CUSTOMER_ID'
 RETURNING VARCHAR2(4000)

	      NULL ON ERROR))=733116)
   5 - filter(TRUNC("P"."ORDER_DATE")=TO_DATE('24-FEB-09','DD-MON-RR'))

Note
-----
   - dynamic statistics used: dynamic sampling (level=2)


Statistics
----------------------------------------------------------
	  0  recursive calls
	  0  db block gets
     253590  consistent gets
     249728  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed


--- WE should use ORDER_DATE virtual column to leverage partition pruning !!!

select sum(ARR.UNIT_PRICE) 
from OI_JSON_ORDER_ITEMS_PART OIJ,
     json_table(OIJ.OI_JSON,
                '$' COLUMNS (ORDER_DATE DATE path '$.ORDER_DATE',
                                NESTED PATH '$.ITEMS[*]' 
                                COLUMNS (UNIT_PRICE NUMBER path '$.UNIT_PRICE'))
                ) as ARR
where json_value (OIJ.OI_JSON, '$.CUSTOMER_ID') = 733116
and OIJ.ORDER_DATE between to_date('24-FEB-09 00:00:00','DD-MON-RR HH24:MI:SS') and to_date('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS');

Elapsed: 00:00:00.06

Execution Plan
----------------------------------------------------------
Plan hash value: 3037461420

--------------------------------------------------------------------------------
----------------------------------------

| Id  | Operation		    | Name		       | Rows  | Bytes |
 Cost (%CPU)| Time     | Pstart| Pstop |

--------------------------------------------------------------------------------
----------------------------------------

|   0 | SELECT STATEMENT	    |			       |     1 |  2013 |
  3935	(54)| 00:00:01 |       |       |

|   1 |  SORT AGGREGATE 	    |			       |     1 |  2013 |
	    |	       |       |       |

|*  2 |   FILTER		    |			       |       |       |
	    |	       |       |       |

|   3 |    NESTED LOOPS 	    |			       |   250K|   480M|
  3935	(54)| 00:00:01 |       |       |

|   4 |     PARTITION RANGE ITERATOR|			       |    31 | 62341 |
  3091	(68)| 00:00:01 |   KEY |   KEY |

|*  5 |      TABLE ACCESS FULL	    | OI_JSON_ORDER_ITEMS_PART |    31 | 62341 |
  3091	(68)| 00:00:01 |   KEY |   KEY |

|   6 |     JSONTABLE EVALUATION    |			       |       |       |
	    |	       |       |       |

--------------------------------------------------------------------------------
----------------------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_DATE('24-FEB-09 23:59:59','DD-MON-RR HH24:MI:SS')>=TO_DATE('24-
FEB-09 00:00:00','DD-MON-RR

	      HH24:MI:SS'))
   5 - filter(TO_NUMBER(JSON_VALUE("OIJ"."OI_JSON" FORMAT JSON , '$.CUSTOMER_ID'
 RETURNING VARCHAR2(4000) NULL

	      ON ERROR))=733116 AND "OIJ"."ORDER_DATE">=TO_DATE('24-FEB-09 00:00
:00','DD-MON-RR HH24:MI:SS') AND

	      "OIJ"."ORDER_DATE"<=TO_DATE('24-FEB-09 23:59:59','DD-MON-RR HH24:M
I:SS'))


Note
-----
   - dynamic statistics used: dynamic sampling (level=2)


Statistics
----------------------------------------------------------
	 18  recursive calls
	  0  db block gets
       3663  consistent gets
	  0  physical reads
	  0  redo size
	580  bytes sent via SQL*Net to client
	 52  bytes received via SQL*Net from client
	  2  SQL*Net roundtrips to/from client
	  0  sorts (memory)
	  0  sorts (disk)
	  1  rows processed

-- We don't repeat the further tests (indexes, search indexes, mv), as partitioning by a JSON field will have no impact.