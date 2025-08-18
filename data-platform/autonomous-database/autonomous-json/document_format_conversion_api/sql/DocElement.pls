create or replace type DocElement under DocComponent (
    
    XML_ARRAY_NAME      varchar2(2000),
    XML_ITEM_NAME       varchar2(2000),
    XML_LIST_NAME       varchar2(2000),
    JSON_ATTR_NODE      varchar2(2000),
    JSON_NS_NODE        varchar2(2000),
    JSON_VAL_NAME       varchar2(2000),
    JSON_COMMENT        varchar2(2000),
    JSON_CDATA          varchar2(2000),
    IGNORE_XML_COMMENTS varchar2(2000),
    KEEP_DOC_CONV_FMT   varchar2(2000),

    key   clob,
    val   clob,
    vtype integer,
    elems CompArray,
    attrs AttrArray,
    array CompArray,
    cdata clob,
    comments clob,
    xns clob,
    xsd clob,
 
    constructor function DocElement
    return self as result,

    constructor function DocElement(eVal clob)
    return self as result,

    constructor function DocElement(eKey clob, eVal clob)
    return self as result,

    constructor function DocElement(xDoc XMLType) 
    return self as result,
    
    constructor function DocElement(jDoc JSON_ELEMENT_T)
    return self as result,

    static function getArray(p_query clob, 
                             arrayName clob := null, 
                             rowName clob := null) return DocElement,

    member function getElType return integer,
    member function getAsXML  (add_def_tokens boolean := true) return XMLType,
    member function getAsJSON (add_def_tokens boolean := true) return JSON_ELEMENT_T,
    
    member function getNoOfElements return integer,
    member function getElement(eKey clob) return DocElement,
    member procedure addElement(eKey clob, eVal clob, nest boolean := false),
    member procedure addElement(elem DocElement, nest boolean := false),
    member procedure delElement(eKey clob),
    member procedure setRootKey(eKey clob),
    member procedure aggregate(tName varchar2, tKey clob),

    member function hasAttrs     return boolean,
    member function getNoOfAttrs return integer,
    member function getAttr(i integer) return DocAttribute,
    member procedure addAttr(aName clob, aVal clob),
    member procedure addAttr(attr DocAttribute),
    member procedure delAttr(aName clob),
    member procedure delAttrs,

    member procedure attr2element(eKey clob),
    member procedure element2attr(eKey clob),

    member function hasComments return boolean,
    member function getComments (fmt integer) return clob,
    member procedure addComment (comment clob),
    member procedure delComments,

    member function hasCData return boolean,
    member function getCData(fmt integer) return clob,
    member procedure addCData(ncdata clob),
    member procedure delCData,

    member procedure setParameter(pName varchar2, pValue varchar2),

    overriding member function getCompType return integer,
    overriding member function toString(fmt integer) return clob
    
);
/
