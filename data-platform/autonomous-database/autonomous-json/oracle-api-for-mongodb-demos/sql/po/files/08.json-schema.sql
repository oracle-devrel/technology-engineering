------------------------------------------------------------------------------------
-- JSON schemas can be used to validate the strctucture and type of JSON documents
-- Use cases:
----  1.JSON Schema validation
----  2.Generating JSON schemas
---------------------------------------------------------------------------------------
 

-- JSON Schema Validation without constraint
SELECT JSON_SERIALIZE(data pretty) FROM purchaseorders 
    WHERE data IS JSON VALIDATE
    '{"type"       : "object",
      "properties" : {"PONumber": {"type"    : "number",
                                   "minimum" : 10000}}}';
/*
*/                          
-- Generating JSON SCHEMAS with data guide: 
-- Data guide creates a  JSON schema from an existing set of JSON documents
-- FLAT data guide
SET LONG 1000000 PAGESIZE 1000
SELECT JSON_DATAGUIDE(data,DBMS_JSON.format_flat) 
FROM   PURCHASEORDERS;
/* 
[{"o:path":"$","type":"object","o:length":1},{"o:path":"$._id","type":"id","o:le
ngth":12},{"o:path":"$.User","type":"string","o:length":8},{"o:path":"$.PONumber
","type":"number","o:length":4},{"o:path":"$.LineItems","type":"array","o:length
":1},{"o:path":"$.LineItems.Part","type":"object","o:length":1},{"o:path":"$.Lin
eItems.Part.UPCCode","type":"number","o:length":8},{"o:path":"$.LineItems.Part.U
nitPrice","type":"double","o:length":8},{"o:path":"$.LineItems.Part.Description"
,"type":"json(scalar)","o:length":128},{"o:path":"$.LineItems.Quantity","type":"
number","o:length":2},{"o:path":"$.LineItems.ItemNumber","type":"number","o:leng
th":2},{"o:path":"$.Reference","type":"string","o:length":32},{"o:path":"$.Reque
stor","type":"string","o:length":32},{"o:path":"$.CostCenter","type":"string","o
:length":4},{"o:path":"$.AllowPartialShipment","type":"boolean","o:length":4},{"
o:path":"$.ShippingInstructions","type":"object","o:length":1},{"o:path":"$.Ship
pingInstructions.name","type":"string","o:length":32},{"o:path":"$.ShippingInstr
uctions.Phone","type":"array","o:length":1},{"o:path":"$.ShippingInstructions.Ph
one.type","type":"string","o:length":8},{"o:path":"$.ShippingInstructions.Phone.
number","type":"string","o:length":16},{"o:path":"$.ShippingInstructions.Address
","type":"string","o:length":1},{"o:path":"$.ShippingInstructions.Address","type
":"object","o:length":1},{"o:path":"$.ShippingInstructions.Address.city","type":
"string","o:length":32},{"o:path":"$.ShippingInstructions.Address.state","type":
"string","o:length":2},{"o:path":"$.ShippingInstructions.Address.county","type":
"string","o:length":8},{"o:path":"$.ShippingInstructions.Address.street","type":
"string","o:length":64},{"o:path":"$.ShippingInstructions.Address.country","type
":"string","o:length":32},{"o:path":"$.ShippingInstructions.Address.zipCode","ty
pe":"number","o:length":4},{"o:path":"$.ShippingInstructions.Address.postcode","
type":"json(scalar)","o:length":8},{"o:path":"$.ShippingInstructions.Address.pro
    vince","type":"string","o:length":2},{"o:path":"$.\"Special Instructions\"","typ
    e":"json(scalar)","o:length":32}]                                               


*/

-- Flat format and pretty.
DBMS_JSON.format_hierarchical
-- Hierarchical data guide
SELECT JSON_DATAGUIDE(data, DBMS_JSON.format_hierarchical)
FROM   PURCHASEORDERS;

