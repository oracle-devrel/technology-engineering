
package com.oracle;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

@Document(collection = "colors")
public class Color {
    @Id
    private String objectId;

    @Field(name = "name")
    private String name;

    public Color() {}

    public Color(String id, String name) {
        this.objectId = id;
        this.name = name;
    }

    public void setObjectId(String id) {
        this.objectId = id;
    }

    public String getObjectId() {
        return this.objectId;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public String toString() {
        return this.objectId+" : "+this.name;
    }

    @Override
    public final boolean equals(Object o) {
        if (!(o instanceof Color color)) return false;

        return getObjectId().equals(color.getObjectId());
    }
}
