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

        if (!oracle_api) {
            console.log("You are connected to a native MongoDB. Partial indexes are natively supported.");
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
        else {
            console.log("You are using Oracle MongoDB API. To create a partial index you need to use:"); 
            console.log("1. $sql operator");
            console.log("2. Function-based Indexes.");
            
            result = db.aggregate([{ $sql: "select * from user_indexes where index_type <> 'LOB' and table_name = 'EMPLOYEES_COL'" }] )
            numOfIndexes = (await result.toArray()).length;
            console.log("Number of indexes on EMPLOYEES_COL collections BEFORE INDEXING : "+numOfIndexes);
            
            result = db.aggregate([ {$sql: {statement: "CREATE INDEX EMPLOYEES_SALARY_IDX on EMPLOYEES_COL(partial_value(DATA))"}}]);
            for await (res of result);

            result = db.aggregate([{ $sql: "select * from user_indexes where index_type <> 'LOB' and table_name = 'EMPLOYEES_COL'" }]);
            numOfIndexes = (await result.toArray()).length;
            console.log("Number of indexes on EMPLOYEES_COL collections AFTER INDEXING : "+numOfIndexes);  
            console.log("Execution plan, which uses partial index.");
            console.log("Query : select c.data from employees_col c where partial_value(data)=4200");
            emps = db.aggregate([{ $sql: "select c.data from employees_col c where partial_value(data)=4200" }] );
            console.log("Results : ");
            for await (emp of emps)
                console.log(emp._id+" "+emp.last_name+" "+emp.salary);
            await utils.displaySQLExecutionPlan(db,"select c.data from employees_col c where partial_value(data)=4200");
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

partial_indexes().catch(console.error);