/* 
{"type":"object","o:length":1,"properties":{"_id":{"type":"id","o:length":12,"o:
preferred_column_name":"_id"},"User":{"type":"string","o:length":8,"o:preferred_
column_name":"User"},"PONumber":{"type":"number","o:length":4,"o:preferred_colum
n_name":"PONumber"},"LineItems":{"type":"array","o:length":1,"o:preferred_column
_name":"LineItems","items":{"properties":{"Part":{"type":"object","o:length":1,"
o:preferred_column_name":"Part","properties":{"UPCCode":{"type":"number","o:leng
th":8,"o:preferred_column_name":"UPCCode"},"UnitPrice":{"type":"double","o:lengt
h":8,"o:preferred_column_name":"UnitPrice"},"Description":{"type":"json(scalar)"
,"o:length":128,"o:preferred_column_name":"Description"}}},"Quantity":{"type":"n
umber","o:length":2,"o:preferred_column_name":"Quantity"},"ItemNumber":{"type":"
number","o:length":2,"o:preferred_column_name":"ItemNumber"}}}},"Reference":{"ty
pe":"string","o:length":32,"o:preferred_column_name":"Reference"},"Requestor":{"
type":"string","o:length":32,"o:preferred_column_name":"Requestor"},"CostCenter"
:{"type":"string","o:length":4,"o:preferred_column_name":"CostCenter"},"AllowPar
tialShipment":{"type":"boolean","o:length":4,"o:preferred_column_name":"AllowPar
tialShipment"},"ShippingInstructions":{"type":"object","o:length":1,"o:preferred
_column_name":"ShippingInstructions","properties":{"name":{"type":"string","o:le
ngth":32,"o:preferred_column_name":"name"},"Phone":{"type":"array","o:length":1,
"o:preferred_column_name":"Phone","items":{"properties":{"type":{"type":"string"
,"o:length":8,"o:preferred_column_name":"type"},"number":{"type":"string","o:len
gth":16,"o:preferred_column_name":"number"}}}},"Address":{"oneOf":[{"type":"stri
ng","o:length":1,"o:preferred_column_name":"Address"},{"type":"object","o:length
":1,"o:preferred_column_name":"Address","properties":{"city":{"type":"string","o
:length":32,"o:preferred_column_name":"city"},"state":{"type":"string","o:length
":2,"o:preferred_column_name":"state"},"county":{"type":"string","o:length":8,"o
:preferred_column_name":"county"},"street":{"type":"string","o:length":64,"o:pre
ferred_column_name":"street"},"country":{"type":"string","o:length":32,"o:prefer
red_column_name":"country"},"zipCode":{"type":"number","o:length":4,"o:preferred
_column_name":"zipCode"},"postcode":{"type":"json(scalar)","o:length":8,"o:prefe
rred_column_name":"postcode"},"province":{"type":"string","o:length":2,"o:prefer
red_column_name":"province"}}}]}}},"Special Instructions":{"type":"json(scalar)"
,"o:length":32,"o:preferred_column_name":"Special Instructions"}}} 
*/

-- Generating JSON SCHEMAS with DBMS_JON_SCHEMA.describe
-- JSON Collection 
SELECT JSON_SERALIZE(
         DBMS_JSON_SCHEMA.describe(
            object_name =>'PURCHASEORDERS')
            ,owner_name => 'SALES_HISTORY');
/*
{                                                                                                                          
  "title" : "PURCHASEORDERS",                                                                                              
  "dbObject" : "SALES_HISTORY.PURCHASEORDERS",                                                                             
  "type" : "object",                                                                                                       
  "dbObjectType" : "table",                                                                                                
  "properties" :                                                                                                           
  {                                                                                                                        
    "DATA" :                                                                                                               
    {                                                                                                                      
      "anyOf" :                                                                                                            
      [                                                                                                                    
        {                                                                                                                  
          "type" : "object",                                                                                               
          "extendedType" : "object"                                                                                        
        }                                                                                                                  
      ]                                                                                                                    
    }                                                                                                                      
  },                                                                                                                       
  "dbPrimaryKey" :                                                                                                         
  [                                                                                                                        
    "RESID"                                                                                                                
  ]                                                                                                                        
}                                                                                                                          
*/

-- Relational table
select JSON_SERIALIZE(DBMS_JSON_SCHEMA.describe(
     object_name =>'SALES'
    ,owner_name => 'SALES_HISTORY')pretty);

