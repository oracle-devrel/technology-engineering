sqlplus system/Oracle_4U@myoracledb:1521/orclpdb1


BEGIN
    ords_admin.enable_schema (
        p_enabled               => TRUE,
        p_schema                => 'SOE',
        p_url_mapping_type      => 'BASE_PATH',
        p_url_mapping_pattern   => 'soe',
        p_auto_rest_auth        => TRUE   -- this flag says, don't expose my REST APIs
    );
    COMMIT;
END;
/

exit

sqlplus soe/soe@myoracledb:1521/orclpdb1

DECLARE
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN

    ORDS.ENABLE_OBJECT(p_enabled => TRUE,
                       p_schema => 'SOE',
                       p_object => 'CUSTOMERS',
                       p_object_type => 'TABLE',
                       p_object_alias => 'customers',
                       p_auto_rest_auth => FALSE);

    commit;

END;
/

exit

curl -k http://myoracledb:8080/ords/soe/customers/ | jq
curl -k http://myoracledb:8080/ords/soe/customers/73 | jq

-- Replace myoracledb by your public IP and use the URL in an internet browser.


### Link a REST API to SQL query

sqlplus soe/soe@myoracledb:1521/orclpdb1

BEGIN
  ORDS.define_service(
    p_module_name    => 'analytics',
    p_base_path      => 'oe/',
    p_pattern        => 'bymonth/',
    p_method         => 'GET',
    p_source_type    => ORDS.source_type_collection_feed,
    p_source         => 'SELECT to_char(O.order_date,''YYYYMM'') as MONTH, sum(OI.unit_price) as TOTAL FROM orders O, order_items OI where O.order_id = OI.order_id group by to_char(O.order_date,''YYYYMM'')',
    p_items_per_page => 0);
    
  COMMIT;
END;
/

curl -k http://myoracledb:8080/ords/soe/oe/bymonth/ | jq

## With Bind variables 

sqlplus soe/soe@myoracledb:1521/orclpdb1

BEGIN
  ORDS.define_service(
    p_module_name    => 'salesreporting',
    p_base_path      => 'salesrep/',
    p_pattern        => 'sales/:custid',
    p_method         => 'GET',
    p_source_type    => ORDS.source_type_collection_feed,
    p_source         => 'SELECT to_char(O.order_date,''YYYYMM'') as MONTH, sum(OI.unit_price) as TOTAL 
    FROM orders O, order_items OI where O.order_id = OI.order_id and O.customer_id = :custid group by to_char(O.order_date,''YYYYMM'')',
    p_items_per_page => 0);
    
  COMMIT;
END;
/

curl -k http://myoracledb:8080/ords/soe/salesrep/sales/733116 | jq