package com.oracle;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.ReplaceOptions;
import com.mongodb.client.model.UpdateOptions;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import org.bson.conversions.Bson;

//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
public class Main {
    public static void main(String[] args) {
        MongoClient client;
        MongoDatabase db;
        String connectString = System.getenv("DB_URI");
        String dbName = System.getenv("DB_NAME");

        try {
            client = MongoClients.create(connectString);
            db = client.getDatabase(dbName);

            System.out.println("Connected!");

            MongoCollection<Document> colors = db.getCollection("colors");
            colors.deleteMany(new Document());
            System.out.println("All documents form colors collection deleted.");

            colors = db.getCollection("colors");
            Document d = new Document("name","black");
            d.append("_id","0001");
            colors.insertOne(d);
            d = new Document("name","yellow");
            colors.insertOne(d);
            d = new Document("name","green");
            colors.insertOne(d);
            System.out.println("Inserts done.");

            Bson filter = Filters.eq("_id", "0001");
            Bson update = Updates.set("name","orange");
            UpdateOptions options = new UpdateOptions().upsert(true);
            System.out.println(colors.updateOne(filter,update,options));
            System.out.println("UPDATE with UPSERT done.");

            ReplaceOptions replace = new ReplaceOptions().upsert(true);
            d = new Document("_id", "0001");
            d.append("name","white");
            colors.replaceOne(filter,d,replace);
            System.out.println("Replace done.");

            System.out.println("Printing all documents from colors collection");
            Bson f = Filters.empty();
            colors.find(f).forEach(doc -> System.out.println(doc.toJson()));

        }
        catch (Exception e) {e.printStackTrace();}
    }
}
