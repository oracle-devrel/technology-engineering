const {MongoClient} = require('mongodb');
const fs = require('fs');

async function displayExecutionPlan(db,collection,statement,hint) {
    if (hint !== undefined)
        result = await db.collection(collection).find(statement).hint(hint).explain();
    else
        result = await db.collection(collection).find(statement).explain();
    console.log(result.queryPlanner);
}

async function displaySQLExecutionPlan(db,sqlStatement) {
    result = db.aggregate([ {$sql: {statement: sqlStatement}}]).explain();
    console.log((await result).stages[0].$sql);    
}

async function getDBVersion(db) {
    let oracle_api = !(await isNativeMongoDB(db));

    if (oracle_api) {
        result = db.aggregate([{ $sql: "select version_full from product_component_version" }] );
        return (await result.toArray())[0].VERSION_FULL;
    }
    else
        return (await db.admin().serverInfo()).version;
}

async function isNativeMongoDB(db) {    
    return !(await db.admin().serverInfo()).hasOwnProperty("oramlVersion");    
}

async function prepareSchema(db) {
    let data_set_dir  = process.env.DATA_SET_DIR;

    // refreshing PURCHASEORDER_COL collection
            result = db.aggregate([{ $sql: "drop table PURCHASEORDERS_COL cascade constraints"}]);
            for await (res of result);

            result = db.aggregate([{ $sql: "create json collection table PURCHASEORDERS_COL"}]);
            for await (res of result);

            result = db.aggregate([{ $sql: "begin "+
                                           "   DBMS_CLOUD.copy_collection(collection_name => 'PURCHASEORDERS_COL',"+
                                           "              credential_name => 'AJD_CRED',"+
                                           "              file_uri_list => '<URL for PURCHASEORDERS_COL.json file>',"+
                                           "              format => json_object('recorddelimiter' value '''\n'''));"+
                                           "end;" }] ); 
            for await (res of result);
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = {displayExecutionPlan,displaySQLExecutionPlan,isNativeMongoDB,prepareSchema,getDBVersion,sleep};