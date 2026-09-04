
package com.oracle;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.ReplaceOptions;
import org.bson.Document;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.bson.conversions.Bson;

@SpringBootTest
public class MongoTest {
    @Autowired
    ColorRepository colorRepository;

    @Autowired
    MongoTemplate mt;

    Color blue   = new Color("123","blue"),
          grey   = new Color("LU0010001-2000001891770-CAMT053-42","grey"),
          green  = new Color("001","green"),
          yellow = new Color("002","yellow"),
          red    = new Color("003", "red");

    @Test
    void insertTest() {
        try {
            System.out.println("Save test");

            System.out.println(colorRepository.save(blue));
            System.out.println(colorRepository.save(grey));
            System.out.println(colorRepository.save(green));
            System.out.println(colorRepository.save(yellow));
            System.out.println(colorRepository.save(red));

            System.out.println("Save test done.");
        }
        catch(Exception e) {e.printStackTrace();}
    }

    @Test
    void replaceTest() {
        try {
            System.out.println("Replace test");

            MongoCollection<Document> col = mt.getCollection("colors");
            Bson filter = Filters.eq("_id", "LU0010001-2000001891770-CAMT053-42");
            ReplaceOptions replace = new ReplaceOptions().upsert(true);
            Document d = new Document("_id", "LU0010001-2000001891770-CAMT053-42");
            d.append("name", "white");
            col.replaceOne(filter, d, replace);

            System.out.println("End of reeplace test.");
        }
        catch (Exception e) {e.printStackTrace();}
    }

    @Test
    void findTest() {
        try {
            System.out.println("Find test");
            Color c = colorRepository.findByName("red");
            System.out.println(c);
            System.out.println("End of find test");
        }
        catch (Exception e) {e.printStackTrace();}
    }
}
