create or replace type body DocElement as

    constructor function DocElement
    return self as result
    is
    begin
        XML_ARRAY_NAME      := doc_utl.get_param('XML_ARRAY_NAME');
        XML_ITEM_NAME       := doc_utl.get_param('XML_ITEM_NAME');
        XML_LIST_NAME       := doc_utl.get_param('XML_LIST_NAME');
        JSON_ATTR_NODE      := doc_utl.get_param('JSON_ATTR_NODE');
        JSON_COMMENT        := doc_utl.get_param('JSON_COMMENT');
        JSON_CDATA          := doc_utl.get_param('JSON_CDATA');
        JSON_NS_NODE        := doc_utl.get_param('JSON_NS_NODE');
        JSON_VAL_NAME       := doc_utl.get_param('JSON_VAL_NAME');
        IGNORE_XML_COMMENTS := doc_utl.get_param('IGNORE_XML_COMMENTS');
        KEEP_DOC_CONV_FMT   := doc_utl.get_param('KEEP_DOC_CONV_FMT');

        key := '';
        val := '';
        vtype := doc_utl.type_null;
        comments := '';
        cdata := '';

        elems := CompArray();
        attrs := AttrArray();
        array := CompArray();
        return;
    end;

    constructor function DocElement(eVal clob)
    return self as result
    is
    begin
        XML_ARRAY_NAME      := doc_utl.get_param('XML_ARRAY_NAME');
        XML_ITEM_NAME       := doc_utl.get_param('XML_ITEM_NAME');
        XML_LIST_NAME       := doc_utl.get_param('XML_LIST_NAME');
        JSON_ATTR_NODE      := doc_utl.get_param('JSON_ATTR_NODE');
        JSON_COMMENT        := doc_utl.get_param('JSON_COMMENT');
        JSON_CDATA          := doc_utl.get_param('JSON_CDATA');
        JSON_NS_NODE        := doc_utl.get_param('JSON_NS_NODE');
        JSON_VAL_NAME       := doc_utl.get_param('JSON_VAL_NAME');
        IGNORE_XML_COMMENTS := doc_utl.get_param('IGNORE_XML_COMMENTS');
        KEEP_DOC_CONV_FMT   := doc_utl.get_param('KEEP_DOC_CONV_FMT');

        key := '';
        val := eVal;
        vtype := doc_utl.val_type(val);
        comments := '';
        cdata := '';

        elems := CompArray();
        attrs := AttrArray();
        array := CompArray();
        return;        
    end;

    constructor function DocElement(eKey clob, eVal clob)
    return self as result
    is
    begin
        XML_ARRAY_NAME      := doc_utl.get_param('XML_ARRAY_NAME');
        XML_ITEM_NAME       := doc_utl.get_param('XML_ITEM_NAME');
        XML_LIST_NAME       := doc_utl.get_param('XML_LIST_NAME');
        JSON_ATTR_NODE      := doc_utl.get_param('JSON_ATTR_NODE');
        JSON_COMMENT        := doc_utl.get_param('JSON_COMMENT');
        JSON_CDATA          := doc_utl.get_param('JSON_CDATA');
        JSON_NS_NODE        := doc_utl.get_param('JSON_NS_NODE');
        JSON_VAL_NAME       := doc_utl.get_param('JSON_VAL_NAME');
        IGNORE_XML_COMMENTS := doc_utl.get_param('IGNORE_XML_COMMENTS');
        KEEP_DOC_CONV_FMT   := doc_utl.get_param('KEEP_DOC_CONV_FMT');

        key := eKey;
        val := eVal;
        vtype := doc_utl.val_type(val);
        comments := '';
        cdata := '';

        elems := CompArray();
        attrs := AttrArray();
        array := CompArray();
        return;    
    end;


    constructor function DocElement(xDoc XMLType) 
    return self as result
    is
        doc_type integer:= doc_utl.doc_type(xDoc);
        tval     clob;
        nDoc     DocElement;
        vDoc XMLType := xDoc;
    begin

        XML_ARRAY_NAME      := doc_utl.get_param('XML_ARRAY_NAME');
        XML_ITEM_NAME       := doc_utl.get_param('XML_ITEM_NAME');
        XML_LIST_NAME       := doc_utl.get_param('XML_LIST_NAME');
        JSON_ATTR_NODE      := doc_utl.get_param('JSON_ATTR_NODE');
        JSON_COMMENT        := doc_utl.get_param('JSON_COMMENT');
        JSON_CDATA          := doc_utl.get_param('JSON_CDATA');
        JSON_NS_NODE        := doc_utl.get_param('JSON_NS_NODE');
        JSON_VAL_NAME       := doc_utl.get_param('JSON_VAL_NAME');
        IGNORE_XML_COMMENTS := doc_utl.get_param('IGNORE_XML_COMMENTS');
        KEEP_DOC_CONV_FMT   := doc_utl.get_param('KEEP_DOC_CONV_FMT');

        key := '';
        val := '';
        vtype := doc_utl.type_null;
        comments := '';
        cdata := '';

        elems := CompArray();
        attrs := AttrArray();
        array := CompArray(); 

        -- comments
        if IGNORE_XML_COMMENTS = 'N' then
            SELECT EXTRACT(xDoc, '/node()/comment()').getStringVal()
	        into comments;
            comments := doc_utl.extractComments(comments);
            cdata := doc_utl.extractCData(vDoc);
            -- namespaces
            -- attributes
        end if;
        for r in (select * from xmltable('/node()/@*' passing  vDoc
                  columns node_name  clob path 'name()',
		          node_value clob path '.')) loop
            attrs.extend;
            attrs(attrs.count) := DocAttribute(r.node_name,r.node_value);                              
        end loop;

        -- components
        if doc_type=doc_utl.doc_simple then

            key := vDoc.getrootelement();
            select extractvalue(vDoc,'/node()')
            into val;
            val := regexp_replace(val,'[[:space:]]');
            vtype := doc_utl.val_type(val);
        elsif doc_type=doc_utl.doc_complex then
            
            if vDoc.getRootElement <> XML_LIST_NAME or KEEP_DOC_CONV_FMT = 'Y'  then
                key := vDoc.getRootElement();
            end if;

            -- text element --
            select extractvalue(vDoc,'/node()/text()')
            into tval;
            tval := regexp_replace(tval,'[[:space:]]');
            --tval := regexp_replace(tval,'<!\[CDATA\[ *(.*?) *\]\]>','',1,1);        
            if tval is not null then
               elems.extend;
               elems(elems.count) := DocElement(replace(tval,' ','')); 
            end if;

            for r in (select * from TABLE(XMLSEQUENCE(EXTRACT(vDoc,'/node()/*')))) loop
                elems.extend;
                elems(elems.count) := DocElement(r.column_value);
            end loop;

        elsif doc_type=doc_utl.doc_list then

            for r in (select * from TABLE(XMLSEQUENCE(EXTRACT(vDoc,'/*')))) loop
                elems.extend;
                if r.column_value.getRootElement <> XML_ITEM_NAME or KEEP_DOC_CONV_FMT = 'Y' then 
                    elems(elems.count) := DocElement(r.column_value); 
                else
                    nDoc := DocElement(r.column_value);
                    nDoc.key := '';
                    elems(elems.count) := nDoc;
                end if;
            end loop;

        elsif doc_type=doc_utl.doc_array then
            if vDoc.getRootElement <> XML_ARRAY_NAME or KEEP_DOC_CONV_FMT = 'Y' then
                key := vDoc.getrootelement();
            end if;

            for r in (select * from TABLE(XMLSEQUENCE(EXTRACT(vDoc,'/node()/*')))) loop   
                array.extend;
                if r.column_value.getRootElement <> XML_ITEM_NAME or KEEP_DOC_CONV_FMT = 'Y' then
                    array(array.count) := DocElement(r.column_value);
                else
                    nDoc := DocElement(r.column_value);
                    nDoc.key := '';
                    array(array.count) := nDoc;
                end if;
            end loop;           

        end if;    
        return;
    end;

    constructor function DocElement(jDoc JSON_ELEMENT_T)
    return self as result
    is
        doc_type integer; 
        jObj     JSON_OBJECT_T;
        njObj    JSON_OBJECT_T;
        jArr     JSON_ARRAY_T;
        nDoc     JSON_ELEMENT_T;
        jDoc2    JSON_ELEMENT_T;
        nVal     clob;
        jKeys    JSON_KEY_LIST;
        njKeys   JSON_KEY_LIST;
        nElem    DocElement;
    begin
        XML_ARRAY_NAME      := doc_utl.get_param('XML_ARRAY_NAME');
        XML_ITEM_NAME       := doc_utl.get_param('XML_ITEM_NAME');
        XML_LIST_NAME       := doc_utl.get_param('XML_LIST_NAME');
        JSON_ATTR_NODE      := doc_utl.get_param('JSON_ATTR_NODE');
        JSON_COMMENT        := doc_utl.get_param('JSON_COMMENT');
        JSON_CDATA          := doc_utl.get_param('JSON_CDATA');
        JSON_NS_NODE        := doc_utl.get_param('JSON_NS_NODE');
        JSON_VAL_NAME       := doc_utl.get_param('JSON_VAL_NAME');
        IGNORE_XML_COMMENTS := doc_utl.get_param('IGNORE_XML_COMMENTS');
        KEEP_DOC_CONV_FMT   := doc_utl.get_param('KEEP_DOC_CONV_FMT');

        key := '';
        val := '';
        vtype := doc_utl.type_null;
        jDoc2 := jDoc;
        comments := doc_utl.extractComments(jDoc2);
        doc_type := doc_utl.doc_type(jDoc2);
        cdata := '';

        elems := CompArray();
        attrs := AttrArray();
        array := CompArray();

        if doc_type = doc_utl.doc_value then
            val := jDoc2.to_Clob;
            vtype := doc_utl.val_type(val);
        elsif doc_type = doc_utl.doc_simple then
            jObj := JSON_OBJECT_T(jDoc2);
            jKeys := jObj.get_Keys;
            key := jKeys(1);
            val := jObj.get_Clob(jKeys(1));
            vtype := doc_utl.val_type(val);
        elsif doc_type = doc_utl.doc_complex then
            jObj := JSON_OBJECT_T(jDoc2);
            jKeys := jObj.get_Keys;
            key := jKeys(1);
            nDoc := jObj.get(key);
            jObj := JSON_OBJECT_T(nDoc);
            jKeys := jObj.get_Keys;
            for i in 1..jKeys.count loop
                nElem := DocElement(jObj.get(jKeys(i)));
                if jKeys(i) <> JSON_VAL_NAME or KEEP_DOC_CONV_FMT = 'Y' then
                    nElem.key := jKeys(i);
                end if;
                elems.extend;
                elems(elems.count) := nElem;
            end loop;
        elsif doc_type = doc_utl.json_array then
            jArr := JSON_ARRAY_T(jDoc2);
            for i in 0..jArr.get_size-1 loop
                array.extend;
                array(array.count) := DocElement(jArr.get(i));
            end loop;

        elsif doc_type = doc_utl.doc_array then
            jObj := JSON_OBJECT_T(jDoc2);
            jKeys := jObj.get_Keys;
            key := jKeys(1);
            nDoc := jObj.get(jKeys(1));
            jArr := JSON_ARRAY_T(nDoc);
            for i in 0..jArr.get_size-1 loop
                array.extend;
                array(array.count) := DocElement(jArr.get(i));
            end loop;        

        elsif doc_type = doc_utl.doc_list then
            jObj := JSON_OBJECT_T(jDoc2);
            jKeys := jObj.get_Keys;
            for i in 1..jKeys.count loop 
                if jKeys(i) = JSON_ATTR_NODE and KEEP_DOC_CONV_FMT = 'N' then
                   nDoc := jObj.get(jKeys(i));
                   if nDoc.is_Object then
                      njObj := JSON_OBJECT_T(nDoc);
                      njKeys := njObj.get_Keys;
                      for j in 1..njKeys.count loop
                          attrs.extend;
                          attrs(attrs.count) := DocAttribute(njKeys(j),njObj.get_Clob(njKeys(j)));
                      end loop;
                   end if; 
                else
                   nDoc := jObj.get(jKeys(i));
                   if (not nDoc.is_Scalar) or nDoc.is_Number then
                       nVal := '{"'||jKeys(i)||'":'||nDoc.to_String||'}';
                    else
                       nVal := '{"'||jKeys(i)||'":'||nDoc.to_String||'}';
                    end if;
                    elems.extend;
                    elems(elems.count) := DocElement(JSON_ELEMENT_T.parse(nVal));
                end if;
            end loop;
        end if; 
        return;
    end;

    static function getArray(p_query clob, 
                             arrayName clob := null, 
                             rowName clob := null) return DocElement
    is
        type json_array_t is table of json;
        json_array json_array_t;
        v_query clob := 'select JSON{*} from ('||p_query||')';
        de DocElement := DocElement();
        di DocElement;
    begin
        execute immediate v_query bulk collect into json_array;
        if json_array.count <> 0 then
            for i in json_array.first..json_array.last loop
                de.array.extend;
                di := DocElement(JSON_ELEMENT_T.parse(JSON_SERIALIZE(json_array(i))));
                de.array(de.array.count) := di;
            end loop;

            if arrayName is not null then
                de.setRootKey(arrayName);
            end if; 
            if rowName is not null then
                de.setParameter('XML_ITEM_NAME',rowName);
            end if;       
            return de;
        end if;
        return null;
    end;

    member function getElType return integer
    is
    begin
        if key is null 
        and val is null 
        and elems.count = 0 
        and array.count = 0 then
            return doc_utl.doc_empty;
        elsif key is null 
          and val is not null 
          and elems.count = 0 
          and array.count = 0 then
            return doc_utl.doc_value;
        elsif key is not null 
          and val is not null  
          and elems.count = 0 
          and array.count = 0 then
            return doc_utl.doc_simple;
        elsif key is not null 
          and val is null
          and elems.count > 0 
          and array.count = 0 then
            return doc_utl.doc_complex;
        elsif key is null 
          and val is null 
          and elems.count > 0 
          and array.count = 0 then
            return doc_utl.doc_list;
        elsif key is null
          and val is null 
          and elems.count = 0 
          and array.count > 0 then
            return doc_utl.json_array;
        elsif key is not null
          and val is null
          and elems.count = 0
          and array.count > 0
        then
            return doc_utl.doc_array;
        elsif key is not null
          and val is null
          and elems.count = 0
          and array.count = 0
        then
            return doc_utl.doc_empty_val;
        else
            return doc_utl.doc_unknown;
        end if;
    end;

    overriding member function getCompType return integer
    is
    begin
        return doc_utl.comp_element;
    end;

    overriding member function toString(fmt integer) return clob
    is
        xd XMLType;
        jd JSON_ELEMENT_T;
    begin
        if fmt = doc_utl.fmt_json then
            jd := getAsJSON;
            return jd.to_String;
        elsif fmt = doc_utl.fmt_xml then
            xd := getAsXML;
            return xd.getclobval;
        end if;
    end;

    member function getAsXML(add_def_tokens boolean := true) return XMLType
    is
        doc_type integer := getElType;
        res      clob := '';
        attrsc   clob := '';
        nel      XMLType;
        ned      DocElement;
        nelc     clob;
    begin
        if hasAttrs then
            for i in 1..attrs.count loop
                attrsc := attrsc||' '||attrs(i).toString(doc_utl.fmt_xml);
            end loop;
        end if;
        if doc_type = doc_utl.doc_empty then
            return null;
        elsif doc_type = doc_utl.doc_empty_val then
            res := '<'||key||attrsc||'></'||key||'>';
        elsif doc_type = doc_utl.doc_value then
            res := '<'||XML_ITEM_NAME||'>'||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml)||val||'</'||XML_ITEM_NAME||'>';
        elsif doc_type = doc_utl.doc_simple then
            res := '<'||key||attrsc||'>'||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml)||val||'</'||key||'>';
        elsif doc_type = doc_utl.doc_complex then
            res := '<'||key||attrsc||'>'||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml);

            for i in 1..elems.count loop
                ned := treat(elems(i) as DocElement);
                if ned.getElType = doc_utl.doc_value then
                    res := res||ned.val;
                else
                    nel := ned.getAsXML(false);
                    res := res||nel.getclobval;
                end if;
            end loop;

            res := res||'</'||key||'>';
        elsif doc_type = doc_utl.doc_array then
            res := '<'||key||attrsc||'>'||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml);
            for i in 1..array.count loop  
                ned := treat(array(i) as DocElement);
                if ned.getElType = doc_utl.doc_list then
                    ned.XML_LIST_NAME := XML_ITEM_NAME;
                    nel := ned.getAsXML;
                    nelc := nel.getClobVal;
                else
                    nel := ned.getAsXML;
                    nelc := '<'||XML_ITEM_NAME||'>'||nel.getClobVal||'</'||XML_ITEM_NAME||'>';
                end if;        
                res := res||nelc;
            end loop;

            res := res||'</'||key||'>';
        elsif doc_type = doc_utl.doc_list then
            if add_def_tokens then
                res := '<'||XML_LIST_NAME||attrsc||'>';
            else
                res := '';
            end if;
            res := res ||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml);
            for i in 1..elems.count loop
                nel := treat(elems(i) as DocElement).getAsXML;                
                res := res||nel.getclobval;
            end loop;

            if add_def_tokens then
                res := res||'</'||XML_LIST_NAME||'>'; -- parameters needed (def list name, item name)
            end if;

        elsif doc_type = doc_utl.json_array then
            res := '<'||XML_ARRAY_NAME||'>'||getComments(doc_utl.fmt_xml)||getCdata(doc_utl.fmt_xml);

            for i in 1..array.count loop
                ned := treat(array(i) as DocElement);
                if ned.getElType = doc_utl.doc_list then
                    ned.XML_LIST_NAME := XML_ITEM_NAME;
                    nel := ned.getAsXML;
                    nelc := nel.getClobVal;
                else
                    nel := ned.getAsXML;
                    nelc := nel.getClobVal;
                end if;        
                res := res||nelc;
            end loop;

            res := res||'</'||XML_ARRAY_NAME||'>'; -- parameters needed (def list name, item name)
        end if;
        return XMLType(res);
    end;

    member function getAsJSON(add_def_tokens boolean := true) return JSON_ELEMENT_T
    is
        doc_type integer := getElType;
        res      clob    := '';
        attrsc   clob    := '';
        tval     clob    := '';
        nJson    JSON_ELEMENT_T;
        nDoc     DocElement;
        ctype varchar2(2000);
    begin
        if hasAttrs then
            attrsc := '"'||JSON_ATTR_NODE||'":{';

            for i in 1..attrs.count loop
                if i > 1 then
                    attrsc := attrsc||',';
                end if;
                attrsc := attrsc||' '||attrs(i).toString(doc_utl.fmt_json); 
            end loop;
            attrsc := attrsc||'}';
        end if;

        if doc_type = doc_utl.doc_empty then
            return null;
        elsif doc_type = doc_utl.doc_empty_val then
            res := '{';
            if hasComments then
                res := res||getComments(doc_utl.fmt_json)||',';
            end if;
            if hasCData then
                res := res||getCData(doc_utl.fmt_json)||',';
            end if;
            res := res||'"'||key||'":null}';
        elsif doc_type = doc_utl.doc_value then
            if vtype <> doc_utl.type_number then
                res := '"'||val||'"';
            else
                res := val;
            end if;
        elsif doc_type = doc_utl.doc_simple then
            res := '{';
            if hasComments then
                res := res||getComments(doc_utl.fmt_json)||',';
            end if;
            if hasCData then
                res := res||getCData(doc_utl.fmt_json)||',';
            end if;
            res := res||'"'||key||'":';
            if hasAttrs then
                res := res || '{'||attrsc||',';
            end if;
            if doc_utl.val_type(val) <> doc_utl.type_number then
                tval := '"'||val||'"';
            else
                tval := val;
            end if;
            if hasAttrs then
                tval := '"'||JSON_VAL_NAME||'":'||tval;
            end if;
            res := res || tval ||'}';
            if hasAttrs then
                res := res||'}';
            end if;
        elsif doc_type = doc_utl.doc_complex then
            res := '{';
            if hasComments then
                res := res||getComments(doc_utl.fmt_json)||',';
            end if;
            if hasCData then
                res := res||getCData(doc_utl.fmt_json)||',';
            end if;
            res := res||'"'||key||'":{';
            if hasAttrs then
                res := res || attrsc||',';
            end if;
            for i in 1..elems.count loop
                if i > 1 then
                    res := res ||',';
                end if;
                nDoc := treat(elems(i) as DocElement);
                if nDoc.getElType = doc_utl.doc_value then
                    tval := '"'||JSON_VAL_NAME||'":';
                    if doc_utl.val_type(nDoc.val) = doc_utl.type_number then
                        tval := tval || nDoc.val;
                    else
                        tval := tval || '"' || nDoc.val || '"';
                    end if;
                else
                    nJson := nDoc.getAsJSON;
                    tval := nJson.to_String;
                    tval := substr(tval,2);
                    tval := substr(tval,1,length(tval)-1);
                end if;
                res := res||tval;
            end loop;
            res := res || '}}';
        elsif doc_type = doc_utl.doc_array then
            res := '{';
            if hasComments then
                res := res||getComments(doc_utl.fmt_json)||',';
            end if;
            if hasCData then
                res := res||getCData(doc_utl.fmt_json)||',';
            end if;
            if hasAttrs then
                res := res || attrsc||',';
            end if;
            res := res||'"'||key||'":[';
            for i in 1..array.count loop
                if i > 1 then
                    res := res ||',';
                end if;

                nDoc := treat(array(i) as DocElement);
                if nDoc.getElType <> doc_utl.doc_value then
                    nJson := nDoc.getAsJSON;
                    tval := nJSon.to_String;
                else
                    if nDoc.vtype <> doc_utl.type_number then
                        tval := '"'||nDoc.val||'"';
                    else
                        tval := nDoc.val; -- was ""
                    end if;
                end if;
                res := res||tval;
            end loop;

            res := res || ']}';
        elsif doc_type = doc_utl.doc_list then
            res := '{';
            if hasComments then
                res := res||getComments(doc_utl.fmt_json)||',';
            end if;
            if hasCData then
                res := res||getCData(doc_utl.fmt_json)||',';
            end if;
            if hasAttrs then
                res := res || attrsc||',';
            end if;
            for i in 1..elems.count loop
                if i > 1 then
                    res := res ||',';
                end if;
                nDoc := treat(elems(i) as DocElement);
                nJson := nDoc.getAsJSON;
                tval := nJson.to_String;
                tval := substr(tval,2);
                tval := substr(tval,1,length(tval)-1);
                res := res || tval;
            end loop;
            res := res||'}';
        elsif doc_type = doc_utl.json_array then
            res := '[';
            for i in 1..array.count loop
                if i > 1 then
                    res := res ||',';
                end if;

                nDoc := treat(array(i) as DocElement);
                if nDoc.getElType = doc_utl.doc_value then
                    if nDoc.vtype = doc_utl.type_number then
                        tval := nDoc.val;
                    else
                        tval := '"'||nDoc.val||'"';
                    end if;
                else
                    nJson := nDoc.getAsJSON;
                    tval := nJson.to_String;
                end if;
                res := res || tval;
            end loop;
            res := res||']';
        end if;
        return JSON_ELEMENT_T.parse(res);
    end;

    member function getNoOfElements return integer
    is
    begin
        if val is not null then
            return 1;
        end if;
        return elems.count;
    end;

    member function getElement(eKey clob) return DocElement
    is
    begin
        if key = eKey then
            return self;
        end if;
        for i in 1..elems.count loop
            if treat(elems(i) as DocElement).key = eKey then
                return treat(elems(i) as DocElement);
            end if;
        end loop;
        return null;
    end;

    member procedure addElement(eKey clob, eVal clob, nest boolean := false)
    is
    begin
        addElement(DocElement(eKey,eVal),nest);
    end;

    member procedure addElement(elem DocElement, nest boolean := false)
    is
        dType integer := getElType;
    begin
        if dType = doc_utl.doc_simple then
            elems.extend;
            if nest then
                elems(elems.count) := DocElement(key,val);
                key := '';
                val := '';
            else
                elems(elems.count) := DocElement(val);
                val := '';
            end if;    
            elems.extend;
            elems(elems.count) := elem;
        elsif dType = doc_utl.doc_complex or dType = doc_utl.doc_list then
            elems.extend;
            elems(elems.count) := elem;
        elsif dType = doc_utl.doc_array or dType = doc_utl.json_array then
            array.extend;
            array(array.count) := elem;
        end if;
    end;

    member procedure delElement(eKey clob)
    is
        dType integer := getElType;        
        de DocElement;
    begin
        if dType = doc_utl.doc_list or dType = doc_utl.doc_complex then
            for i in 1..elems.count loop
                de := treat(elems(i) as DocElement);
                if de.key = eKey then
                    for j in i..elems.count-1 loop
                        elems(j) := elems(j+1);
                    end loop;
                    elems.trim;
                    return;
                end if;
            end loop;
        elsif dType = doc_utl.doc_simple and key = eKey then
            key := '';
            val := '';
        end if;
    end;

    member procedure setRootKey(eKey clob)
    is
        dType integer := getElType;
    begin
        if dType in (doc_utl.doc_list,doc_utl.doc_array,doc_utl.json_array) then
            key := eKey;
        end if;
    end;

    member procedure aggregate(tName varchar2, tKey clob)
    is
        v_query clob := 'select * from '||tNAME||' where '||tKey||' = ';
        deKey DocElement := treat(getElement(tKey) as DocElement);
    begin
        if deKey.getElType = doc_utl.doc_simple then
            v_query := v_query||deKey.val;
        
            deKey := DocElement.getArray(v_query,tName,tKey);
            if deKey is not null then
                addElement(deKey);
            end if;
        end if;
    end;

    member function hasAttrs return boolean
    is
    begin
        if attrs.count > 0 then
            return true;
        end if;
        return false;
    end;

    member function getNoOfAttrs return integer
    is
    begin
        return attrs.count;
    end;

    member function getAttr(i integer) return DocAttribute
    is
    begin
        return attrs(i);
    end;

    member procedure addAttr(aName clob, aVal clob)
    is
    begin
        attrs.extend;
        attrs(attrs.count) := DocAttribute(aName,aVal);
    end;

    member procedure addAttr(attr DocAttribute)
    is
    begin
        attrs.extend;
        attrs(attrs.count) := attr;
    end;

    member procedure delAttr(aName clob)
    is
    begin
        for i in 1..attrs.count loop
            if attrs(i).key = aName then
                for j in i..attrs.count - 1 loop
                    attrs(j) := attrs(j+1);
                end loop;
                attrs.trim;
                return;
            end if;
        end loop;
    end;

    member procedure delAttrs
    is
    begin
        attrs := AttrArray();
    end;

    member procedure attr2element(eKey clob)
    is
        dType integer := getElType; 
    begin
        for i in 1..attrs.count loop
            if attrs(i).key = eKey then
                addElement(attrs(i).key, attrs(i).val);
                for j in i..attrs.count-1 loop
                    attrs(j) := attrs(j+1);
                end loop;
                attrs.trim;
                return;
            end if;
        end loop;
    end;

    member procedure element2attr(eKey clob)
    is
        dType integer := getElType; 
        ed DocElement;
    begin
        for i in 1..elems.count loop
            ed := treat(elems(i) as DocElement);
            if ed.key = eKey and ed.getElType = doc_utl.doc_simple then
                attrs.extend;
                attrs(attrs.count) := DocAttribute(ed.key,ed.val);
                for j in i..elems.count-1 loop
                    elems(j) := elems(j+1);
                end loop;
                elems.trim;
                if elems.count = 1 then
                    ed := treat(elems(elems.count) as DocElement);
                    if ed.getElType = doc_utl.doc_value then
                        val := ed.val;
                        elems.trim;
                    end if;
                end if;
                return;
            end if;
        end loop;
    end;

    member function hasComments return boolean
    is
    begin
        if comments is not null then
            return true;
        end if;
        return false;
    end;

    member function getComments(fmt integer) return clob
    is
    begin
        if fmt = doc_utl.fmt_xml and hasComments then
            return '<!--'||comments||'-->';
        elsif fmt = doc_utl.fmt_json and hasComments then
            return '"'||JSON_COMMENT||'":"'||comments||'"';
        end if;
        return '';
    end;

    member procedure addComment (comment clob)
    is
    begin
        comments := comments||' '||comment;
    end;

    member procedure delComments
    is
    begin   
        comments := '';
    end;

    member function hasCData return boolean
    is
    begin
        if cdata is not null then
            return true;
        end if;
        return false;
    end;

    member function getCData(fmt integer) return clob
    is
    begin
        if fmt = doc_utl.fmt_xml and hasCData then
            return '<![CDATA['||cdata||']]>';
        elsif fmt = doc_utl.fmt_json and hasCData then
            return '"'||JSON_CDATA||'":"'||cdata||'"';
        end if;
        return '';
    end;  

    member procedure addCData(ncdata clob)
    is
    begin
        cdata := cdata||' '||ncdata;
    end;

    member procedure delCData
    is
    begin
        cdata := '';
    end;

    member procedure setParameter(pName varchar2, pValue varchar2)
    is
    begin
        if upper(pName) = 'XML_ITEM_NAME' then
            XML_ITEM_NAME := pValue;
        elsif upper(pName) = 'XML_LIST_NAME' then
            XML_LIST_NAME := pValue;
        elsif upper(pName) = 'JSON_ATTR_NODE' then
            JSON_ATTR_NODE := pValue;
        elsif upper(pName) = 'JSON_NS_NODE' then
            JSON_NS_NODE := pValue;
        elsif upper(pName) = 'JSON_VAL_NAME' then
            JSON_VAL_NAME := pValue;
        elsif upper(pName) = 'JSON_COMMENT' then
            JSON_COMMENT := pValue;
        elsif upper(pName) = 'IGNORE_XML_COMMENTS' then
            IGNORE_XML_COMMENTS := pValue;
        elsif upper(pName) = 'KEEP_DOC_CONV_FMT' then
            KEEP_DOC_CONV_FMT := pValue;
        end if;
    end;
end;
/
