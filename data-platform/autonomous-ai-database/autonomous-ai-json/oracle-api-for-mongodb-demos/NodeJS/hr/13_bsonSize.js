const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function bsonSize() {      
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let session       = client.startSession();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);
    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");
        result = await db.collection("EMPLOYEES_COL").aggregate([
                {
                    "$project": {
                    "last_name": 1,
                    "object_size": { $bsonSize: "$$ROOT" }
                    }
                }
        ]);
        console.log("Results : ");
        for await (doc of result)
            console.log(doc.last_name+" "+doc.object_size);
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}        

bsonSize().catch(console.error);