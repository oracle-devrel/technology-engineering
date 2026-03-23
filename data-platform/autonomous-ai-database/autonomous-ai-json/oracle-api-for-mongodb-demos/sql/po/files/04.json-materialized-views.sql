


---------------------------------------------------------------------------------
-- Materialized  Views over JSON Data with ROWID and PRIMARY KEY
-- PURCHASEORDERS collection table 
---------------------------------------------------------------------------------

-- Creating Materialized view with ROWID 
DROP MATERIALIZED VIEW JSON_PO_MV;
CREATE MATERIALIZED VIEW JSON_PO_MV
BUILD IMMEDIATE
REFRESH FAST ON STATEMENT WITH ROWID
AS
SELECT po.rowid as id, jt.*
FROM PURCHASEORDERS po,
    JSON_TABLE(DATA, '$' error on error null on empty
     COLUMNS (ponumber  number         PATH '$.PONumber',
              requestor varchar2(32)   PATH '$.Requestor',
              special   varchar2(30)   PATH '$."Special Instructions"',
              NESTED PATH '$.LineItems[*]'
                     COLUMNS
                     ( itemnumber number PATH '$.ItemNumber', 
                        quantity number PATH '$.Quantity', 
                        NESTED PATH '$.Part[*]'
                        COLUMNS ( 
                        itemdesc varchar2(50) PATH '$.Description',
                        upccode  number PATH '$.UPCCode',
                        unitprice number PATH '$.UnitPrice')
                      )
                )) jt;


-- Explain Plan
EXPLAIN PLAN FOR 
SELECT * FROM JSON_PO_VIEW_NESTED;
SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());


-- Creating Materialized view with PK 
DROP MATERIALIZED VIEW JSON_PO_MV_PK;
CREATE MATERIALIZED VIEW JSON_PO_MV_PK BUILD IMMEDIATE
REFRESH FAST ON STATEMENT WITH PRIMARY KEY
AS SELECT po.resid, jt.*
FROM PURCHASEORDERS po,
    JSON_TABLE(po.DATA, '$' error on error null on empty
           COLUMNS
           (poNum           varchar2(10) PATH '$.PONumber',
            userid          VARCHAR2(10) PATH '$.User',
            NESTED PATH '$.LineItems[*]'
            COLUMNS
            (itemnumber number PATH '$.ItemNumber', 
             itemQuantity varchar2(10) PATH '$.Quantity',
             NESTED PATH '$.Part[*]'
             COLUMNS ( itename varchar2(50) PATH '$.Description',
                      upccode  varchar2(10) PATH '$.UPCCode',
                      unitprice number PATH '$.UnitPrice'
                     )  
            )
          )) jt; 
      
DROP MATERIALIZED VIEW JSON_PO_MV_PK;          
CREATE MATERIALIZED VIEW JSON_PO_MV_PK BUILD IMMEDIATE
REFRESH FAST ON STATEMENT WITH PRIMARY KEY
AS SELECT po.resid, po.*
FROM PURCHASEORDERS po,
      JSON_TABLE (po.DATA, '$' error on error null on empty
            COLUMNS (ponumber  number         PATH '$.PONumber',
                     requestor varchar2(32)   PATH '$.Requestor',
                     special   varchar2(30)   PATH '$."Special Instructions"',
                     NESTED PATH '$.LineItems[*]'
                     COLUMNS
                     ( itemnumber number PATH '$.ItemNumber', 
                        NESTED PATH '$.Part[*]'
                        COLUMNS ( 
                        itemdesc varchar2(50) PATH '$.Description',
                        upccode  number PATH '$.UPCCode',
                        unitprice number PATH '$.UnitPrice')
                        )));


EXPLAIN PLAN FOR  SELECT * FROM JSON_PO_MV_PK; 
select  PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());

set define off
explain plan for SELECT po.data FROM purchaseorders po
  WHERE json_exists(po.data,
                    '$?(@.PONumber == 25
                        && exists(@.LineItems[*]?(
                                   @.Part.UPCCode == 85391264828
                                    && @.Quantity > 3))'); 
 

select  PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());

explain plan for SELECT po.data FROM purchaseorders po
  WHERE json_exists(po.data,
                    '$?(@.PONumber == 25
                        && exists(@.LineItems[*]?(
                                   @.Part[*]?(@.UPCCode == 85391264828
                                    && @.Quantity > 3)))'); 



------- Query Rewrite

CREATE MATERIALIZED VIEW mv_for_query_rewrite
  BUILD IMMEDIATE
  REFRESH FAST ON STATEMENT WITH PRIMARY KEY
  AS SELECT po.resid, jt.*
       FROM purchaseorders po,
            json_table(po.data, '$' ERROR ON ERROR NULL ON EMPTY
              COLUMNS (
                po_number       NUMBER         PATH '$.PONumber',
                userid          VARCHAR2(10)   PATH '$.User',
                NESTED PATH '$.LineItems[*]'
                  COLUMNS (
                    itemno      NUMBER         PATH '$.ItemNumber',
                    description VARCHAR2(256)  PATH '$.Part.Description',
                    upc_code    NUMBER         PATH '$.Part.UPCCode',
                    quantity    NUMBER         PATH '$.Quantity',
                    unitprice   NUMBER         PATH '$.Part.UnitPrice'))) jt;

---- &&
SET DEFINE OFF

EXPLAIN PLAN for SELECT po.data FROM purchaseorders po
      WHERE JSON_EXISTS(po.data,
                    '$?(@.PONumber == 25
                        && exists(@.LineItems[*]?(
                                   @.Part.UPCCode == 85391264828
                                    && @.Quantity > 3)))'); 

SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());

