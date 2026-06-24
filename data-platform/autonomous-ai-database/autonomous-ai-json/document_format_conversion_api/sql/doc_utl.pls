create or replace package doc_utl
is
    type t_param_table is table of varchar2(200) index by varchar2(200);
    type t_vc_table is table of varchar2(200) index by binary_integer;

    type_string constant integer := DBMS_TYPES.TYPECODE_VARCHAR2;
    type_number constant integer := DBMS_TYPES.TYPECODE_NUMBER;
    type_date   constant integer := DBMS_TYPES.TYPECODE_DATE;
    type_bool   constant integer := -1;
    type_null   constant integer := -2;

    comp_component constant integer := 1;
    comp_element   constant integer := 2;
    comp_attribute constant integer := 3;

    doc_unknown   constant integer := -1; -- unknown format
    doc_empty     constant integer := 0; -- val,key,lval,array are empty,
    doc_value     constant integer := 1; -- val is not empty; key, lval, array are empty 
    doc_simple    constant integer := 2; -- val,key are not empty; lval, array are empty
    doc_complex   constant integer := 3; -- key, lval are not empty; val, array are empty
    doc_list      constant integer := 4; -- lval is not empty; val, key, array are empty, 
    doc_array     constant integer := 5; -- array is not empty, key is not empty;
    json_array    constant integer := 6; -- array is not empty, key is empty, val is empty, elems is empty
    doc_empty_val constant integer := 7; -- key is not empty, val, lval, array is empty

    fmt_xml        constant integer := 1;
    fmt_json       constant integer := 2;

    params    t_param_table;
    doc_types t_vc_table;

    function doc_type (xDoc XMLType)        return integer;
    function doc_type (jDoc JSON_ELEMENT_T) return integer;
    function doc_type (eDoc DocElement)     return integer;
    function val_type (val clob)            return number;
    function get_param(p_name varchar2)     return varchar2;
    procedure set_param(p_n varchar2,p_val varchar2,permanent boolean := false);

    function extractComments(xmlComments clob)    return clob;
    function extractComments(jDoc in out JSON_ELEMENT_T,
                             pCommentKey varchar2 := params('JSON_COMMENT')) return clob;
    
    function extractCData(xDoc in out XMLType) return clob;
end;
/
