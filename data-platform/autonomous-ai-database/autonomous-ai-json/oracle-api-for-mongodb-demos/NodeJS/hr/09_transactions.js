const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function transactions() {      
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
            console.log("You are connected to an Oracle MongoDB API. ACID transactions are fully supported.");
        else {
            console.log("You are connected to a native MongoDB instance.");
            console.log("Limitations : ");
            console.log("1. Single instance installations do not support transactions at all.");
            console.log("   In that case an exception is raised, when transaction is started.");
            console.log("2. Transactions have mulitple limitations. When a limit is exceeded, transaction is rolled back automatically.");            
        }
        console.log("Test #1 : transaction timeout.");
        
        emps = db.collection("EMPLOYEES_COL").find({_id:107});
        for await (emp of emps)
            console.log("id: "+emp._id + ", last_name: " +emp.last_name + ", salary: "+emp.salary);

        console.log("Starting transaction.");
        session.startTransaction({maxCommitTimeMS: 3000});
        await db.collection("EMPLOYEES_COL").findOneAndUpdate({ "_id" : 107 },
                                                       { $inc: { "salary" : 300 } },
                                                       { session } );
        console.log("Sleeping for 2 seconds.");
        await utils.sleep(2000);
        console.log("Waking up and continuing the work.")
        session.commitTransaction();
        console.log("Transaction commited.");
        
        emps = db.collection("EMPLOYEES_COL").find({"_id" : 107});
        for await (emp of emps)
            console.log("id: "+emp._id + ", last_name: " +emp.last_name + ", salary: "+emp.salary);
        console.log("Test #1 completed.");

        console.log("Test #2 : transaction rollback.");   
        emps = db.collection("EMPLOYEES_COL").find({"_id" : 107});
        for await (emp of emps)
            console.log("id: "+emp._id + ",  salary: " +emp.salary);

        console.log("Starting transaction.");
        session.startTransaction({maxCommitTimeMS: 1000});
        await db.collection("EMPLOYEES_COL").findOneAndUpdate({ "_id" : 107 },
                                                       { $inc: { "salary" : 300 } },
                                                       { session });
        console.log("Aborting transaction.");
        session.abortTransaction();
        console.log("Transaction aborted/rolled back.");
        
        emps = db.collection("EMPLOYEES_COL").find({ "_id" : 107});
        for await (emp of emps)
            console.log("id: "+emp._id + ",  salary: " +emp.salary);
        console.log("Test #2 completed.");   
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

transactions().catch(console.error);
