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
    let oracle_api = !(await isNativeMongoDB(db));
    
    // EMPLOYEES relational table cleaning up
    if (oracle_api) {
        result = db.aggregate([{ $sql: "truncate table employees"}]);
        for await (res of result);
        result = db.aggregate([{ $sql: "truncate table departments"}]);
        for await (res of result);
    }

    // DEPARTMENTS_COL and EMPLOYEES_COL preparation
    let departmentsArrayFile = data_set_dir + "/departments.json";
    let employeesArrayFile   = data_set_dir + "/employees.json";
    let departments = JSON.parse(fs.readFileSync(departmentsArrayFile));
    let employees   = JSON.parse(fs.readFileSync(employeesArrayFile));
 
    // dropping views
    await db.dropCollection("DEPARTMENTS_COL_VW");       //  view based on collection
    if (oracle_api) {
        await db.dropCollection("DEPARTMENTS_TAB_VW");    // JSON Collection view based on table
        await db.dropCollection("DEPARTMENTS_DUAL_VW");   // JSON Duality View based on table
        await db.dropCollection("EMPLOYEES_DUAL_VW");     // JSON Duality View based on table
        await db.dropCollection("DEPT_EMP_COL");
    }

    // dropping collections
    await db.dropCollection("DEPARTMENTS_COL");
    await db.dropCollection("EMPLOYEES_COL");
    await db.dropCollection("DEPARTMENTS_COL_BKP");
 
    // load data into DEPARTMENTS_COL collection
    await db.createCollection("DEPARTMENTS_COL");
    await db.collection("DEPARTMENTS_COL").insertMany(departments);
    // load data into EMPLOYEES_COL collection
    await db.createCollection("EMPLOYEES_COL");
    await db.collection("EMPLOYEES_COL").insertMany(employees);
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = {displayExecutionPlan,displaySQLExecutionPlan,isNativeMongoDB,prepareSchema,getDBVersion,sleep};