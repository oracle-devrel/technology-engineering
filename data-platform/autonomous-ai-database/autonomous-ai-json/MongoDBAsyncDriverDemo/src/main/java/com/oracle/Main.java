
package com.oracle;

import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;
import com.mongodb.ServerApi;
import com.mongodb.ServerApiVersion;
import com.mongodb.client.result.InsertManyResult;
import com.mongodb.reactivestreams.client.MongoCollection;
import org.bson.Document;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoClients;
import com.mongodb.reactivestreams.client.MongoDatabase;
import org.reactivestreams.Publisher;
import reactor.core.publisher.Mono;
import java.util.Arrays;
import java.util.List;
import static com.mongodb.client.model.Filters.eq;
//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
public class Main {

    private static MongoDatabase database;
    private static boolean latch = true;


    public static void readSampleData() {
        // due to asynchronous nature of the code there is need to use
        // try-with-resource blocks, they guarantee that all the resources are freed
        // after the execution
        //using reactor package to perform operations in the reactive mode
        String uri = System.getenv("DB_URI");
        ServerApi serverApi = ServerApi.builder()
                .version(ServerApiVersion.V1)
                .build();
        MongoClientSettings settings = MongoClientSettings.builder()
                .applyConnectionString(new ConnectionString(uri))
                .serverApi(serverApi)
                .build();
        try (MongoClient mongoClient = MongoClients.create(settings)) {
            MongoDatabase database = mongoClient.getDatabase("oradev");
            MongoCollection<Document> employees = database.getCollection("EMP_JSON_VIEW");
            Mono.from(employees.find(eq("LAST_NAME", "King")))
                    .doOnSuccess(i -> System.out.println(i))
                    .doOnError(err -> System.out.println("Error: " + err.getMessage()))
                    .block();
        }
    }

    public static void insertData() {
        Document doc1  = new Document("name", "Pink"),
                 doc2  = new Document("name", "Grey"),
                 doc3  = new Document("name","Dark-Green"),
                 doc4  = new Document("name","Magenta"),
                 doc5  = new Document("name","Black"),
                 doc6  = new Document("name","White"),
                 doc7  = new Document("name","Red"),
                 doc8  = new Document("name","Green"),
                 doc9  = new Document("name","Blue"),
                 doc10 = new Document("name","Yellow");

        List<Document> docs = Arrays.asList(doc1,doc2,doc3,doc4,doc5,doc6,doc7,doc8,doc9,doc10);

        String uri = System.getenv("DB_URI");
        ServerApi serverApi = ServerApi.builder()
                .version(ServerApiVersion.V1)
                .build();
        MongoClientSettings settings = MongoClientSettings.builder()
                .applyConnectionString(new ConnectionString(uri))
                .serverApi(serverApi)
                .build();
        try (MongoClient mongoClient = MongoClients.create(settings)) {
            MongoDatabase database = mongoClient.getDatabase("oradev");
            MongoCollection<Document> colors = database.getCollection("colors");

            Publisher<InsertManyResult> iPublisher = colors.insertMany(docs);
            Mono.from(iPublisher).block();
        }
    }

    public static void main(String[] args) {
        readSampleData();
        System.out.println("Data read");
        insertData();
        System.out.println("Data inserted");
    }
}