SELECT JSON_SERIALIZE(po.data) FROM purchaseorders po WHERE json_exists(po.data,
                    '$?(@.User == "ABULL"
                        && exists(@.LineItems[*]?(
                                    @.Part.UPCCode == 85391628927
                                    && @.Quantity > 3)))');

-- explain plan 
explain plan for SELECT po.data FROM purchaseorders po
  WHERE json_exists(po.data,
                    '$?(@.User == "ABULL"
                        && exists(@.LineItems[*]?(
                                    @.Part.UPCCode == 85391628927
                                    && @.Quantity > 3)))'); 
 
 SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());
 

/*
Plan hash value: 1405009755                                                                                        
                                                                                                                   
-----------------------------------------------------------------------------------------------------              
| Id  | Operation                    | Name                 | Rows  | Bytes | Cost (%CPU)| Time     |              
-----------------------------------------------------------------------------------------------------              
|   0 | SELECT STATEMENT             |                      |     1 |  5137 |   131   (2)| 00:00:01 |              
|   1 |  NESTED LOOPS                |                      |     1 |  5137 |   131   (2)| 00:00:01 |              
|   2 |   SORT UNIQUE                |                      |     1 |    33 |   129   (1)| 00:00:01 |              
|*  3 |    MAT_VIEW ACCESS FULL      | MV_FOR_QUERY_REWRITE |     1 |    33 |   129   (1)| 00:00:01 |              
|   4 |   TABLE ACCESS BY INDEX ROWID| PURCHASEORDERS       |     1 |  5104 |     1   (0)| 00:00:01 |              
|*  5 |    INDEX UNIQUE SCAN         | SYS_C008438          |     1 |       |     0   (0)| 00:00:01 |              
-----------------------------------------------------------------------------------------------------              
                                                                                                                   
Predicate Information (identified by operation id):                                                                
---------------------------------------------------                                                                
                                                                                                                   
   3 - filter("SYS_JMV_1"."UPC_CODE"=85391628927 AND "SYS_JMV_1"."USERID"='ABULL' AND                              
              "SYS_JMV_1"."QUANTITY">3)                                                                            
   5 - access("SYS_JMV_1"."RESID"=JSON_VALUE("DATA" /*+ LOB_BY_VALUE    FORMAT OSON ,                             
              '$._id' RETURNING ANY ORA_RAWCOMPARE(2000) NO ARRAY ERROR ON ERROR TYPE(LAX) ))                      
                                                                                                                   
Note                                                                                                               
-----                                                                                                              
   - dynamic statistics used: dynamic sampling (level=2)                                                           

24 rows selected. 

You can tell whether the materialized view is used for a particular query by examining the execution plan. 
If it is, then the plan refers to mv_for_query_rewrite. For example:
|* 4| MAT_VIEW ACCESS FULL | MV_FOR_QUERY_REWRITE |1|51|3(0)|00:00:01|
*/
---
-- Index on a MV
drop INDEX MV_IDx;
CREATE INDEX mv_idx ON mv_for_query_rewrite(userid,
                                            upc_code,
                                            quantity);

explain plan for SELECT po.data FROM purchaseorders po
  WHERE json_exists(po.data,
                    '$?(@.User == "ABULL"
                        && exists(@.LineItems[*]?(
                                    @.Part.UPCCode == 85391628927
                                    && @.Quantity > 3)))'); 

SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());
/*
PLAN_TABLE_OUTPUT                                                                                        
________________________________________________________________________________________________________ 
Plan hash value: 1405009755                                                                              
                                                                                                         
-----------------------------------------------------------------------------------------------------    
| Id  | Operation                    | Name                 | Rows  | Bytes | Cost (%CPU)| Time     |    
-----------------------------------------------------------------------------------------------------    
|   0 | SELECT STATEMENT             |                      |     1 |  5137 |   131   (2)| 00:00:01 |    
|   1 |  NESTED LOOPS                |                      |     1 |  5137 |   131   (2)| 00:00:01 |    
|   2 |   SORT UNIQUE                |                      |     1 |    33 |   129   (1)| 00:00:01 |    
|*  3 |    MAT_VIEW ACCESS FULL      | MV_FOR_QUERY_REWRITE |     1 |    33 |   129   (1)| 00:00:01 |    
|   4 |   TABLE ACCESS BY INDEX ROWID| PURCHASEORDERS       |     1 |  5104 |     1   (0)| 00:00:01 |    
|*  5 |    INDEX UNIQUE SCAN         | SYS_C008438          |     1 |       |     0   (0)| 00:00:01 |    
-----------------------------------------------------------------------------------------------------    
                                                                                                         
Predicate Information (identified by operation id):                                                      
---------------------------------------------------                                                      
                                                                                                         
   3 - filter("SYS_JMV_1"."UPC_CODE"=85391628927 AND "SYS_JMV_1"."USERID"='ABULL' AND                    
              "SYS_JMV_1"."QUANTITY">3)                                                                  
   5 - access("SYS_JMV_1"."RESID"=JSON_VALUE("DATA" /*+ LOB_BY_VALUE * FORMAT OSON ,                   
              '$._id' RETURNING ANY ORA_RAWCOMPARE(2000) NO ARRAY ERROR ON ERROR TYPE(LAX) ))            
                                                                                                         
Note                                                                                                     
-----                                                                                                    
   - dynamic statistics used: dynamic sampling (level=2)                                                 

24 rows selected. 
*/


-- Materialized view  aggregation                 
DROP MATERIALIZED VIEW  mv_for_aggregation;
CREATE MATERIALIZED VIEW mv_for_aggregation
  AS SELECT jt.po_number, sum(jt.quantity * jt.unitprice) 
       FROM PURCHASEORDERS po,
            json_table(po.data, '$' ERROR ON ERROR NULL ON EMPTY
              COLUMNS (
                po_number       NUMBER         PATH '$.PONumber',
                userid          VARCHAR2(10)   PATH '$.User',
                NESTED PATH '$.LineItems[*]'
                  COLUMNS (
                    itemno      NUMBER         PATH '$.ItemNumber',
                    description VARCHAR2(256)  PATH '$.Part.Description',
                    upc_code    NUMBER         PATH '$.Part.UPCCode',
                    quantity    NUMBER         PATH '$.Quantity',
                    unitprice   NUMBER         PATH '$.Part.UnitPrice'))) jt 
          GROUP BY (jt.po_number);



explain plan for select * from mv_for_aggregation;

select * from SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY());

-- MV example 2
-- SALES JSON collection Tabke
drop table if exists SALES;
create JSON collection table if not exists SALES;

-- populate the JSON collection table with 2 documents:

insert into SALES values ('{ "_id" : 1, "item" : "Espresso", "price" : 5, "size": "Short", "quantity" : 22, "date" : "2025-04-15T08:00:00Z"}');
insert into SALES values ('{ "_id" : 2, "item" : "Finlandia", "price" : 6, "old_price" : 4, "size": "Grande","quantity" : 100, "date" : "2025-01-10T10:00:00Z",
"CoffeeItems" : [{ "Details"     : { "Description" : "Coffee from Helsinki",
                                "UnitPrice"   : 6,
                                "Code"        : 35801},
                   "Quantity" : 50.0 },
                 { "Details"     : { "Description" : "Coffee from Tampere",
                                "UnitPrice"   : 6,
                                "Code"        : 35802},
                   "Quantity" : 30.0 } ,
                 { "Details"     : { "Description" : "Coffee from Turku",
                                "UnitPrice"   : 6,
                                "Code"        : 35803},
                   "Quantity" : 20.0 }] }');

commit work;

drop MATERIALIZED VIEW if exists sales_mv;

CREATE MATERIALIZED VIEW sales_mv
  BUILD IMMEDIATE
  REFRESH FORCE 
   START WITH TRUNC(SYSDATE+1)+12/24
   NEXT SYSDATE+1 
  WITH ROWID
 AS SELECT jt.*
    FROM sales s,
         json_table(s.data, '$' ERROR ON ERROR NULL ON EMPTY
              COLUMNS (
                item_id         NUMBER         PATH '$._id',
                item_name       VARCHAR2(16)   PATH '$.item',
                item_price      NUMBER         PATH '$.price',
                NESTED PATH '$.CoffeeItems[*]'
                  COLUMNS (
                    details_description VARCHAR2(32)  PATH '$.Details.Description',
                    details_code        NUMBER        PATH '$.Details.Code'))) jt;

CREATE INDEX mv_det_code_idx ON sales_mv(details_code);

select * from SALES_MV;
-- update the price
exec DBMS_MVIEW.REFRESH('SALES_MV');
SELECT * FROM sales_mv s WHERE s.details_code is not null;
explain plan for SELECT * FROM sales_mv s WHERE s.details_code is not null;
select * from dbms_xplan.display();

CREATE OR REPLACE JSON COLLECTION VIEW sales_json_cv AS 
  SELECT JSON {'_id'             : item_id,
               'coffee_location' : details_description,
               'code'            : details_code}
  FROM sales_mv
  WHERE details_code is not NULL;
  
select * from SALES_JSON_CV;




