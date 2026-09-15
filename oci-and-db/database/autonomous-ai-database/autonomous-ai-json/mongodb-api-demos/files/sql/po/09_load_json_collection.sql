-------------------------------------------------------------------------------------------------------
---------------- 1. Load JSON Collection (File System) ------------------------------------------------
-------------------------------------------------------------------------------------------------------

--Create DIRECTORY(as system)
CREATE OR REPLACE DIRECTORY order_entry_dir as '/home/oracle';
CREATE OR REPLACE DIRECTORY JSON_LOADER_OUTPUT as '/home/oracle';
GRAN READ, WRITE ANY DIRECTORY to '%1'


 
-- LOAD OPTION 1: CREATE External table using dmp file

DROP TABLE json_dump_file_contents;
CREATE TABLE json_dump_file_contents (json_document  JSON)
  ORGANIZATION EXTERNAL
    (TYPE ORACLE_LOADER DEFAULT DIRECTORY order_entry_dir
                         ACCESS PARAMETERS
                           (RECORDS DELIMITED BY 0x'0A'
                            DISABLE_DIRECTORY_LINK_CHECK
                            BADFILE JSON_LOADER_OUTPUT: 'JSON_DUMPFILE_CONTENTS.bad'
                            LOGFILE JSON_LOADER_OUTPUT: 'JSON_DUMPFILE_CONTENTS.log'
                            FIELDS (json_document CHAR(5000)))
                         LOCATION (order_entry_dir:'PURCHASEORDERS.dmp'))
  PARALLEL
  REJECT LIMIT UNLIMITED;


-- LOAD OPTION 2: CREATE External table using ORACLE_BIGDATA driver
DROP TABLE json_file_contents CASCADE CONSTRAINTS; 
CREATE TABLE json_file_contents (DATA JSON)
    ORGANIZATION EXTERNAL
     (TYPE ORACLE_BIGDATA
      ACCESS PARAMETERS (com.oracle.bigDATA.fileformat = jsondoc)
      LOCATION (order_entry_dir:'PURCHASEORDERS.dmp'))
    PARALLEL
   REJECT LIMIT UNLIMITED;
 
 
-------------------------------------------------------------------------------------------------------
-- Creating a Table With a JSON Column for JSON DATA
-------------------------------------------------------------------------------------------------------
DROP TABLE J_PURCHASEORDER CASCADE CONSTRAINTS;
CREATE TABLE J_PURCHASEORDER
  (id          VARCHAR2 (32) NOT NULL PRIMARY KEY,
   date_loaded TIMESTAMP (6) WITH TIME ZONE,
   pdmpo_document JSON);
   
-- populating  J_PURCHASEORDER

INSERT INTO J_PURCHASEORDER, po_document)
  SELECT SYS_GUID(), SYSTIMESTAMP,json_document
    FROM json_dump_file_contents;
 INSERT INTO PURCHASEORDERS SELECT * FROM json_dump_file_contents; 
 

 -- Copying JSON DATA FROM an External Table To a JSON Collection Table. ( 23ai )

DROP TABLE PURCHASEORDERS CASCADE CONSTRAINTS;
CREATE JSON COLLECTION TABLE  PURCHASEORDERS;
INSERT INTO PURCHASEORDERS SELECT * FROM json_file_contents;  

--checking JSON dictionary views

SELECT * FROM USER_JSON_COLUMNS;
/*
TABLE_NAME        OBJECT_TYPE    COLUMN_NAME    FORMAT    DATA_TYPE    
_________________ ______________ ______________ _________ ____________ 
PURCHASEORDERS    TABLE          DATA           OSON      JSON         */

-------------------------------------------------------------------------------------------------------
-- LOAD OPTION 3 : Load DATA using DBMS_CLOUD 
-------------------------------------------------------------------------------------------------------
-- upload PurchaseOrder.dmp to object store
-- e.g. the object uri is 
-- https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/fro8fl9kuqli/b/bucket-for-ajd-data/o/PurchaseOrders.dmp
 
EXEC DBMS_CLOUD.create_credential(credential_name => 'ajd_cred', username => 'SALES_HISTORY', password => '&1');
 
BEGIN
DBMS_CLOUD.copy_collection(collection_name => 'PURCHASEORDERS'
, credential_name => 'ajd_cred'
, file_uri_list => 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/Nxp67PGb4W2anSsgURMhXmGptTlswzZFbugXkTu4Wy0fDWCbuxvXTvNiyXssrurA/n/fro8fl9kuqli/b/bucket-for-ajd-data/o/PurchaseOrders.dmp'
, format => json_object('recorddelimiter' value '''\n'''));
END;
/
