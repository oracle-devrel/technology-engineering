-- arrays
-- requires HR sample schema
set serveroutput on

declare
	de DocElement := DocElement.getArray('select * from hr.employees '||
                                         'where department_id = 90','EMP_90','EMPLOYEE');
	dx XMLType;
	dj JSON_ELEMENT_T;
begin
	dbms_output.put_line('type : '||de.getElType);
	dj := de.getAsJSON;
	dx := de.getAsXML;
	dbms_output.put_line('------- JSON DATA -------');
	dbms_output.put_line(dj.to_String);
	dbms_output.put_line('---- END OF JSON DATA ---');
	dbms_output.put_line('------- XML DATA --------');
	dbms_output.put_line(dx.getClobVal);
	dbms_output.put_line('---- END OF XML DATA ----'); 
end;
/

drop table if exists dept_emp_json_table;
create json collection table dept_emp_json_table;

drop table if exists dept_emp_xml_table;
create table dept_emp_xml_table of XMLType;

declare
	dept_emp_de DocElement := DocElement();
	dept_de DocElement := DocElement();
	emp_de  DocElement := DocElement();
	dept_id DocElement;
	jd JSON_ELEMENT_T;
	xd XMLType;
	jc clob;
begin
	dept_emp_de.setRootKey('DEPARTMENTS');

	for rd in (select JSON{*} dept from hr.departments) loop
		dept_de := DocElement(JSON_ELEMENT_T.parse(JSON_SERIALIZE(rd.dept)));
		dept_de.setRootKey('DEPARTMENT');
		dept_id := dept_de.getElement('DEPARTMENT_ID');
		emp_de := DocElement.getArray('select * from hr.employees where department_id = '||dept_id.val,'EMPLOYEES','EMP');

		if emp_de is not null then
			dept_de.addElement(emp_de);			
		end if;
		
		jd := dept_de.getAsJSON;
		xd := dept_de.getAsXML;
		jc := jd.to_Clob;
		
		insert into dept_emp_json_table values (jc);
		insert into dept_emp_xml_table values (xd);
	end loop;
	commit;
	
end;
/

select *
from dept_emp_json_table;

select *
from dept_emp_xml_table;

-- or

declare
	dept_de DocElement;
	jd JSON_ELEMENT_T;
	xd XMLType;
begin
	for rd in (select JSON{*} dept from hr.departments) loop
		dept_de := DocElement(JSON_ELEMENT_T.parse(JSON_SERIALIZE(rd.dept)));
		dept_de.setRootKey('DEPARTMENT');
		dept_de.aggregate('HR.EMPLOYEES','DEPARTMENT_ID');
		jd := dept_de.getAsJSON;
		xd := dept_de.getAsXML;
		dbms_output.put_line(jd.to_String);
		dbms_output.put_line(xd.getClobVal);
	end loop;	
end;
/

select xmltojson(XMLType('<a><![CDATA[characters with markup]]><b attrb="valb">aaa</b><b>ccc</b></a>'))
select doc_conv.xml2json(XMLType('<a><b attrb="valb">aaa</b><b>ccc</b></a>'))
select jsontoxml(json{*}) from hr.departments;
select doc_conv.json2xml(json{*}) from hr.departments;

