create or replace package doc_conv
is
    fmt_xml        constant integer := 1;
    fmt_json       constant integer := 2;

    function xml2json_element_t(xDoc XMLType) return JSON_ELEMENT_T; 
    function xml2json(xDoc XMLType) return JSON;
    function json_element_t2xml(jDoc JSON_ELEMENT_T) return XMLType;
    function json2xml(jDoc JSON) return XMLType;
    function get_param(p_name varchar2) return varchar2;
    procedure set_param(p_n varchar2,p_val varchar2,permanent boolean := false);
end;
/