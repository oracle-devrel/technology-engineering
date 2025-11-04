-- this demo demonstrates basic functionality of Document Conversion API
-- requirements: HR sample schema
drop table if exists emp_xml_table;

create table emp_xml_table OF XMLType
as
select XMLElement("Emp",
                    XMLForest( e.employee_id AS "employee_id",
                    		   e.first_name AS "first_name",
                               e.last_name AS "last_name",
                               e.hire_date AS "hiredate"))
"result" FROM hr.employees e;

-- alternative
drop table if exists emp_xml_table;

create table emp_xml_table of XMLType
as
select doc_conv.json2xml(JSON{*}) employee
from hr.employees;
--
select * from emp_xml_table;    

select doc_conv.xml2json(value(e)) json_col
from emp_xml_table e;

create or replace json collection view emp_json_view
as
select doc_conv.xml2json(value(e)) data
from emp_xml_table e;

select *
from emp_json_view;

mongosh :
db.emp_json_view.find()
db.emp_json_view.find({"SALARY":6200})
db.emp_json_view.find({"SALARY":6200}).explain()




 
