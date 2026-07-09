drop table if exists doc_params;

create table doc_params
( p_name varchar2(200) primary key,
  p_value varchar2(200) );

insert into doc_params values
( 'XML_ARRAY_NAME','_dc_array_');

insert into doc_params values
( 'XML_ITEM_NAME','_dc_item_');

insert into doc_params values
( 'XML_LIST_NAME','_dc_object_');

insert into doc_params values
( 'JSON_ATTR_NODE','_dc_attrs_');

insert into doc_params values
( 'JSON_NS_NODE','_dc_ns_');

insert into doc_params values
( 'JSON_VAL_NAME' , '_dc_value_');

insert into doc_params values
( 'JSON_COMMENT','_dc_comment_');

insert into doc_params values
( 'JSON_CDATA', '_dc_data_');

insert into doc_params values
( 'IGNORE_XML_COMMENTS','N');

insert into doc_params values
( 'KEEP_DOC_CONV_FMT','N');

commit;

