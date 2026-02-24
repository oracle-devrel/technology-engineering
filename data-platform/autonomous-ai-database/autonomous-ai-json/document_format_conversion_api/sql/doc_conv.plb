create or replace package body doc_conv
is
    function xml2json_element_t(xDoc XMLType) return JSON_ELEMENT_T
    is
    begin
        return DocElement(xDoc).getAsJSON;
    end;

    function xml2json(xDoc XMLType) return JSON
    is
    begin
        return JSON(xml2json_element_t(xDoc).to_Clob);
    end;

    function json_element_t2xml(jDoc JSON_ELEMENT_T) return XMLType
    is
    begin
        return DocElement(jDoc).getAsXML;
    end;

    function json2xml(jDoc JSON) return XMLType
    is
        jc clob;
        jd JSON_ELEMENT_T;
    begin
        select JSON_SERIALIZE(jDoc)
        into jc;

        jd := JSON_ELEMENT_T.parse(jc);

        return json_element_t2xml(jd);
    end;

    function get_param(p_name varchar2) return varchar2
    is
    begin
        return doc_utl.get_param(p_name);
    end;

    procedure set_param(p_n varchar2,p_val varchar2,permanent boolean := false)
    is
    begin
        doc_utl.set_param(p_n,p_val,permanent);
    end;
end;
/