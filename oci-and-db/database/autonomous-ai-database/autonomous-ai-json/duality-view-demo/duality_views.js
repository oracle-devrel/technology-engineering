// list existing collections, dept_v, emp_v and dept_emp_v created at SQL stage are visible
show collections

// the simplest query, which finds all documents in dept_v duality view
db.dept_v.find()


// inserting a new document into dept_v duality view
db.dept_v.insertOne({"_id"            : 310,
                     "departmentName" : "Warehouse",
                     "managerId"      : 202,
                     "locationId"     : 2500}
)

// checking if the document has been inserted correctly
db.dept_v.find({"departmentName" : "Warehouse"})

// moving an employee into newly inserted department - update on emp_v duality view
db.emp_v.update({"_id": 202},
                {$set: 
                 {"departmentId" : 310}
                })

// sample query, which finds all employees with salary greater than 6000
db.emp_v.find({"salary" : { $gt: 6000 } })

// displaying an execution plan of a query, which uses an index on employee_id column
db.emp_v.find({"_id" : { $gt: 120 } }).explain()

// demonstration of remove commands executed on duality views and environment cleaning up
db.emp_v.remove({"_id" : { $gt:206} })

db.emp_v.update({"_id": 202},
                {$set: 
                 {"departmentId" : 310}
                })

db.emp_v.update({"_id": 202},
                {$set: 
                 {"departmentId" : 20}
                })

db.dept_v.remove({"departmentName" : {$in: ["Warehouse","Human Resources","Research and Development"]}})