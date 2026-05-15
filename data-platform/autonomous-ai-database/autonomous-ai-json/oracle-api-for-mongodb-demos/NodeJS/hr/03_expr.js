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

        if (oracle_api) {
            console.log("You are connected to an Oracle MongoDB API service.");
            console.log("This version of API supports $expr operator");
        }
        else
            console.log("You are connected to a native MongoDB database.");

        emps = db.collection("EMPLOYEES_COL").find({$expr: {$lt: ["$manager_id","$_id"]}});
        
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