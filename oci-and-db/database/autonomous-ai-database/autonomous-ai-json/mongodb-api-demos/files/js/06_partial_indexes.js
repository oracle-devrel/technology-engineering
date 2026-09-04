const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function partial_indexes() { 
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);

    try {               
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");

        if (oracle_api) 
            console.log("Connection to an Oracle MongoDB API instance created.");
        else
            console.log("Connection to a native MongoDB instance created.");
        numOfIndexes = (await db.collection("EMPLOYEES_COL").aggregate([{$indexStats:{}}]).toArray()).length;
        console.log("Number of indexes on EMPLOYEES_COL collections BEFORE INDEXING : "+numOfIndexes);
            
        await db.collection("EMPLOYEES_COL").createIndex( { salary: 1, last_name: 1 },
                                                              { partialFilterExpression : { salary: { $lt: 8000 } } } );
            
        numOfIndexes = (await db.collection("EMPLOYEES_COL").aggregate([{$indexStats:{}}]).toArray()).length;
        console.log("Index created succesfully."); 
        console.log("Number of indexes on EMPLOYEES_COL collections AFTER INDEXING : "+numOfIndexes);

        console.log("Execution plan, which uses partial index.");
        console.log("Query: db.EMPLOYEES_COL.find({salary:4200})");
        emps = db.collection("EMPLOYEES_COL").find({salary:4200});
        console.log("Results : ");
        for await (emp of emps)
            console.log(emp._id+" "+emp.last_name+" "+emp.salary);
        await utils.displayExecutionPlan(db,"EMPLOYEES_COL",{SALARY:42000},"salary_1_last_name_1");
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

partial_indexes().catch(console.error);
