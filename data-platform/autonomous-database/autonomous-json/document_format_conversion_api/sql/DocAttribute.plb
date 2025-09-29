create or replace type body DocAttribute as
    constructor function DocAttribute(aName clob, avalue clob) return self as result
    is
    begin
        key := aName;
        val := aValue;
        return;
    end;
    
    overriding member function getCompType return integer
    is
    begin
        return doc_utl.comp_attribute;
    end;

    overriding member function toString(fmt integer) return clob
    is
    begin
        if fmt = doc_utl.fmt_xml then
            return key||'="'||val||'"';
        elsif fmt = doc_utl.fmt_json then
            return '"'||key||'":"'||val||'"';
        end if;
    end;
end;
/