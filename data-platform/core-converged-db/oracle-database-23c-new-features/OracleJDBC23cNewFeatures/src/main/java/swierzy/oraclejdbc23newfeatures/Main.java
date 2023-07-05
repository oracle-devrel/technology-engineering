package swierzy.oraclejdbc23newfeatures;

import java.sql.*;
import oracle.jdbc.*;

import java.util.UUID;
import java.util.concurrent.*;
import oracle.rsi.*;
import java.time.*;

/*
   main application class
   it uses two additional subscriber classes
   1. DMLSubscriber as a subscriber for the INSERT statement being called asynchronously
   2. QuerySubscriber as a subscriber for the SELECT statement being called asynchronously
   it provides two methods demonstrating JDBC 23c new features
   1. reactiveCallsDemo() which demonstrates Oracle JDBC 23c driver support for reactive programming
   2. streamsIngestionDemo() which demonstrates Oracje JDBC 23c driver support for streams ingestion
 */
public class Main {
    private static CountDownLatch latch = new CountDownLatch(2);
    /*
       reactiveCallsDemo: method, which demonstrates reactive programming support
       provided by Oracle23c JDBC driver
     */
    public static void reactiveCallsDemo() throws Exception {
        // database connection used by psDML and psQuery PreparedStatement objects
        Connection con;
        // prepared statements used to call INSERT and SELECT SQL statements in NOWAIT mode
        PreparedStatement psDML, psQuery;

        // database connection creation
        System.out.println("Main.reactiveCallsDemo: connecting to the database.");
        con = DriverManager.getConnection(
                "<db_url>",
                "<db_username>",
                "<db_password>");
        System.out.println("Main.reactiveeCallsDemo: Connected to the database");

        // prepared statements for INSERT and SELECT calls creation
        psDML = con.prepareStatement("INSERT INTO TEST (VAL)"+
                "SELECT DBMS_RANDOM.STRING('a',2000) "+
                "FROM TEST");

        psQuery = con.prepareStatement("SELECT COUNT(*) FROM TEST");

        /*
           INSERT and SELECT statements reactive calls
           notes:
           1. reactive methods are implemented ONLY as Oracle extensions to the standard JDBC interfaces
              - it is not possible to call them without using OraclePrepareStatement class directly
           2. traditional JAVA casting due to Oracle official documentation is not recommended
              - it is needed to use class.unwrap method to get the OraclePreparedStatement object
         */
        Flow.Publisher<OracleResultSet> fpQuery =  psQuery.unwrap(OraclePreparedStatement.class).executeQueryAsyncOracle();
        fpQuery.subscribe(new QuerySubscriber(latch));
        System.out.println("Main.reactiveCallsDemo: SELECT started in NOWAIT mode");

        Flow.Publisher<Long> fpDML = psDML.unwrap(OraclePreparedStatement.class).executeUpdateAsyncOracle();
        fpDML.subscribe(new DMLSubscriber(latch));
        System.out.println("Main.reactiveCallsDemo: INSERT started in NOWAIT mode");
        /*
           As this demo uses reactive methods, the execution does not wait for the end of SQL statements
           reactiveCallsDemo() execution is completed BEFORE completion of INSERT and SELECT statements reactive execution
         */
        System.out.println("Main.reactiveCallsDemo: end of method and return to Main.main.");

    }

    /*
       stramsIngestionDemo(): method, which demonstrates support for Streams Ingestion
       provided by Oracle 23c JDBC driver
     */
    public static void streamsIngestionDemo() throws Exception {
        String value;

        // auxiliary, traditional database connection used to check number of rows in TEST table
        Connection conAux = DriverManager.getConnection(
                "<db_url>",
                "<db_username>",
                "<db_password>");

        // auxiliary PreparedStatement object used to check number of rows in TEST table
        PreparedStatement psAux = conAux.prepareStatement("SELECT COUNT(*) FROM TEST");
        // auxiliary ResultSet object used to check number of rows in TEST table
        ResultSet rsAux;
        int countInt;

        /*
           Streams Ingestion additionally to traditional JDBC parameters, like
           connection string, username and password, requires providing the following data
           1. ExecutorService: pool of threads responsible for execution
           2. buffer size
           3. interval (in seconds) between pushing the data into the database
           4. names of target schema, table and columns
         */

        System.out.println("Main.streamsIngestDemo: connecting to the database.");
        ExecutorService es = Executors.newFixedThreadPool(5);
        ReactiveStreamsIngestion rs = ReactiveStreamsIngestion
                .builder()
                .url("<db_url>")
                .username("<db_username>")
                .password("<db_password>")
                .executor(es)
                .bufferRows(60)
                .bufferInterval(Duration.ofSeconds(2))
                .schema("<db_username>")
                .table("TEST")
                .columns(new String[] {"VAL"})
                .build();
        System.out.println("Main.streamsIngestiondemo: connected to the database");
        // Streams Ingestion uses reactive calls and provides its own publisher and subscriber
        PushPublisher<Object[]> pushPublisher = ReactiveStreamsIngestion.pushPublisher();
        pushPublisher.subscribe(rs.subscriber());
        System.out.println("Main.streamsIngestionDemo: ReactiveStreamsIngestion configured.");

        for (int i = 1; i <= 60; i++) {
            // generation of a random value
            value = UUID.randomUUID().toString();
            // pushing the data into the database
            pushPublisher.accept(new Object[] {value});
            System.out.println("Main.streamsIngestionDemo: A random string #"+i+" has been generated and pushed into the database stream.");

            /*
               Auxiliary PreparedStatement object got from the auxiliary, separate database connection,
               checks the number of rows in the TEST table
            */
            rsAux = psAux.executeQuery();
            rsAux.next();
            countInt = rsAux.getInt(1);
            System.out.println("Main.streamsIngestionDemo: Number of rows in TEST table: "+countInt);
            Thread.sleep(200);
        }

        // closing the stream and the executor service
        pushPublisher.close();
        rs.close();
        es.shutdown();
        System.out.println("Main.streamsIngestionDemo: end of method and return to Main.main.");
    }
    public static void main(String[] args) {
        try {
            System.out.println("Main.main: begin of the demonstration");
            Class.forName("oracle.jdbc.driver.OracleDriver");
            reactiveCallsDemo();
            streamsIngestionDemo();
            System.out.println("Main.main: waiting for DML and Query subscribers");
            latch.await();
            System.out.println("Main.main: end of the demonstration");
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}