const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function expr() { 
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));

    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");

        if (oracle_api)
            console.log("You are connected to an Oracle MongoDB API service.");
        else
            console.log("You are connected to a native MongoDB database.");

        if (!oracle_api) {
           console.log("You are using native MongoDB service. $expr operator is fully supported.");
           emps = db.collection("EMPLOYEES_COL").find({$expr: {$lt: ["$manager_id","$_id"]}});
        }
        else {
           try {
                console.log("Query using $expr operator.");
                console.log("db.EMPLOYEES_COL.find({$expr: {$lt: ['$manager_id','$_id']}})")
                emps = db.collection("EMPLOYEES_COL").find({$expr: {$lt: ["$manager_id","$_id"]}});
                for await (emp of emps) {
                    console.log(emp.last_name + " " + emp.first_name);         
                }  
           }
           catch (e) {
                console.log("You are using Oracle MongoDB API. $epr operator has limited support.");
                console.error(e);
           }
           console.log("You are using Oracle MongoDB API. There is need to use $sql operator instead of $expr.");
           console.log("Query : select c.DATA from EMPLOYEES_COL c where c.DATA.manager_id < c.DATA.'_id'");
           emps = db.aggregate([{ $sql: 'select c.DATA from EMPLOYEES_COL c where c.DATA.manager_id < c.DATA."_id"' }] ); 
           console.log("Execution plan : ");
           await utils.displaySQLExecutionPlan(db,'select c.DATA from EMPLOYEES_COL c where c.DATA.manager_id < c.DATA."_id"');
        }
        for await (emp of emps)
            console.log(emp.last_name + " " + emp.first_name); 
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

expr().catch(console.error);