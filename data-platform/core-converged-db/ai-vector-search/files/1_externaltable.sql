REM Create an external table and check the data set
 
-- copy the data set in the directory DM_DUMP
-- Data set is located [here](https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/fro8fl9kuqli/b/AIVECTORS/o/dataset_200K.txt)

-- connect as user VECTOR_USER and create an external table

connect vector_user/Oracle_4U@FREEPDB1

CREATE TABLE if not exists CCNEWS_TMP (sentence VARCHAR2(4000))
  ORGANIZATION EXTERNAL (TYPE ORACLE_LOADER DEFAULT DIRECTORY dm_dump
                         ACCESS PARAMETERS
                           (RECORDS DELIMITED BY 0x'0A'
                            READSIZE 100000000
                            FIELDS (sentence CHAR(4000)))
                         LOCATION (sys.dm_dump:'dataset_200K.txt'))
  PARALLEL
  REJECT LIMIT UNLIMITED;

-- Check that the external table is correct

select count(*) from CCNEWS_TMP; 

-- Check the 4 first rows

select * from CCNEWS_TMP where rownum < 4;

