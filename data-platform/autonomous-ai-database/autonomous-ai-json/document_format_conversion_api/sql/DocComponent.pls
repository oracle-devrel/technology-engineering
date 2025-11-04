create or replace type DocComponent as object
( 
    id integer,
    not instantiable member function getCompType return integer,
    not instantiable member function toString(fmt integer) return clob
)
not instantiable not final;
/