-- this demo demonstrates comments and attributes support 
-- requirements: HR sample schema

-- 1. Comments
drop table if exists dept_xml_table;

create table dept_xml_table
as
select department_id, doc_conv.json2xml(JSON{*}) department
from hr.departments;

select *
from dept_xml_table;

declare
    cursor c_dept is select * from dept_xml_table for update;
    de DocElement;
    dj JSON_ELEMENT_T;
    dx XMLType;
    i integer := 0;
begin
    for r in c_dept loop
    
        i := i+1;
        
        de := DocElement(r.department);
        de.addComment('Comment for department : '||r.department_id);
        
        dx := de.getAsXML;
        
        update dept_xml_table
        set department = dx
        where current of c_dept;
    
    end loop;
    commit;
end;
/

select department
from dept_xml_table;

create or replace json collection view dept_json_view
as
select doc_conv.xml2json(department)
from dept_xml_table;

select *
from dept_json_view;

select doc_conv.json2xml(data)
from dept_json_view;

-- 2.Attributes
declare
    cursor c_dept is select * from dept_xml_table for update;
    de DocElement;
    dj JSON_ELEMENT_T;
    dx XMLType;
    da DocAttribute;
    i integer := 0;
begin
    for r in c_dept loop
        de := DocElement(r.department);
        
        select count(*)
        into i
        from hr.employees
        where department_id = r.department_id;
        
        da := DocAttribute('no_of_emps',to_clob(i));
        dbms_output.put_line('i = '||i);
        dbms_output.put_line('key = '||da.key||' val = '||da.val);
        
        de.addAttr(da);
        dx := de.getAsXML;        
        
        update dept_xml_table
        set department = dx
        where current of c_dept;
    
    end loop;
    commit;
end;
/

select *
from dept_xml_table;

select *
from dept_json_view;

select doc_conv.json2xml(data)
from dept_json_view;

declare
    xd XMLType := XMLType('<a attra="val_attr_a"><a1>val_a1</a1><a2>val_a2</a2></a>');
    ed DocElement := DocElement(xd);
    jd JSON_ELEMENT_T := ed.getAsJSON;
begin
    dbms_output.put_line('before attribute to element transformation : ');
    dbms_output.put_line(xd.getclobval);
    dbms_output.put_line(jd.to_String);
    
    ed.attr2element('attra');
    
    xd := ed.getAsXML;
    jd := ed.getAsJSON;
    
    dbms_output.put_line('after attribute to element transformation : ');
    dbms_output.put_line(xd.getclobval);
    dbms_output.put_line(jd.to_String);

    ed.element2attr('a1');
    xd := ed.getAsXML;
    jd := ed.getAsJSON;
    dbms_output.put_line('after element to attribute transformation : ');
    dbms_output.put_line(xd.getclobval);
    dbms_output.put_line(jd.to_String);
end loop;
/
    


