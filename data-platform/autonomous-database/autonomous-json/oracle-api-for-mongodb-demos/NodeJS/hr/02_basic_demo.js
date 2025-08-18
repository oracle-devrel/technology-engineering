const utils         = require("./00_utils");
const {MongoClient} = require("mongodb");

async function basic_demo() {   
    let client        = new MongoClient(process.env.MONGO_URI);
    let db            = client.db();
    let oracle_api    = !(await utils.isNativeMongoDB(db));

    let colls=[];
    let collName = "";
    let numColls = 0;

    try {
        console.log("Preparing the database schema.");
        await utils.prepareSchema(db);
        console.log("Database schema prepared.");

        if (oracle_api)
            console.log("You are connected to an Oracle MongoDB API service.");
        else
            console.log("You are connected to a native MongoDB database.");
        
        // 1. list databases
        databasesList = await db.admin().listDatabases();
        console.log("Databases:");
        databasesList.databases.forEach(db => console.log(` ${db.name}`));    
    
        // 2. list collections in the default database
        colls = (await db.listCollections().toArray());
        console.log("Number of collections : "+colls.length);
        console.log("Collections : ");
        for ( i = 0; i < colls.length; i++ )
            console.log(" "+colls[i].name);    

        // 3. insert documents into DEPARTMENTS_COL collection
        console.log("Inserting department 120 - HR into DEPARTMENTS_COL collection");
        db.collection("DEPARTMENTS_COL").insertOne(
            {"_id" : 120, "department_name" : "Human Resources"}
        );
        console.log("Department 120, Human Resoures inserted.");
        
        console.log("Inserting departments 130, 140 and 150 using insertMany method");
        db.collection("DEPARTMENTS_COL").insertMany([
            {"_id" : 130, "department_name" : "Department 130"},
            {"_id" : 140, "department_name" : "Department 140"},
            {"_id" : 150, "department_name" : "Department 150"}
        ]);
        console.log("Departments 130, 140 and 150 inserted.");

        // 4. reading data from DEPARTMENTS_COL collection
        console.log("Reading all documents from DEPARTMENTS_COL collection");
        depts = db.collection("DEPARTMENTS_COL").find().sort( {"_id" : 1} );
        for await (dept of depts)
            console.log("id : " + dept._id + " name : " + dept.department_name);
        
        // 5. joining data from two collections
        console.log("Query joining DEPARTMENTS_COL and EMPLOYEES_COL collections");
        depts = db.collection("DEPARTMENTS_COL").aggregate
        ([{ 
            $lookup : { from         : "EMPLOYEES_COL",
                        localField   : "_id",
                        foreignField : "department_id",
                        as           : "EMPLOYEEES" }
        }]);
        for await (dept of depts) {
            console.log(dept);
        }
        
        // 6. create a backup collection and copying the data
        console.log("Creating DEPARTMENTS_COL_BKP collection.");
        await db.createCollection("DEPARTMENTS_COL_BKP");
        console.log("Collection DEPARTMENTS_COL_BKP created.");

        console.log("Copying data from DEPARTMENTS_COL to DEPARTMENTS_COL_BKP.");
        depts = db.collection("DEPARTMENTS_COL").find().sort( {"_id" : 1} );
        for await (dept of depts) {
            await db.collection("DEPARTMENTS_COL_BKP").insertOne(dept);
            console.log("Department #"+dept._id+" copied to backup collection.")
        }
        console.log("Backup completed.");
        console.log("Number of copied documents : " + (await db.collection("DEPARTMENTS_COL_BKP").countDocuments()));
    }   
    catch (e) {
        console.error(e);
    }  
    finally {
        await client.close();
        console.log("Disconnected from database.");
    }
}

basic_demo().catch(console.error);