// this code needs to be executed in mongosh
 for (var i=200; i < 225; i++) 
    db.DEPARTMENTS_COL.insertOne({"_id" : i, "department_name" : "New Department #"+i})
