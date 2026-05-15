
-- Relational Views using JSON_DATAGUIDE
-------------------------------------------------------------------------------------------------------
-- Creating  a Relational view from PURCHASEORDERS using JSON_DATAGUIDE
-------------------------------------------------------------------------------------------------------
DECLARE
  dg CLOB;
  BEGIN
    SELECT JSON_DATAGUIDE(DATA,
                          DBMS_JSON.FORMAT_HIERARCHICAL,
                          DBMS_JSON.PRETTY)
      INTO dg
      FROM PURCHASEORDERS;
    DBMS_JSON.create_view('PURCHASEORDERS_DG_V',
                          'PURCHASEORDERS',
                          'DATA',
                          dg);
  END;
/


-- Generated View- 

CREATE OR REPLACE VIEW "PURCHASEORDERS_DG_V" ("_id", "User", "PONumber", "Reference", "Requestor", "CostCenter", "AllowPartialShipment", "name", "Address", "city", "state", "county", "street", "country", "zipCode", "postcode", "province", "Special Instructions", "UPCCode", "UnitPrice", "Description", "Quantity", "ItemNumber", "type", "number") AS 
  SELECT JT."_id",JT."User",JT."PONumber",JT."Reference",JT."Requestor",JT."CostCenter",JT."AllowPartialShipment",JT."name",JT."Address",JT."city",JT."state",JT."county",JT."street",JT."country",JT."zipCode",JT."postcode",JT."province",JT."Special Instructions",JT."UPCCode",JT."UnitPrice",JT."Description",JT."Quantity",JT."ItemNumber",JT."type",JT."number"
FROM "PURCHASEORDERS" RT,
JSON_TABLE("DATA", '$[*]' COLUMNS 
      "_id" raw(12) path '$._id',
      "User" varchar2(8) path '$.User',
      "PONumber" number path '$.PONumber',
      NESTED PATH '$.LineItems[*]' COLUMNS (
      "UPCCode" number path '$.Part.UPCCode',
      "UnitPrice" binary_double path '$.Part.UnitPrice',
      "Description" json path '$.Part.Description',
      "Quantity" number path '$.Quantity',
      "ItemNumber" number path '$.ItemNumber'),
      "Reference" varchar2(32) path '$.Reference',
      "Requestor" varchar2(32) path '$.Requestor',
      "CostCenter" varchar2(4) path '$.CostCenter',
      "AllowPartialShipment" varchar2(4) path '$.AllowPartialShipment',
      "name" varchar2(32) path '$.ShippingInstructions.name',
      NESTED PATH '$.ShippingInstructions.Phone[*]' COLUMNS (
            "type" varchar2(8) path '$.type',
            "number" varchar2(16) path '$.number'),
            "Address" varchar2(1) path '$.ShippingInstructions.Address',
            "city" varchar2(32) path '$.ShippingInstructions.Address.city',
            "state" varchar2(2) path '$.ShippingInstructions.Address.state',
            "county" varchar2(8) path '$.ShippingInstructions.Address.county',
            "street" varchar2(64) path '$.ShippingInstructions.Address.street',
            "country" varchar2(32) path '$.ShippingInstructions.Address.country',
            "zipCode" number path '$.ShippingInstructions.Address.zipCode',
            "postcode" json path '$.ShippingInstructions.Address.postcode',
            "province" varchar2(2) path '$.ShippingInstructions.Address.province',
            "Special Instructions" json path '$."Special Instructions"')JT;

-------------------------------------------------------------------------------------------------------
DESCRIBE PURCHASEORDERS_DG_V
;
/*
 Name                 Null?    Type
 -------------------- -------- ---------------------------
 DATE_LOADED                   TIMESTAMP(6) WITH TIME ZONE
 ID                   NOT NULL RAW(16)
 User                          VARCHAR2(8)
 PONumber                      NUMBER
 UPCCode                       NUMBER
 UnitPrice                     NUMBER
 Description                   VARCHAR2(32)
 Quantity                      NUMBER
 ItemNumber                    NUMBER
 Reference                     VARCHAR2(16)
 Requestor                     VARCHAR2(16)
 CostCenter                    VARCHAR2(4)
 AllowPartialShipment          VARCHAR2(4)
 name                          VARCHAR2(16)
 Phone                         VARCHAR2(16)
 type                          VARCHAR2(8)
 number                        VARCHAR2(16)
 city                          VARCHAR2(32)
 state                         VARCHAR2(2)
 street                        VARCHAR2(32)
 country                       VARCHAR2(32)
 zipCode                       NUMBER
 Special Instructions          VARCHAR2(8)
*/


 SELECT  "PONumber" 
    ,"Requestor"
    , "Special Instructions"
    , "zipCode"
    , "UPCCode"
    , "ItemNumber"
    , "Quantity"
    ,"Description"
 FROM 
    PURCHASEORDERS_DG_V
    WHERE "PONumber" =7;

/*
  PONumber Requestor      Special Instructions       zipCode        UPCCode    ItemNumber    Quantity Description                         
___________ ______________ _______________________ __________ ______________ _____________ ___________ ___________________________________ 
          7 Vance Jones    "Hand Carry"                 99236    13131111798             1           3 "The Kentucky Fried Movie"          
          7 Vance Jones    "Hand Carry"                 99236    43396086494             2           4 "The Loves of Carmen"               
          7 Vance Jones    "Hand Carry"                 99236    24543016403             3           7 "Two Girls And A Guy"               
          7 Vance Jones    "Hand Carry"                 99236    25192033926             4           4 "Fear and Loathing in Las Vegas"    
          7 Vance Jones    "Hand Carry"                 99236                                                                             
*/


-------------------------------------------------------------------------------------------------------
-- Creating a View That Projects Scalar Fields Targeted By a Path Expression
-------------------------------------------------------------------------------------------------------
-- Enabling Persistent Support for a JSON Data Guide But Not For Search
CREATE SEARCH INDEX po_dg_only_idx
  ON PURCHASEORDERS (data) FOR JSON
    PARAMETERS ('DATAGUIDE ON SEARCH_ON NONE');


EXEC DBMS_JSON.create_view_on_path('LINEITEMS_C','PURCHASEORDERS','DATA','$.LineItems.Part');

/*
SQL> DESC LINEITEMS_C;

Name                         Null?    Type             
____________________________ ________ ________________ 
DATA$_id                              RAW(12 BYTE)     
DATA$User                             VARCHAR2(8)      
DATA$PONumber                         NUMBER           
DATA$Reference                        VARCHAR2(32)     
DATA$Requestor                        VARCHAR2(32)     
DATA$CostCenter                       VARCHAR2(4)      
DATA$AllowPartialShipment             VARCHAR2(4)      
DATA$name                             VARCHAR2(32)     
DATA$Address                          VARCHAR2(1)      
DATA$city                             VARCHAR2(32)     
DATA$state                            VARCHAR2(2)      
DATA$county                           VARCHAR2(8)      
DATA$street                           VARCHAR2(64)     
DATA$country                          VARCHAR2(32)     
DATA$zipCode                          NUMBER           
DATA$postcode                         VARCHAR2(8)      
DATA$province                         VARCHAR2(2)      
DATA$SpecialInstructions              VARCHAR2(32)     
DATA$UPCCode                          NUMBER           
DATA$UnitPrice                        BINARY_DOUBLE    
DATA$Description                      VARCHAR2(128) 
*/

 