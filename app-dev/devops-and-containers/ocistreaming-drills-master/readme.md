# Start by cloning this repository into your OCI Cloud Shell:

```git
git clone https://github.com/fharris/ocistreaming-drills
cd ocistreaming-drills/
```

# Producing messages to OCI Streaming with Go


*Example from documentation* 
https://docs.oracle.com/en-us/iaas/Content/Streaming/Tasks/streaming-quickstart-oci-sdk-for-go.htm
https://github.com/oracle/oci-go-sdk


```shell
vi producer.go 
```

Update variables according to your OCI configuration file and OCI Streaming Service streamOCID and Endpoint:
```Go
const ociMessageEndpoint = "https://cell-1.streaming.eu-frankfurt-1.oci.oraclecloud.com"
const ociStreamOcid = "ocid1.stream.oc1.eu-frankfurt-1.amaaaaa..."
const ociConfigFilePath = "/home/fernando_h/.oci/config"
const ociProfileName = "DEFAULT"
```

You might need  to update dependencies in mod with below command :
```
go get -d github.com/oracle/oci-go-sdk/v49@latest
```

Then run the application:
```
go run .
```

You sould be able to see a bunch of new messages being sent to OCI Streaming.


# Consuming messages from OCI Streaming with Java

*Example from documentation* 
https://docs.oracle.com/en-us/iaas/Content/Streaming/Tasks/streaming-quickstart-oci-sdk-for-java.htm#java-sdk-streaming-quickstart
https://github.com/oracle/oci-java-sdk


```shell
mvn -B archetype:generate -DgroupId=com.oci.stream -DartifactId=Consumer -DarchetypeArtifactId=maven-archetype-quickstart -DarchetypeVersion=1.4
cd Consumer
vi pom.xml
```

Add dependencies to *pom* file:
```xml
<dependencies>
    <dependency>
      <groupId>com.oracle.oci.sdk</groupId>
      <artifactId>oci-java-sdk-common</artifactId>
      <version>1.33.2</version>
    </dependency>
    <dependency>
      <groupId>com.oracle.oci.sdk</groupId>
      <artifactId>oci-java-sdk-streaming</artifactId>
      <version>1.33.2</version>
    </dependency>
  </dependencies>
```

Copy class Consumer.Java to mvn project location:
```shell
cp ../Consumer.java src/main/java/com/oci/stream/
```

You sould need to update de oci configuration file and the oci stream id and message endpoint:
```java
        final String configurationFilePath = "/home/fernando_h/.oci/config";
        final String profile = "DEFAULT";
        final String ociStreamOcid = "ocid1.stream.oc1.eu-frankfurt-1.amaaaaaaue...";
        final String ociMessageEndpoint = "https://cell-1.streaming.eu-frankfurt-1.oci.oraclecloud.com";
```

Open Consumer.java and update OCI configuration:
```
vi src/main/java/com/oci/stream/Consumer.java
```

Finally, run the application with maven and see the messages previously produced with the Go producer being processed:
```
mvn install exec:java -Dexec.mainClass=com.oci.stream.Consumer
```

You should be able to see the output with the captured messages 
