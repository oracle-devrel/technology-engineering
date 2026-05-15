const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function indexes() { 
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);

    try {               
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");

        if (oracle_api) 
            console.log("Connection to an Oracle MongoDB API instance created.");
        else
            console.log("Connection to a native MongoDB instance created.");

        if (oracle_api && db_version.substr(0,2) >= "23" ) {
             console.log("You are using Oracle Database v."+db_version+". It supports Multivalue Indexes.");
             console.log("Preparing DEPT_EMP_COL collection for this experiment");
             db.createCollection("DEPT_EMP_COL");
             depts = (await db.collection("DEPARTMENTS_COL").aggregate
                         ([{ 
                             $lookup : { from         : "EMPLOYEES_COL",
                                         localField   : "_id",
                                         foreignField : "department_id",
                                         as           : "EMPLOYEES" 
                         }}]).toArray());
             await db.collection("DEPT_EMP_COL").insertMany(depts);
             console.log("DEPT_EMP_COL collection created.");

             console.log("Creating multivalue index.");
             result = db.aggregate([{ $sql: "CREATE MULTIVALUE INDEX MVI_SALARY ON DEPT_EMP_COL c (c.data.EMPLOYEES.salary.numberOnly())"}]);
             for await (res of result);  
             console.log("Multivalue index created.");
            
             console.log("Execution plan, which uses multivalue index.");
             console.log("Query : db.DEPT_EMP_COL.find({EMPLOYEES.salary:8300})");
             console.log("Results : ");
             emps = db.collection("DEPT_EMP_COL").find({"EMPLOYEES.salary":8300});
             for await (emp of emps)
                console.log(emp);
             await utils.displayExecutionPlan(db,"DEPT_EMP_COL",{"EMPLOYEES.salary":8300},"MVI_SALARY");            
        }
        else if (oracle_api)
            console.log("You are using Oracle Database v."+db_version+". This version does not support Multivalue Indexes.");
        else
            console.log("You are using an MongoDB native database. It does not support Multivalue Indexes.");
    
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

indexes().catch(console.error);
