const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function aggregations() {      
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let session       = client.startSession();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);
    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");

        if (oracle_api)
            console.log("You are connected to an Oracle MongoDB API service.");
        else
            console.log("You are connected to a native MongoDB database.");

        // 1. example, which works in all cases: native MongoDB database, MongoDB API instance 
        console.log("Execute an aggregation query. It works in MongoDB native system as well as in MongoDB API connection.");
        console.log("Query : db.EMPLOYEES_COL.aggregate([{ $group : { _id : '$department_id', avgsalary : { $avg : '$salary' } } }])")
        result = db.collection("EMPLOYEES_COL").aggregate([
            { $group : { _id : '$department_id', avgsalary : { $avg : "$salary" } } }
        ]);
        console.log("Results : ");
        for await (doc of result)
            console.log(doc._id+" "+doc.avgsalary);
        console.log("Execution plan : ");
        result = await db.collection("EMPLOYEES_COL").aggregate([
            { $group : { _id : '$department_id', avgsalary : { $avg : "$salary" } } }
        ]).explain();
        if (!oracle_api)
            console.log(result.queryPlanner.winningPlan);
        else
            console.log(result.stages[0].$sql);
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}        

aggregations().catch(console.error);