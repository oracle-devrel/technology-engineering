package utils.dbutils;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import org.bson.BsonDocument;
import org.bson.Document;

import java.io.*;
import java.time.LocalDateTime;

public class Applier {
    private static int numOfSucceses     = 0;
    private static int numOfErrors       = 0;
    private static int numOfAllCommands  = 0;
    private static String dbName, oldDbname;
    private static MongoClient client;
    private static MongoDatabase db;
    private static BufferedReader inputFile;

    public static void printSettings(boolean footer) {
        if (!footer)
            Config.logMessage(LocalDateTime.now() + " : Starting commands application. ", Config.LOG_LEVEL_SUMMARY);
        else {
            Config.logMessage(LocalDateTime.now() + " : Commands application completed.", Config.LOG_LEVEL_SUMMARY);
            Config.logMessage("Summary", Config.LOG_LEVEL_SUMMARY);
        }

        if (Config.inputFileName != null)
            Config.logMessage("Input file              : " + Config.inputFileName, Config.LOG_LEVEL_SUMMARY);
        else
            Config.logMessage("Input redirected to StdIn", Config.LOG_LEVEL_SUMMARY);

        if (Config.logFileName != null)
            Config.logMessage("Log file                : " + Config.logFileName, Config.LOG_LEVEL_SUMMARY);
        else
            Config.logMessage("Logging set to StdOut.", Config.LOG_LEVEL_SUMMARY);
        Config.logMessage("Log Level               : "+Config.logLevel, Config.LOG_LEVEL_SUMMARY);
        Config.logMessage("Database connect string : "+Config.connectString, Config.LOG_LEVEL_SUMMARY);
        if (footer)
        {
            Config.logMessage("Number of all commands          : " + numOfAllCommands, Config.LOG_LEVEL_SUMMARY);
            Config.logMessage("Number of successful executions : " + numOfSucceses, Config.LOG_LEVEL_SUMMARY);
            Config.logMessage("Number of errors                : " + numOfErrors, Config.LOG_LEVEL_SUMMARY);
        }
    }

    public static void initialize() throws Exception  {
            Config.readConfiguration(Config.APPLY);
            printSettings(false);
            client = MongoClients.create(Config.connectString);
            db     = client.getDatabase(Config.dbName);
            if (Config.inputFileName != null)
                inputFile = new BufferedReader((new FileReader(Config.inputFileName)));
            else
                inputFile = new BufferedReader(new InputStreamReader(System.in));
            dbName = Config.dbName;
            oldDbname = Config.dbName;
    }

    public static synchronized void shutdown() {
            try {
                printSettings(true);
                Config.logFile.close();
            } catch (Exception e) {
                e.printStackTrace();
                System.exit(0);
            }
    }

    public static void main(String[] args) {
        String line = "";
        JsonObject commandJSON;
        BsonDocument commandBSON;
        Document commandResult;

        try {
            initialize();
            while ((line = inputFile.readLine()) != null) {
                numOfAllCommands++;
                try {
                    Config.logMessage("Command #"+numOfAllCommands+" : "+line, Config.LOG_LEVEL_ALL);
                    Gson gson = new Gson();
                    commandJSON = gson.fromJson(line, JsonObject.class);
                    dbName = commandJSON.getAsJsonPrimitive("$db").getAsString();
                    if (!dbName.equals(oldDbname)) {
                        db = client.getDatabase(dbName);
                        oldDbname = dbName;
                    }
                    commandJSON.remove("$db");
                    commandBSON = BsonDocument.parse(commandJSON.toString());
                    commandResult = db.runCommand(commandBSON);
                    Config.logMessage("Result : "+commandResult.toString().substring(8),Config.LOG_LEVEL_ALL);
                    numOfSucceses++;
                } catch(Exception e) {
                    numOfErrors++;
                    Config.logMessage("Error #"+numOfErrors+" : "+line, Config.LOG_LEVEL_ERRORS);
                    Config.logMessage(e.toString(), Config.LOG_LEVEL_ERRORS);
                }
            }
        } catch (Exception e)
        {e.printStackTrace();}
        shutdown();
    }
}
