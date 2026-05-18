@tables.sql
@DocComponent.pls
@DocAttribute.pls
@arrays.sql
@DocElement.pls
@doc_utl.pls
@doc_utl.plb
@DocAttribute.plb
@DocElement.plb
@doc_conv.pls
@doc_conv.plb
create role dc_role;
grant execute on doc_conv to dc_role;
grant execute on DocElement to dc_role;
grant execute on DocAttribute to dc_role;