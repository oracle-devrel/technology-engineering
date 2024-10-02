-- this script
-- (re)creates partitioned versions of ORDERS and ORDER_ITEMS tables
-- (re)creates hybrid partitioned versions of ORDERS and ORDER_ITEMS tables
-- loads data to both sets of tables using tables created in lab01.sql 
-- compares the performance of queries executed on internal and hybrid partitioned tables

alter session set nls_language=american;
alter session set nls_territory=america;
alter session set nls_date_format='YYYY-MM-DD';
alter session set nls_timestamp_format='YYYY-MM-DD';

drop table orders_part cascade constraints;
drop table order_items_part cascade constraints;

create table orders_part
partition by range(order_id)
( partition o_p01 values less than (250000),
  partition o_p02 values less than (500000),
  partition o_p03 values less than (750000),
  partition o_p04 values less than (1000000),
  partition o_p05 values less than (1250000),
  partition o_p06 values less than (1500000),
  partition o_p07 values less than (1750000),
  partition o_p08 values less than (maxvalue))  
  as select * from orders;
  
create table order_items_part
partition by range(order_id)
( partition oi_p01 values less than (250000),
  partition oi_p02 values less than (500000),
  partition oi_p03 values less than (750000),
  partition oi_p04 values less than (1000000),
  partition oi_p05 values less than (1250000),
  partition oi_p06 values less than (1500000),
  partition oi_p07 values less than (1750000),
  partition oi_p08 values less than (maxvalue))
  as select * from order_items;

drop table orders_hpart cascade constraints;
drop table order_items_hpart cascade constraints;

begin
  dbms_cloud.create_hybrid_part_table(
    table_name      => 'ORDERS_HPART',
    credential_name => 'DBMS_CLOUD_CREDENTIAL',
    format          => json_object('ignoremissingcolumns' value 'true', 
                                    'removequotes' value 'true', 
                                    'skipheaders' value '1',
                                    'delimiter' value ';',
                                    'timestampformat' value 'YYYY-MM-DD'),
    column_list     => 'ORDER_ID       number(10),
                        ORDER_DATE     timestamp(9),
                        ORDER_MODE     varchar2(30),
                        CUSTOMER_ID    number(10),
                        ORDER_STATUS   number(10),
                        ORDER_TOTAL    number(10,2),
                        SALES_REP_ID   number(10),
                        PROMOTION_ID   number(10)',
    partitioning_clause => 'partition by range (order_id) (
                             partition o_hp01 values less than (250000),
                             partition o_hp02 values less than (500000),
                             partition o_hp03 values less than (750000),
                             partition o_hp04 values less than (1000000),
                             partition o_hp05 values less than (1250000),
                             partition o_hp06 values less than (1500000),
                             partition o_hp07 values less than (1750000) external location (
                              ''https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/orders_p07.dat''),
                             partition o_hp08 values less than (maxvalue) external location (
                              ''https://https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/orders_p08.dat'')
                            )'
  );
end;
/

begin
    dbms_cloud.validate_external_table('orders_hpart');
end;
/

begin
  dbms_cloud.create_hybrid_part_table(
    table_name      => 'order_items_hpart',
    credential_name => 'DBMS_CLOUD_CREDENTIAL',
    format          => json_object('ignoremissingcolumns' value 'true', 
                                    'removequotes' value 'true', 
                                    'skipheaders' value '1',
                                    'delimiter' value ';'),
    column_list     => 'ORDER_ID       number(10),
                        LINE_ITEM_ID   number(10),
                        PRODUCT_ID     number(10),
                        UNIT_PRICE     number(10,2),
                        QUANTITY       number(10)',
    partitioning_clause => 'partition by range (order_id) (
                                partition oi_hp01 values less than (250000),
                                partition oi_hp02 values less than (500000),
                                partition oi_hp03 values less than (750000),
                                partition oi_hp04 values less than (1000000),
                                partition oi_hp05 values less than (1250000),
                                partition oi_hp06 values less than (1500000),
                                partition oi_hp07 values less than (1750000) external location (
                                ''https://https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/order_items_p07.dat''),
                                partition oi_hp08 values less than (maxvalue) external location (
                                ''https://https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/order_items_p08.dat'')
                            )'
  );
end; 
/

begin
    dbms_cloud.validate_external_table('order_items_hpart');
end;
/

insert into orders_hpart
select *
from ORDERS
where order_id < 1500000;

insert into order_items_hpart
select *
from ORDER_ITEMS
where order_id < 1500000;

commit; 

set timing on

prompt "calculating number of rows in ORDERS_PART table"
select count(*) from orders_part;

prompt "calculating number of rows in ORDERS_HPART table"
select count(*) from orders_hpart;

prompt "calculating number of rows in ORDER_ITEMS_PART table"
select count(*) from order_items_part;

prompt "calculating number of rows in ORDER_ITEMS_HPART table"
select count(*) from order_items_HPART;

set timing off