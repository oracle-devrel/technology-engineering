

-- PURCHASEORDERS - JSON collection table 
-- PURCHASEORDER_CV, PURCHASEORDER_TOT_PRC_CV, PURCHASEORDER_AVG_PRC_CV  - JSON collection views


---------------------------------------------------------------------------------
---------------------------- JSON RELATIONAL VIEW ------------------------------- 
---------------------------------------------------------------------------------
CREATE or REPLACE VIEW PURCHASEORDER_V AS
      SELECT ponumber, requestor, special, address
      FROM PURCHASEORDERS,
          json_table (DATA, '$'
            COLUMNS (ponumber  number         PATH '$.PONumber',  
                     requestor varchar2(32)   PATH '$.Requestor',
                     special   varchar2(10)   PATH '$."Special Instructions"',
                     address    JSON  PATH '$.ShippingInstructions.Address')) jt         
;


DESC PURCHASEORDER_V
/*
Name      Null? Type         

--------- ----- ------------ 
PONUMBER        NUMBER       
REQUESTOR       VARCHAR2(32) 
SPECIAL         VARCHAR2(10) 
ADDRESS         JSON   
*/

SELECT * FROM  PURCHASEORDER_V ORDER BY PONUMBER; 
/*
   PONUMBER REQUESTOR         SPECIAL       ADDRESS                                                                                                                                 
___________ _________________ __________ _______________________________________________________________________________________________________________________________________ 
          1 Martha Sullivan              {"street":"200 Sporting Green","city":"South San Francisco","state":"CA","zipCode":99236,"country":"United States of America"}          
          2 Martha Sullivan              {"street":"200 Sporting Green","city":"South San Francisco","state":"CA","zipCode":99236,"country":"United States of America"} 
 ...............................................................................................................................
 
 */ 

SELECT po_v.ponumber, po_v.REQUESTOR , po_v.SPECIAL, po_v.address.city FROM 
PURCHASEORDER_V po_v WHERE ponumber =7;
/*
  PONUMBER REQUESTOR      SPECIAL       CITY                     
___________ ______________ _____________ ________________________ 
          7 Vance Jones    Hand Carry    "South San Francisco"   */

-- using a CTE (Common Table Expression) 
WITH po_cte AS 
          (SELECT ponumber, requestor, special, address
          FROM PURCHASEORDERS,
             JSON_TABLE (DATA, '$'
                COLUMNS (ponumber  number         PATH '$.PONumber',
                         requestor varchar2(32)   PATH '$.Requestor',
                         special   varchar2(32)   PATH '$."Special Instructions"',
                         address    JSON  PATH '$.ShippingInstructions.Address')) jt
            )
SELECT ponumber, requestor, special, address FROM  po_cte;

---------------------------------------------------------------------------------
---------------------------- JSON COLLECTION VIEW ------------------------------- 
---------------------------------------------------------------------------------
  
 
-- JSON collection view with nested path 
CREATE OR REPLACE  JSON COLLECTION VIEW PURCHASEORDER_CV AS
      SELECT JSON {ponumber, requestor, special, itemnumber,itemdesc,unitprice, upccode, quantity}
      FROM PURCHASEORDERS,
          JSON_TABLE (DATA, '$'
            COLUMNS (ponumber  number         PATH '$.PONumber',
                     requestor varchar2(32)   PATH '$.Requestor',
                     special   varchar2(30)   PATH '$."Special Instructions"',
                     NESTED PATH '$.LineItems[*]'
                     COLUMNS
                     (  itemnumber number PATH '$.ItemNumber', 
                        quantity number PATH '$.Quantity',
                        NESTED PATH '$.Part[*]'
                        COLUMNS ( 
                        itemdesc varchar2(50) PATH '$.Description',
                        upccode  number PATH '$.UPCCode',
                        unitprice number PATH '$.UnitPrice')
                      )
                    ))
  ;
                    
                     
