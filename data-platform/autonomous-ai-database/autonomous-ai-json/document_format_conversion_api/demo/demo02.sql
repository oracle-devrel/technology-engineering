-- basic document manipulation
-- requirements: HR demo schema
drop table if exists dept_xml_table;

create table dept_xml_table
as
select department_id, doc_conv.json2xml(JSON{*}) department
from hr.departments;

select *
from dept_xml_table;

create or replace json collection view dept_json_view
as
select doc_conv.xml2json(department)
from dept_xml_table;

select *
from dept_json_view;

declare
	cursor c_dept is select * from dept_xml_table for update;
	de DocElement;
begin
	for r_dept in c_dept loop
		de := DocElement(r_dept.department);
		de.setRootKey('DEPARTMENT');
		
		update dept_xml_table
		set department = de.getAsXML
		where current of c_dept;
	end loop;
	commit;
end;
/

select *
from dept_xml_table;

select *
from dept_json_view;

declare
	cursor c_dept is select * from dept_xml_table for update;
	de DocElement;
begin
	for r_dept in c_dept loop
		de := DocElement(r_dept.department);
		de.delElement('MANAGER_ID');
		
		update dept_xml_table
		set department = de.getAsXML
		where current of c_dept;
	end loop;
	commit;
end;
/

select *
from dept_xml_table;

select *
from dept_json_view;

declare
	cursor c_dept is select * from dept_xml_table for update;
	de DocElement;
	nde DocElement;
	NofEMPS integer;
begin
	for r_dept in c_dept loop
		de := DocElement(r_dept.department);
		nde := de.getElement('DEPARTMENT_ID');
				
		select count(*)
		into NofEMPS
		from hr.employees
		where department_id = to_char(nde.val);
		
		de.addElement('NO_OF_EMPS',to_clob(NofEMPS));
		
		update dept_xml_table
		set department = de.getAsXML
		where current of c_dept;
	end loop;
	commit;
end;
/

select *
from dept_xml_table;

select *
from dept_json_view;
