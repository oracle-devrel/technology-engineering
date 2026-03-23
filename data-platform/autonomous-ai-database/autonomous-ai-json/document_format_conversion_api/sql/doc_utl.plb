create or replace package body doc_utl
is
    function doc_type (xDoc XMLType)        return integer
    is
        root       clob := xDoc.getRootElement;
        n_nodes    number(38);
        n_name     clob := '';
        n_old_name clob := '';
        i          integer := 0;
    begin
        if root is null then
            return doc_list;
        end if;

        select count(*)
        into n_nodes
        from (select * 
              from table(XMLSEQUENCE(EXTRACT(xDoc,'/node()/*'))));

        if n_nodes = 0 then
           return doc_simple;
        end if;

        for r in (select * 
                  from TABLE(XMLSEQUENCE(EXTRACT(xDoc,'/node()/*')))) loop
            n_name := r.column_value.getrootelement;    
            if i = 0 then
                n_old_name := n_name;
            elsif n_name <> n_old_name then
                return doc_complex;
            end if;
            i := i+1;
        end loop;
        if i = 1 then
            return doc_complex;
        end if;
        return doc_array;
    end;

    function doc_type (jDoc JSON_ELEMENT_T) return integer
    is
        j_size integer := jDoc.get_Size;
        jObj JSON_OBJECT_T;
        nDoc JSON_ELEMENT_T;
        keys JSON_KEY_LIST;
    begin
        if jDoc.is_Scalar then     --- a
            return doc_value;
        elsif jDoc.is_Object and j_size = 1 then --- {"a": something}
            jObj := JSON_OBJECT_T(jDoc);
            keys := jObj.get_Keys;
            nDoc := jObj.get(keys(1));
            if nDoc.is_Scalar then
                return doc_simple;
            elsif nDoc.is_Object then
                return doc_complex;
            elsif nDoc.is_Array then
                return doc_array;
            end if;
        elsif jDoc.is_Object and j_size > 1 then --- {"a" : "b" , "c": "d" ...}
            return doc_list;
        elsif jDoc.is_Array then
            return json_array;
        end if;
        return 0;
    end;

    function doc_type (eDoc DocElement)     return integer
    is
    begin
        return eDoc.getElType;
    end;

    function val_type (val clob) return number
    is
    begin
        if val is null or length(val) = 0 then
            return type_null;
        end if;

        declare
            vn number(38);
        begin
            vn := to_number(val);
            return type_number;
        exception
            when others then null;
        end;

        declare
            vd date;
        begin
            vd := to_date(val);
            return type_date;
        exception
            when others then null;
        end;        

        if upper(trim(' ' from val)) = 'TRUE'
        or upper(trim(' ' from val)) = 'FALSE' then
            return type_bool;
        end if;

        return type_string;
    end;

    function get_param(p_name varchar2)     return varchar2
    is
    begin
        return params(upper(trim(' ' from p_name)));
    end;
    
    procedure set_param(p_n varchar2,p_val varchar2,permanent boolean := false)
    is
    begin
        params(upper(trim(' ' from p_n))) := p_val;
        if permanent then
            update doc_params
            set p_value = p_val
            where p_name = upper(trim(' ' from p_n));

            commit;
        end if;
    end;

    function extractComments(xmlComments clob) return clob
    is
        res clob;
    begin
        return replace(replace(xmlComments,'<!--',' '),'-->',' ');
    end;

    function extractComments(jDoc in out JSON_ELEMENT_T,
                             pCommentKey varchar2 := params('JSON_COMMENT')) return clob
    is
        v_comments clob := '';
        jObj JSON_OBJECT_T;
        jArr JSON_ARRAY_T;
        jEl  JSON_ELEMENT_T;
    begin
        if jDoc.is_Object then
            jObj := JSON_OBJECT_T(jDoc);
            v_comments := jObj.get_Clob(pCommentKey);
            jObj.remove(pCommentKey);
            jDoc := JSON_ELEMENT_T.parse(jObj.to_Clob);
        end if;
        return v_comments;
    end;

    function extractCData(xDoc in out XMLType) return clob
    is
        xc clob := xDoc.getclobval;
        cd clob := regexp_substr(xc, '<!\[CDATA\[ *(.*?) *\]\]>',1,1);
        xd clob := xDoc.getclobval;
    begin
        xd := replace(xd,cd,'');
        xDoc := XMLType(xd);
        return substr(cd,10,length(cd)-12);
    end;

begin
    doc_types(-1) := 'doc_unknown';
    doc_types(0)  := 'doc_empty';
    doc_types(1)  := 'doc_value';
    doc_types(2)  := 'doc_simple';
    doc_types(3)  := 'doc_complex';
    doc_types(4)  := 'doc_list';
    doc_types(5)  := 'doc_array';
    doc_types(6)  := 'json_array';

    for r in (select * from doc_params) loop
        params(r.p_name) := r.p_value;
    end loop;
end;
/
