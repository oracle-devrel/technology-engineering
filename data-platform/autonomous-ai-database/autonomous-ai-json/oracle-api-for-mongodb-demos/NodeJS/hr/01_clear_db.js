const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function clear_db() {   
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));

    let colls=[];
    let collName = "";
    let numColls = 0;

    try {
        console.log("Cleaning up the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema is clear.");
    }
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

clear_db().catch(console.error);