SELECT po.DATA.requestor
      ,po.DATA.ponumber
      ,po.DATA.itemnumber
      ,po.DATA.itemdesc
      ,po.DATA.unitprice
      ,po.DATA.quantity
    FROM PURCHASEORDER_CV po 
WHERE po.DATA.ponumber=25
;
/*
REQUESTOR          PONUMBER    ITEMNUMBER    ITEMDESC                                  UNITPRICE    QUANTITY    
__________________ ___________ _____________ _________________________________________ ____________ ___________ 
"Timothy Gates"    25          1             "The Land Before Time: The Big Freeze"    27.95        2           
"Timothy Gates"    25          2             "Winning"                                 19.95        1           
"Timothy Gates"    25          3             "Falling Down"                            19.95        5         
*/
----------------------------------------------------------------------------------------------------------------
----------------JSON COLLECTION VIEW  with AGGREGATE functions  
----------------------------------------------------------------------------------------------------------------

-- JSON collection view with SUM 
CREATE OR REPLACE JSON COLLECTION VIEW PURCHASEORDER_TOT_PRC_CV AS
    SELECT JSON {jt.ponumber, jt.requestor,  jt.total_price}
       FROM (
       SELECT  ROUND (SUM(unitprice * quantity),2)  total_price
       , ponumber
       , requestor
       FROM PURCHASEORDERS,
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
                        itemdesc CLOB PATH '$.Description',
                        upccode  number PATH '$.UPCCode',
                        unitprice number PATH '$.UnitPrice')
                      )
                ))
        GROUP BY requestor, ponumber
        )jt
;

SELECT po.DATA.ponumber, po.DATA.requestor,po.DATA.total_price 
      FROM PURCHASEORDER_TOT_PRC_CV po
      WHERE po.DATA.ponumber=25;
                   
 /*
PONUMBER    REQUESTOR          TOTAL_PRICE    
___________ __________________ ______________ 
25          "Timothy Gates"    175.6          

 */

---------------------------------------------------------------------------------
----------------JSON COLLECTION VIEWS with WINDOW function ---------------------- 
---------------------------------------------------------------------------------
-- Avgeare of Total items price   

 
CREATE OR REPLACE JSON COLLECTION VIEW PURCHASEORDER_AVG_PRC_CV AS
    SELECT JSON {
       jt.ponumber,
       jt.itemnumber,
       jt.itemdesc,
       jt.quantity,
       jt.unitprice,
       jt.total_item_price,
       jt.average_total_item_price}
    FROM (
    SELECT 
           ponumber, 
           itemnumber,
           itemdesc,
           quantity,
           unitprice,  
          ROUND (unitprice * quantity,2) total_item_price,
          ROUND (avg(unitprice * quantity) over (partition by ponumber),2)  average_total_item_price
          FROM PURCHASEORDERS, 
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
                                  itemdesc CLOB PATH '$.Description',
                                  --itemdesc varchar2(100) PATH '$.Description',
                                  upccode  number PATH '$.UPCCode',
                                  unitprice number PATH '$.UnitPrice')
                              )
                        )
                    )
          ) jt
;


SELECT po.DATA.ponumber,
       po.DATA.itemnumber,
       po.DATA.itemdesc,
       po.DATA.quantity,
       po.DATA.unitprice,
       po.DATA.total_item_price,
       po.DATA.average_total_item_price 
 FROM PURCHASEORDER_AVG_PRC_CV po
 WHERE po.DATA.ponumber=25
;
 
/*

PONUMBER    ITEMNUMBER    ITEMDESC                                  QUANTITY    UNITPRICE    TOTAL_ITEM_PRICE    AVERAGE_TOTAL_ITEM_PRICE    
___________ _____________ _________________________________________ ___________ ____________ ___________________ ________________________ 
25          1             "The Land Before Time: The Big Freeze"    2           27.95        55.9                58.53                 
25          2             "Winning"                                 1           19.95        19.95               58.53                 
25          3             "Falling Down"                            5           19.95        99.75               58.53                 
*/



