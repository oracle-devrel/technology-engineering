create or replace type DocAttribute under DocComponent (
    key  clob,
    val  clob,
    
    constructor function DocAttribute(aName clob, avalue clob) return self as result,

    overriding member function getCompType return integer,
    overriding member function toString(fmt integer) return clob

);
/