const { exit } = require("process");
const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");
const fs = require('fs');

async function partition_test() {   
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));

    if (!oracle_api) {
        console.log("This demo can be executed against Oracle API for MongoDB only!");
        await client.close();
        exit(0);
    }

    try {
        console.log("You are connected to an instance of Oracle API for MongoDB. Starting the demonstration.");
        console.log("Preparing the schema");
        await utils.prepareSchema(db);
        console.log("Schema prepared");

        result = db.aggregate([{ $sql: "DROP TABLE IF EXISTS ORDERS_COL"}]);
        for await (res of result);
        console.log("ORDERS_COL dropped.");
    
        result = db.aggregate([{ $sql: "CREATE JSON COLLECTION TABLE ORDERS_COL"}]);
        for await (res of result);
        console.log("ORDERS_COL created.");

        result = db.aggregate([{$sql: "INSERT INTO ORDERS_COL SELECT * FROM PURCHASEORDERS_COL"}]);
        for await (res of result);
        console.log("Data into ORDERS_COL loaded.");

        result = db.aggregate([{ $sql: "ALTER TABLE ORDERS_COL "+
                                       "ADD (po_num_vc NUMBER GENERATED ALWAYS AS "+
                                       "    (json_value (DATA, '$.PONumber.number()' "+
                                       "     ERROR ON ERROR)))" }]);
        for await (res of result);
        console.log("Partition key added.");

        result = db.aggregate([{$sql: "ALTER TABLE ORDERS_COL "+
                                      "MODIFY PARTITION BY RANGE (po_num_vc) "+
                                      "(PARTITION p1 VALUES LESS THAN (1000), "+
                                      "PARTITION p2 VALUES LESS THAN (2000), "+
                                      "PARTITION p3 VALUES LESS THAN (3000), "+
                                      "PARTITION p4 VALUES LESS THAN (4000), "+
                                      "PARTITION p5 VALUES LESS THAN (5000), "+
                                      "PARTITION p6 VALUES LESS THAN (6000), "+
                                      "PARTITION p7 VALUES LESS THAN (7000), "+
                                      "PARTITION p8 VALUES LESS THAN (8000), "+
                                      "PARTITION p9 VALUES LESS THAN (9000), "+
                                      "PARTITION p10 VALUES LESS THAN (10000), "+
                                      "PARTITION p11 VALUES LESS THAN (11000))"
                                }]);
        for await (res of result);
        console.log("Table ORDERS_COL partitioned.");

        await utils.displayExecutionPlan(db,"ORDERS_COL",{ "PO_NUM_VC" : {$lte : 800 }});  

    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

partition_test().catch(console.error);