/*
{                                                                                                                          
  "title" : "SALES",                                                                                                       
  "dbObject" : "SALES_HISTORY.SALES",                                                                                      
  "description" : "facts table, without a primary key; all rows are uniquely identified by the combination of all foreign k
eys",                                                                                                                      
  "type" : "object",                                                                                                       
  "dbObjectType" : "table",                                                                                                
  "properties" :                                                                                                           
  {                                                                                                                        
    "PROD_ID" :                                                                                                            
    {                                                                                                                      
      "description" : "FK to the products dimension table",                                                                
      "type" : "integer",                                                                                                  
      "extendedType" : "integer",                                                                                          
      "sqlPrecision" : 6                                                                                                   
    },        
    ..........................................
    */

-- Duality view
select JSON_SERIALIZE(DBMS_JSON_SCHEMA.describe(
     object_name =>'PRODUCTS_DV'
    ,owner_name => 'SALES_HISTORY')pretty);

/*
{                                                                                                                          
  "title" : "PRODUCTS_DV",                                                                                                 
  "dbObject" : "SALES_HISTORY.PRODUCTS_DV",                                                                                
  "dbObjectType" : "dualityView",                                                                                          
  "dbObjectProperties" :                                                                                                   
  [                                                                                                                        
    "insert",                                                                                                              
    "update",                                                                                                              
    "check"                                                                                                                
  ],                                                                                                                       
  "type" : "object",                                                                                                       
  "properties" :                                                                                                           
  {                                                                                                                        
    "_id" :                                                                                                                
    {                                                                                                                      
      "type" : "number",                                                                                                   
      "extendedType" : "number",                                                                                           
      "dbFieldProperties" :                                                                                                
      [                                                                                                                    
        "check"                                                                                                            
      ]                                                                                                                    
    },       
*/





-- JSON Document validation report 
-- PURCHASEORDERS JSON Collection 
SET SERVEROUTPUT ON
DECLARE
j_doc    JSON;
j_schema JSON;
    r        JSON;
result   VARCHAR2(2000);

BEGIN
    SELECT DBMS_JSON_SCHEMA.describe(
            object_name =>'PURCHASEORDERS'
            ,owner_name => 'SALES_HISTORY') into j_schema;
     SELECT po.DATA into j_doc FROM PURCHASEORDERS po
     WHERE po.DATA.PONumber=1;
     SELECT DBMS_JSON_SCHEMA.VALIDATE_REPORT (j_doc, j_schema) into r;  
     SELECT JSON_SERIALIZE(r pretty) INTO result;
     DBMS_OUTPUT.PUT_LINE('Result is' || result);     
END;
/
/*
Result is{
  "valid" : true,
  "errors" :
  [
  ]
}
*/
-- JSON Document validation report 
-- SALES Collection 

SET SERVEROUTPUT ON
DECLARE
j_doc    JSON;
j_schema JSON;
    r        JSON;
result   VARCHAR2(2000);

BEGIN
    SELECT DBMS_JSON_SCHEMA.describe(
            object_name =>'SALES'
            ,owner_name => 'SALES_HISTORY') into j_schema;
     SELECT JSON {*} into j_doc FROM SALES WHERE rownum <2;
     SELECT DBMS_JSON_SCHEMA.VALIDATE_REPORT (j_doc, j_schema) into r;  
     SELECT JSON_SERIALIZE(r pretty) INTO result;
     DBMS_OUTPUT.PUT_LINE('Result is' || result);     
END;
/*
Result is{
  "valid" : false,
  "errors" :
  [
    {
      "schemaPath" : "$",
      "instancePath" : "$",
      "code" : "JZN-00501",
      "error" : "JSON schema validation failed"
    },
    {
      "schemaPath" : "$.properties",
      "instancePath" : "$",
      "code" : "JZN-00514",
      "error" : "invalid properties: 'TIME_ID'"
    },
    {
      "schemaPath" : "$.properties.TIME_ID.type",
      "instancePath" : "$.TIME_ID",
      "code" : "JZN-00503",
      "error" : "invalid type found, actual: , expected: string"
    }
  ]
}
*/
 