const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");
const fs = require('fs');

async function views() {
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));
    let data_set_dir  = process.env.DATA_SET_DIR;
    let departmentsArrayFile = data_set_dir + "/departments.json";
    let employeesArrayFile   = data_set_dir + "/employees.json";

    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");
        if (oracle_api) {
            console.log("You are using Oracle MongoDB API.");
            console.log("Additionally to native MongoDB views you can create :");
            console.log("1. JSON Collection Views - read-only views based on relational tables");
            console.log("2. JSON Duality Views - updateable views based on relational tables");
            console.log("To create such views there is need to use $sql operator and SQL CREATE command ");
            console.log("Creating JSON Collection View DEPARTMENTS_TAB_VW");
            result = db.aggregate([{ $sql: "create json collection view DEPARTMENTS_TAB_VW as "+ 
                                            "select JSON { '_id'             : department_id, "+
                                            "              'department_name' : department_name, "+
                                            "              'manager_id'      : manager_id, "+
                                            "              'location_id'     : location_id } as data " +
                                            "from DEPARTMENTS " }]); 
            for await (res of result);
            console.log("View DEPARTMENTS_TAB_VW has been created.");

            console.log("Creating JSON Duality View DEPARTMENTS_DUAL_VW");
            result = db.aggregate([{ $sql: "create json duality view DEPARTMENTS_DUAL_VW as "+
                                           "DEPARTMENTS @update @insert @delete { "+ 
                                           " _id             : department_id "+
                                           " department_name : department_name "+
                                           " manager_id      : manager_id "+
                                           " location_id     : location_id }"
                                   }]); 
            for await (res of result);    
            console.log("View DEPARTMENTS_DUAL_VW has been created.");

            console.log("Creating JSON Duality view EMPLOYEES_DUAL_VW");
            result = db.aggregate([{ $sql: "create json duality view EMPLOYEES_DUAL_VW as "+
                                           "EMPLOYEES @update @insert @delete { "+ 
                                           " _id            : employee_id "+
                                           " first_name     : first_name  "+
                                           " last_name      : last_name "+
                                           " email          : email "+
                                           " phone_number   : phone_number "+
                                           " hire_date      : hire_date "+
                                           " job_id         : job_id "+
                                           " salary         : salary "+
                                           " commission_pct : commission_pct "+
                                           " manager_id     : manager_id "+
                                           " department_id  : department_id "+
                                           " bonus          : bonus }"
                                   }]);
            for await (res of result);                                    
            console.log("View EMPLOYEES_DUAL_VW created.");
        }
 

        if (oracle_api) {
            // test JSON Collection views and JSON Duality views with updates
            console.log("You are using Oracle MongoDB API. Testing JSON Duality and Collection Views");

            console.log("Loading data into duality views.");
            console.log("1. DEPARTMENTS_DUAL_VW");
            depts = (await db.collection("DEPARTMENTS_COL").find().sort( {"_id" : 1} ).toArray());        
            await db.collection("DEPARTMENTS_DUAL_VW").insertMany(depts);
            console.log("data to DEPARTMENTS_DUAL_VW loaded.");
           
            console.log("2. EMPLOYEES_DUAL_VW");
            emps = db.collection("EMPLOYEES_COL").find().sort( {"_id" : 1} );
            for await (emp of emps)
                await db.collection("EMPLOYEES_DUAL_VW").insertOne({
                        "_id"            : emp._id,
                        "first_name"     : emp.first_name,
                        "last_name"      : emp.last_name,
                        "email"          : emp.email,
                        "phone_number"   : emp.phone_number,
                        "hire_date"      : new Date(emp.hire_date),
                        "job_id"         : emp.job_id,
                        "salary"         : emp.salary,
                        "commission_pct" : emp.commission_pct,
                        "manager_id"     : emp.manager_id,
                        "department_id"  : emp.department_id,
                        "bonus"          : emp.bonus
                    });
            console.log("data to EMPLOYEES_DUAL_VW loaded.");

            console.log("Reading data from EMPLOYEES_DUAL_VW");
            emps = db.collection("EMPLOYEES_DUAL_VW").find({"_id" : 101});
            for await (emp of emps) {
                console.log(emp._id + " "+emp.last_name+" "+emp.salary);
            }
            console.log("Trying to update SALARY for EMPLOYEE_ID #101");
            result = await db.collection("EMPLOYEES_DUAL_VW").updateOne({_id:101},{$set:{salary:24000}});
            console.log("Updated rows : "+result.modifiedCount);
            console.log("Checking new salary of employee #101")
            emps = db.collection("EMPLOYEES_DUAL_VW").find({"_id":101});
            for await (emp of emps) {
                console.log(emp._id + " "+emp.last_name+" "+emp.salary);
            }

            console.log("Reading data from DEPARTMENTS_TAB_VW JSON Collection view");
            depts = db.collection("DEPARTMENTS_TAB_VW").find().sort( {"_id" : 1} );
            for await (dept of depts)
                console.log(dept._id + " : "+dept.department_name);
            try {
                console.log("Trying to update DEPARTMENTS_TAB_VW");
                result = await db.collection("DEPARTMENTS_TAB_VW").updateOne({_id:110},{$set:{department_name:"NoName"}});
            }
            catch(e) {
                console.log("JSON Collection views are read only.");
                console.log("Updates on them raise exceptions.");
                console.log(e);
            }

            // display execution plan of some queries
            console.log("Displaying execution plans of some queries using views.");
            console.log("1. db.DEPARTMENTS_TAB_VIEW.find({_id:110})");
            await utils.displayExecutionPlan(db,"DEPARTMENTS_TAB_VIEW",{_id:110});
            console.log("2. db.EMPLOYEES_DUAL_VIEW.find({salary:{$lte:12000}})");
            await utils.displayExecutionPlan(db,"EMPLOYEES_DUAL_VIEW",{salary:{$lte:12000}});
        }   
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

views().catch(console.error);
