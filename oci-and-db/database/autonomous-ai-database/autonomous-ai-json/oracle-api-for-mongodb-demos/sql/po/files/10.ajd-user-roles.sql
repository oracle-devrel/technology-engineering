
--------------------------------------------------------------------------------------------------
-- In Autonomous Database the predefined administrative user is ADMIN. This account has privileges
-- to manage users and to manage the database. 
-- Admin roles and prvileges can be queried from ROLE_SYS_PRIVS and DBA_SYS_PRIVS views
--------------------------------------------------------------------------------------------------

SELECT * FROM ROLE_SYS_PRIVS;


SELECT PRIVILEGE FROM DBA_SYS_PRIVS WHERE GRANTEE = 'ADMIN' ORDER BY 1;



------------------------------------------------------------------------------------------------
-- CREATING and ordinary (app dev) user:
-- Oracle Database API for MongoDB relies on Oracle Database users, privileges, and roles. 
-- The minimum Oracle Database roles required to use the API are CONNECT, RESOURCE, and SODA_APP. 
-------------------------------------------------------------------------------------------------
CREATE USER JSONDEV IDENTIFIED BY DB23ee###1234;
-- ADD ROLES
GRANT CONNECT, RESOURCE, SODA_APP TO JSONDEV;
-- QUOTA
ALTER USER JSONDEV QUOTA UNLIMITED ON DATA;
-- Enabling ORDS
BEGIN
 ords_admin.enable_schema(
  p_enabled => TRUE,
  p_schema => 'devuser',
  p_url_mapping_pattern => 'devuser'
 );
 commit;
END;
/ 


-- JSONDEV roles and privileges

SELECT * FROM USER_ROLE_PRIVS;
/*
USERNAME    GRANTED_ROLE    ADMIN_OPTION    DELEGATE_OPTION    DEFAULT_ROLE    OS_GRANTED    COMMON    INHERITED    
___________ _______________ _______________ __________________ _______________ _____________ _________ ____________ 
JSONDEV     CONNECT         NO              NO                 YES             NO            NO        NO           
JSONDEV     RESOURCE        NO              NO                 YES             NO            NO        NO           
JSONDEV     SODA_APP        NO              NO                 YES             NO            NO        NO     
*/


 SELECT * FROM ROLE_SYS_PRIVS;
/*
ROLE        PRIVILEGE                     ADMIN_OPTION    COMMON    INHERITED    
___________ _____________________________ _______________ _________ ____________ 
RESOURCE    CREATE PROPERTY GRAPH         NO              YES       YES          
RESOURCE    CREATE ANALYTIC VIEW          NO              YES       YES          
RESOURCE    CREATE HIERARCHY              NO              YES       YES          
RESOURCE    CREATE ATTRIBUTE DIMENSION    NO              YES       YES          
CONNECT     SET CONTAINER                 NO              YES       YES          
RESOURCE    CREATE INDEXTYPE              NO              YES       YES          
RESOURCE    CREATE OPERATOR               NO              YES       YES          
RESOURCE    CREATE TYPE                   NO              YES       YES          
RESOURCE    CREATE MATERIALIZED VIEW      NO              YES       YES          
RESOURCE    CREATE TRIGGER                NO              YES       YES          
RESOURCE    CREATE PROCEDURE              NO              YES       YES          
RESOURCE    CREATE SEQUENCE               NO              YES       YES          
RESOURCE    CREATE VIEW                   NO              YES       YES          
RESOURCE    CREATE SYNONYM                NO              YES       YES          
RESOURCE    CREATE CLUSTER                NO              YES       YES          
RESOURCE    CREATE TABLE                  NO              YES       YES          
CONNECT     CREATE SESSION                NO              YES       YES          

17 rows selected. 
*/


------------------------------------------------------------------------------------------------
-- An ORACLE user can be switched to read only mode by ADMIN
-------------------------------------------------------------------------------------------------

ALTER USER JSONDEV READ ONLY;

-----------------------------------------------------------------------------------------------------
-- Creating an Administrative user:
-- Administrative users can create new users (database schemas)
-- Oracle database roles  CONNECT, RESOURCE, SODA_APP, CREATE USER, ALTER USER, DROP USER.  
-- Oracle recommends not allow production applications to make use of an administrative user.
-- Applications should instead connect as ordinary users, with a minimum set of privileges
------------------------------------------------------------------------------------------------------

CREATE USER JSONADM IDENTIFIED BY DB23ee###1234;
-- ADD ROLES
GRANT CONNECT, RESOURCE, SODA_APP TO JSONADM;
GRANT CREATE USER, ALTER USER, DROP USER to JSONADM;  
-- QUOTA
ALTER USER JSONDEV QUOTA UNLIMITED ON DATA;
-- Enabling ORDS
BEGIN
 ords_admin.enable_schema(
  p_enabled => TRUE,
  p_schema => 'jsonadm',
  p_url_mapping_pattern => 'jsonadm'
 );
 commit;
END;
/ 

CREATE USER JSONDEV1 IDENTIFIED BY DB23ee###1234;
/* 
User JSONDEV1 created.
*/

DROP USER JSONDEV1;
/*
User JSONDEV1 dropped.
*/


----------------------------------------------------------------------------------------------------------------
----------------  Grants required to load JSON files from  Object Storage ----------------------------------
----------------------------------------------------------------------------------------------------------------

 GRANT EXECUTE on DBMS_CLOUD to JSONDEV
 GRANT READ,WRITE on DIRECTORY data_pump_dir to  JSONDEV