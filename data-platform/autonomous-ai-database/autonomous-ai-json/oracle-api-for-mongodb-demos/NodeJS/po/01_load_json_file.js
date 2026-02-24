const { exit } = require("process");
const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");
const fs = require('fs');

async function load_json_file() {   
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));

    if (!oracle_api) {
        console.log("This demo can be executed against Oracle API for MongoDB only!");
        await client.close();
        exit(0);
    }
    
    try {
        console.log("You are connected to an instance of Oracle API for MongoDB. Starting data loading process.");
        result = db.aggregate([{ $sql: "drop table if exists PURCHASEORDERS_COL cascade constraints"}]);
        for await (res of result);
            
        result = db.aggregate([{ $sql: "create json collection table PURCHASEORDERS_COL"}]);
        numOfDocs = await db.collection("PURCHASEORDERS_COL").countDocuments();
        console.log("Number of documents before loading : "+numOfDocs);
        console.log("Starting loading data.");
        result = db.aggregate([{ $sql: "begin "+
                                        "   DBMS_CLOUD.copy_collection(collection_name => 'PURCHASEORDERS_COL',"+
                                        "              credential_name => 'AJD_CRED',"+
                                        "              file_uri_list => '<URL for PURCHASEORDERS_COL.json file>',"+
                                        "              format => json_object('recorddelimiter' value '''\n'''));"+
                                        "end;" }] ); 
        for await (res of result);
        numOfDocs = await db.collection("PURCHASEORDERS_COL").countDocuments();
        console.log("Data loaded.");
        console.log("Number of loaded documents : "+numOfDocs);
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

load_json_file().catch(console.error);