alter session set tracefile_identifier='CCCP1';
alter session set events '10046';

update CUST_ORDERS
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

commit;

alter session set events '10046 trace name context off';

-- See files: FREE_ora_212444_CCCP1.trc and JRD_update.lis

--- autotrace:

set autotrace traceonly explain statistics

update CUST_ORDERS
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
	},
	{
	  "ORDER_ID" : 1000,
	  "LINE_ITEM_ID" : 3,
	  "PRODUCT_ID" : 1726,
	  "UNIT_PRICE" : 1000,
	  "QUANTITY" : 1
	}
      ]
    }
  ]
}'
where json_value(data, '$.CUSTOMER_ID') = 9999;


1 row updated.


Execution Plan
----------------------------------------------------------
Plan hash value: 1666954083

--------------------------------------------------------------------------------
-------------------------

| Id  | Operation			      | Name		| Rows	| Bytes
| Cost (%CPU)| Time	|

--------------------------------------------------------------------------------
-------------------------

|   0 | UPDATE STATEMENT		      | 		|     3 |   168
|    26   (0)| 00:00:01 |

|   1 |  UPDATE 			      | CUSTOMERS	|	|
|	     |		|

|*  2 |   TABLE ACCESS FULL		      | CUSTOMERS	|     3 |   168
|     5   (0)| 00:00:01 |

|   3 |   TABLE ACCESS BY INDEX ROWID	      | CUSTOMERS	|     1 |    56
|     1   (0)| 00:00:01 |

|*  4 |    INDEX UNIQUE SCAN		      | CUSTOMERS_PK	|     1 |
|     0   (0)| 00:00:01 |

|   5 |   SORT GROUP BY 		      | 		|     1 |    18
|	     |		|

|   6 |    TABLE ACCESS BY INDEX ROWID BATCHED| ORDER_ITEMS	|     6 |   108
|     3   (0)| 00:00:01 |

|*  7 |     INDEX RANGE SCAN		      | ITEM_ORDER_IX	|     6 |
|     1   (0)| 00:00:01 |

|   8 |   SORT GROUP BY 		      | 		|     1 |    17
|	     |		|

|   9 |    TABLE ACCESS BY INDEX ROWID BATCHED| ORDERS		|     2 |    34
|     2   (0)| 00:00:01 |

|* 10 |     INDEX RANGE SCAN		      | ORD_CUSTOMER_IX |     2 |
|     1   (0)| 00:00:01 |

--------------------------------------------------------------------------------
-------------------------


Predicate Information (identified by operation id):
---------------------------------------------------

   2 - filter(TO_NUMBER(JSON_VALUE(JSON_SCALAR("C"."CUSTOMER_ID" JSON NULL ON NU
LL ) FORMAT OSON

	      , '$.string()' RETURNING VARCHAR2(4000) NULL ON ERROR))=9999)
   4 - access("C"."CUSTOMER_ID"=:B1)
   7 - access("OI"."ORDER_ID"=:B1)
  10 - access("O"."CUSTOMER_ID"=:B1)

SQL Analysis Report (identified by operation id/Query Block Name/Object Alias):
-------------------------------------------------------------------------------

   2 -	SEL$494CC270 / "C"@"SEL$2"
	   -  The following columns have predicates which preclude their
	      use as keys in index range scan. Consider rewriting the
	      predicates.
		"CUSTOMER_ID"


Statistics
----------------------------------------------------------
	109  recursive calls
	 15  db block gets
	 78  consistent gets
	  0  physical reads
	  0  redo size
	204  bytes sent via SQL*Net to client
	 83  bytes received via SQL*Net from client
	  1  SQL*Net roundtrips to/from client
	  4  sorts (memory)
	  0  sorts (disk)
	  1  rows processed


SQL> commit;

Commit complete.

SQL> set autotrace off
SQL> select * from order_items where order_id = 1000;

  ORDER_ID LINE_ITEM_ID PRODUCT_ID UNIT_PRICE	QUANTITY
---------- ------------ ---------- ---------- ----------
      1000	      1       3350	 1000	       1
      1000	      3       1726	 1000	       1
      1000	      2       2236	 1000	       1

SQL>