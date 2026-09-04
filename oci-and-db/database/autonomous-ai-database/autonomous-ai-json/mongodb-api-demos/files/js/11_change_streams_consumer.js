const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function change_streams_consumer() {      
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let session       = client.startSession();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);

    try {           
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db)
        console.log("Database schema prepared.");

        if (oracle_api)
            console.log("You are connected to an Oracle MongoDB API. ");
        else 
            console.log("You are connected to a native MongoDB instance.");
        
        console.log("Enabling changeStreams for DEPARTMENTS_COL collection");

        var commandDoc = {collMod: "DEPARTMENTS_COL",preview:true, enableChangeStream:{preAndPost:true}};

        var results = await db.command(commandDoc);

        console.log(results);

        console.log("changeStreams enabled");
        console.log("Starting to consume events produced by producer's code");

        const collection = db.collection("DEPARTMENTS_COL");
        
        const changeStream = collection.watch();
        // start listen to changes
        console.log("Starting to consume events produced by producer's code");
        
        for (var i=0; i < 25; i++) {
            console.log(await changeStream.next()); 
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

change_streams_consumer().catch(console.error);
