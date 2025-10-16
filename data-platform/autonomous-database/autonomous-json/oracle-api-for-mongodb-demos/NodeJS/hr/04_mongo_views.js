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

        console.log("Creating view DEPARTMENTS_COL_VW based on DEPARTMENTS_COL collection");
        await db.createCollection("DEPARTMENTS_COL_VW",{viewOn : "DEPARTMENTS_COL", pipeline : [] } ); 
        console.log("DEPARTMENTS_COL_VW read-only view created.");

        
        console.log("Checking the execution plan of a query using the view");
        console.log("Query : db.DEPARTMENTS_COL_VW.find({{ '_id' : {$lte : 80 }}})");
        depts = db.collection("DEPARTMENTS_COL_VW").find({ "_id" : {$lte : 80 }});
        for await (dept of depts) 
            console.log(dept._id+" "+dept.department_name);
        await utils.displayExecutionPlan(db,"DEPARTMENTS_COL_VW",{ "_id" : {$lte : 80 }});
        try {
            console.log("Trying to update DEPARTMENTS_COL_VW");
            result = await db.collection("DEPARTMENTS_COL_VW").updateOne({_id:190},{$set:{department_name:"NoName"}});
            console.log("Number of modified rows : "+result.modifiedCount);
            if (oracle_api) {
                console.log("You are using Oracle MongoDB API.");
                console.log("Updates on collection views don't raise any exceptions, but are just ignored.");
            }
        }
        catch (e) {
            if (!oracle_api)
                console.log("You are connected to a native MongoDB instance. Updates on VIEWS raise exceptions.");
            console.error(e);    
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
