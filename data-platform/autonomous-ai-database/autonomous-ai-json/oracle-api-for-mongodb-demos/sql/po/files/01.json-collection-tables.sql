

-------------------------------------------------------------------------------------------------------
-----------  SAMPLE Queries using SQL/JSON JSON_VALUE,JSON_EXISTS,JSON_QUERY ------------------------
-------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------
-- dot notation: "_id", "resid", "reference", "requestor"
-------------------------------------------------------------------------------------------------------
 SELECT po.DATA."_id"  "_id"
      , po.resid resid
      , po.DATA.Reference reference
      , po.DATA.Requestor requestor
  FROM PURCHASEORDERS po where rownum < 2; 

/*
_id                           RESID                         REFERENCE              REQUESTOR           
_____________________________ _____________________________ ______________________ ___________________ 
"681778538527e06b8c86e698"    08681778538527E06B8C86E698    "SVOLLMAN-20140523"    "Shanta Vollman"    
*/

-------------------------------------------------------------------------------------------------------
-- JSON_SERIALIZE, JSON_EXISTS  
-------------------------------------------------------------------------------------------------------

SELECT JSON_SERALIZE(DATA  PRETTY ORDERED)
    FROM PURCHASEORDERS 
    WHERE JSON_EXISTS(DATA, '$?(@.PONumber == $V1)'
       PASSING '25' AS "V1")       
;
 /* {                                                                                                      
  "_id" : "6810e62338848c2330102b9a",                                                                  
  "CostCenter" : "A50",                                                                                
  "PONumber" : 25,                                                                                     
  "Reference" : "TGATES-20140511",                                                                     
  "Requestor" : "Timothy Gates",                                                                       
  "Special Instructions" : "Priority Overnight",                                                       
  "User" : "TGATES",                                                                                   
  "ShippingInstructions" :                                                                             
  {                                                                                                    
    "name" : "Timothy Gates",                                                                          
    "Address" :                                                                                        
    {                                                                                                  
      "city" : "South San Francisco",                                                                  
      "country" : "United States of America",                                                          
      "state" : "CA",                                                                                  
      "street" : "200 Sporting Green",                                                                 
      "zipCode" : 99236                                                                                
  ....................................                                                                                                
}*/      
-------------------------------------------------------------------------------------------------------
-- JSON_EXISTS. Query by "_id"
-------------------------------------------------------------------------------------------------------
SELECT DATA
    FROM PURCHASEORDERS 
    WHERE JSON_EXISTS(DATA, '$?(@._id == $V1)'
    PASSING '681778538527e06b8c86e698' AS "V1")
;
 
-------------------------------------------------------------------------------------------------------
-- JSON_VALUE. Extracting three POs references
-------------------------------------------------------------------------------------------------------

SELECT JSON_VALUE (DATA, '$.Reference') "PO Reference"
       FROM PURCHASEORDERS where ROWNUM < 4;
/*
PO Reference         
____________________ 
SVOLLMAN-20140531    
TFOX-20140511        
GGEONI-20141114 
*/
-------------------------------------------------------------------------------------------------------
--JSON_EXISTS. Extracting  LineItems with UPCCode = 85391628927
-------------------------------------------------------------------------------------------------------
SELECT JSON_SERIALIZE(DATA pretty) FROM PURCHASEORDERS 
  WHERE JSON_EXISTS (DATA,'$.LineItems.Part?(@.UPCCode == $V1)'
                    PASSING '85391628927' AS "V1");
/*
{
  "_id" : "68177b1d8527e06b8c873477",
  "PONumber" : 9947,
  "Reference" : "GHIMURO-20141128",
  "Requestor" : "Guy Himuro",
  "User" : "GHIMURO",
  "CostCenter" : "A30",
  "ShippingInstructions" :
  {
    "name" : "Guy Himuro",
    "Address" :
    {
      "street" : "2004 Blacksmiths Court",
      "city" : "Seattle",
      "state" : "WA",
      "zipCode" : 98199,
  ...................

*/                    
-------------------------------------------------------------------------------------------------------
--- Extracting LineItems with unit price less than 19
-------------------------------------------------------------------------------------------------------
SELECT DATA FROM PURCHASEORDERS 
   WHERE JSON_EXISTS(DATA '$.LineItems.Part?(@.UnitPrice < $V1)'
                    PASSING '19' AS "V1");
-------------------------------------------------------------------------------------------------------
--- Extracting Purchase Order 25
-------------------------------------------------------------------------------------------------------
SELECT DATA FROM PURCHASEORDERS
     WHERE JSON_EXISTS(DATA, '$?(@.PONumber == $V1)'
       PASSING '25' AS "V1" ); 
-------------------------------------------------------------------------------------------------------
-- Extracting Orders allowing Partial Shipments - Boolean DATA type 
-------------------------------------------------------------------------------------------------------
SELECT DATA
     FROM PURCHASEORDERS 
     WHERE JSON_VALUE (DATA, '$.AllowPartialShipment'
                  RETURNING BOOLEAN)
-------------------------------------------------------------------------------------------------------
-- Shipping instructions :  state CA
-------------------------------------------------------------------------------------------------------
SELECT  DATA FROM PURCHASEORDERS 
     WHERE JSON_EXISTS(DATA,'$.ShippingInstructions?(@.Address.state == $V1)' 
                    PASSING 'CA' AS "V1");
-------------------------------------------------------------------------------------------------------
-- Shipping instructions :  name Timothy Gates
-------------------------------------------------------------------------------------------------------
SELECT DATA FROM PURCHASEORDERS 
      WHERE JSON_EXISTS( DATA, '$.ShippingInstructions?(@.name == $V1)'
                                   PASSING 'Timothy Gates' AS "V1");
-------------------------------------------------------------------------------------------------------
-- JSON Query
-------------------------------------------------------------------------------------------------------
SELECT JSON_QUERY(DATA,'$.ShippingInstructions')
     FROM PURCHASEORDERS
     where JSON_VALUE(DATA,'$.PONumber' returning number)=1000;

/*
{"name":"Charles Johnson","Address":{"street":"Magdalen Centre, The Isis Science Park","city":"Oxford","county":"Oxon."
,"postcode":"OX9 9ZB","country":"United Kingdom"},"Phone":[{"type":"Office","number":"66-555-3120"}]}    
*/

