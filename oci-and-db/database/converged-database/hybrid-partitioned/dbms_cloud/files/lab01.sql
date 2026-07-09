-- this script
-- (re)creates credentials
-- (re)creates non-partitioned ORDERS and ORDER_ITEMS table
-- loads data to above table from object storage by executing DBMS_CLOUD.COPY_DATA procedure
-- creates external tables with exactly the same data 


alter session set nls_language=american;
alter session set nls_territory=america;
alter session set nls_date_format='YYYY-MM-DD';
alter session set nls_timestamp_format='YYYY-MM-DD';

drop table orders cascade constraints;
drop table order_items cascade constraints;

create table orders 
( ORDER_ID       number(10),
  ORDER_DATE     timestamp(9),
  ORDER_MODE     varchar2(30),
  CUSTOMER_ID    number(10),
  ORDER_STATUS   number(10),
  ORDER_TOTAL    number(10,2),
  SALES_REP_ID   number(10),
  PROMOTION_ID   number(10) );

create table order_items
( ORDER_ID       number(10),
  LINE_ITEM_ID   number(10),
  PRODUCT_ID     number(10),
  UNIT_PRICE     number(10,2),
  QUANTITY       number(10) );

begin
    dbms_credential.drop_credential(credential_name=>'DBMS_CLOUD_CREDENTIAL');
end;
/

begin
    dbms_credential.create_credential(credential_name=>'DBMS_CLOUD_CREDENTIAL',
                                      username=>'<tenancy_user_name>',
                                      password=>'<token>');
end;
/

select *
from   dbms_cloud.list_objects(
        credential_name => 'DBMS_CLOUD_CREDENTIAL',
        location_uri    => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/');

begin
 dbms_cloud.copy_data(
    table_name =>'ORDERS',
    credential_name =>'DBMS_CLOUD_CREDENTIAL',
    file_uri_list =>'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/orders.dat',
    format => json_object('ignoremissingcolumns' value 'true', 
                          'removequotes' value 'true', 
                          'skipheaders' value '1',
                          'delimiter' value ';',
                          'timestampformat' value 'YYYY-MM-DD')
 );
end;
/

begin
 dbms_cloud.copy_data(
    table_name =>'ORDER_ITEMS',
    credential_name =>'DBMS_CLOUD_CREDENTIAL',
    file_uri_list =>'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/order_items.dat',
    format => json_object('ignoremissingcolumns' value 'true', 
                          'removequotes' value 'true', 
                          'skipheaders' value '1',
                          'delimiter' value ';',
                          'timestampformat' value 'YYYY-MM-DD')
 );
end;
/

drop table orders_ext;
drop table order_items_ext;

begin
  dbms_cloud.create_external_table(
    table_name      => 'ORDERS_EXT',
    credential_name => 'DBMS_CLOUD_CREDENTIAL',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/orders.dat',
    column_list     => 'ORDER_ID       number(10),
                        ORDER_DATE     timestamp(9),
                        ORDER_MODE     varchar2(30),
                        CUSTOMER_ID    number(10),
                        ORDER_STATUS   number(10),
                        ORDER_TOTAL    number(10,2),
                        SALES_REP_ID   number(10),
                        PROMOTION_ID   number(10)',
    format          => json_object('ignoremissingcolumns' value 'true', 
                                    'removequotes' value 'true', 
                                    'skipheaders' value '1',
                                    'delimiter' value ';',
                                    'timestampformat' value 'YYYY-MM-DD')
 );
end;
/

begin
    dbms_cloud.validate_external_table('orders_ext');
end;
/

begin
  dbms_cloud.create_external_table(
    table_name      => 'ORDER_ITEMS_EXT',
    credential_name => 'DBMS_CLOUD_CREDENTIAL',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/order_items.dat',
    column_list     => 'ORDER_ID       number(10),
                        LINE_ITEM_ID   number(10),
                        PRODUCT_ID     number(10),
                        UNIT_PRICE     number(10,2),
                        QUANTITY       number(10)',
    format          => json_object('ignoremissingcolumns' value 'true', 
                                    'removequotes' value 'true', 
                                    'skipheaders' value '1',
                                    'delimiter' value ';',
                                    'timestampformat' value 'YYYY-MM-DD')
 );
end;
/

begin
    dbms_cloud.validate_external_table('order_items_ext');
end;
/

set timing on

prompt "calculating number of rows in ORDERS table"
select count(*) from orders;

prompt "calculating number of rows in ORDERS_EXT table"
select count(*) from orders_ext;

prompt "calculating number of rows in ORDER_ITEMS table"
select count(*) from order_items;

prompt "calculating number of rows in ORDER_ITEMS_EXT table"
select count(*) from order_items_ext;

set timing off