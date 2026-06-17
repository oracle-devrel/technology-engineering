const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function lookup_example() {      
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let session       = client.startSession();
    let oracle_api    = !(await utils.isNativeMongoDB(db));  
    let db_version    = await utils.getDBVersion(db);
    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");
        console.log("Simple lookup");
        result = await db.collection("EMPLOYEES_COL").aggregate( [
                {
                    $lookup:
                    {
                        from: "EMPLOYEES_COL",
                        localField: "_id",
                        foreignField: "department_id",
                        as: "EMPLOYEES"
                    }
                }
        ] );
        console.log("Results : ");
        for await (doc of result)
            console.log(doc);
        console.log("Example with lookup, let and pipeline");
        console.log("This example requires database version 23.26.2");
        result = await db.collection("DEPARTMENTS_COL").aggregate( [
        {
            $lookup: {
                from: "EMPLOYEES_COL",
                let: { deptno : "$_id"},
                pipeline: [ {
                    $match: {
                        $expr: {
                            $eq: [ "$$deptno", "$department_id" ] 
                        } 
                    }
                } ],
                as: "matches"
            }
          }
        ] );
        console.log("Results : ");
        for await (doc of result)
            console.log(doc);
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}        

lookup_example().catch(console.error);