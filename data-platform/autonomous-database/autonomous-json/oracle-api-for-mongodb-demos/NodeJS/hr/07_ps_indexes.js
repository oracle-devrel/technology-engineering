const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function ps_indexes() { 
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

        if ( oracle_api && db_version.substr(0,4) >= "23.6" ) {          
            console.log("You are using Oracle Database v."+db_version+". It supports Path Subsetting Indexes.");
            console.log("Preparing DEPT_EMP_COL collection for this experiment");
            db.createCollection("DEPT_EMP_COL");
            depts = (await db.collection("DEPARTMENTS_COL").aggregate
                        ([{ 
                            $lookup : { from         : "EMPLOYEES_COL",
                                        localField   : "_id",
                                        foreignField : "department_id",
                                        as           : "EMPLOYEES" 
                        }}]).toArray());
            await db.collection("DEPT_EMP_COL").insertMany(depts);
            console.log("DEPT_EMP_COL collection created.");

            result = db.aggregate([{ $sql: "CREATE SEARCH INDEX DEPT_EMP_SEARCH_IDX ON DEPT_EMP_COL (data) "+
                                           "PARAMETERS ('SYNC (ON COMMIT) SEARCH_ON TEXT "+
                                           "INCLUDE ($.department_name, $.employees.salary) VALUE(VARCHAR2, NUMBER) "+ 
                                           "INCLUDE ($.location_id) VALUE(NUMBER)') "
                                }]);
             for await (res of result);  
             console.log("Path Subsetting Search Index created.");
             
             console.log("Execution plan, which uses path subsetting search index");
             console.log("Query : db.DEPT_EMP_COL.find({location_id':1500})");
             depts = db.collection("DEPT_EMP_COL").find({"location_id":1500});
             console.log("Results : ");
             for await (dept of depts)
                console.log(dept); 
             await utils.displayExecutionPlan(db,"DEPT_EMP_COL",{"location_id":3000},"DEPT_EMP_SEARCH_IDX");
        } else if (oracle_api)
            console.log("You are using Oracle Database v."+db_version+". This version does not support Path Subsetting Indexes.");
        else
            console.log("You are using an MongoDB native database. It does not support Path Subsetting Indexes.");    
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

ps_indexes().catch(console.error);
