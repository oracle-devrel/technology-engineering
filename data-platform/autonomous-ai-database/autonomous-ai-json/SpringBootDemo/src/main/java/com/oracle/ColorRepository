package com.oracle;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

public interface ColorRepository extends MongoRepository<Color,String>  {
    @Query
    Color findByName(String Name);
}
