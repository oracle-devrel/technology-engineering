package com.oracle;

import oracle.soda.*;
import oracle.soda.rdbms.OracleRDBMSClient;
import oracle.jdbc.datasource.impl.OracleDataSource;
import java.util.List;

public class Main {
    private static OracleDatabase sodaDb;
    private static OracleDatabaseAdmin sodaDbAdmin;
    private static OracleCollection sodaSampleCollection;

    public static void prepareSODAConnection() throws Exception {
        OracleDataSource ods = new OracleDataSource();
        ods.setURL(System.getenv("DB_URL"));
        ods.setUser(System.getenv("DB_USERNAME"));
        ods.setPassword(System.getenv("DB_PASSWORD"));
        OracleRDBMSClient client = new OracleRDBMSClient();
        sodaDb = client.getDatabase(ods.getConnection());
        sodaDbAdmin = sodaDb.admin();
    }

    public static void listExistingCollections() throws Exception {
        List<String> collections = sodaDbAdmin.getCollectionNames();
        System.out.println("Listing existing collections : ");

        for (String name: collections) {
            System.out.println("Collection : "+name);
        }
    }

    public static void resetSampleCollection() {
        try {
            sodaSampleCollection = sodaDb.openCollection("sodaSampleCollection");
            sodaSampleCollection.admin().drop();
            System.out.println("sodaSampleCollection dropped succesfully");
        }
        catch (Exception e) {
            System.out.println("sodaSampleCollection has not been created yet. Dropping was unneeded.");
        }

        try {
            sodaSampleCollection = sodaDbAdmin.createCollection("sodaSampleCollection");
            System.out.println("sodaSampleCollection created succesfully");
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void insertSampleData() throws Exception {
        String docs;
        OracleDocument doc;
        for ( int i = 0; i < 100; i++ ) {
            docs = "{\"name\": \"SampleDoc"+i+"\",\"value\":"+i+"}";
            System.out.println("Inserting document# : "+i+" : "+docs);
            doc = sodaDb.createDocumentFromString(docs);
            sodaSampleCollection.insert(doc);
        }
    }

    public static void findSampleData() throws Exception {
        System.out.println("Looking for document 12");
        OracleCursor cursor = sodaSampleCollection.find().filter("{\"value\":12}").getCursor();
        System.out.println("Results : ");
        while (cursor.hasNext()) {
            OracleDocument doc = cursor.next();
            System.out.println("Key : "+doc.getKey());
            System.out.println("Media type : "+doc.getMediaType());
            System.out.println("Doc : "+doc.getContentAsString());
        }
    }

    public static void closeSODAConnection() throws Exception {
        sodaDbAdmin.getConnection().close();
        System.out.println("Database connection closed succesfully.");
    }

    public static void main(String[] args) {
        try {
            prepareSODAConnection();
            listExistingCollections();
            resetSampleCollection();
            insertSampleData();
            findSampleData();
            closeSODAConnection();
        }
        catch (Exception e) {e.printStackTrace();}
    }
}
