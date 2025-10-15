package utils.dbutils;

import com.google.gson.*;
import com.mongodb.client.*;
import org.bson.Document;
import org.json.*;
import java.io.*;
import java.util.Hashtable;
import java.util.Map;
import java.time.LocalDateTime;

public class Extractor {

    private static String dbName    = "", oldDbName = "";
    private static int numOfCommands        = 0;
    private static int numOfAllEntries      = 0;
    private static Hashtable<String, PrintStream> outputFiles = new Hashtable<String,PrintStream>();
    private static BufferedReader inputFile;
    public static int sem = 0;

    public synchronized static void setSem(int newSem) {
        sem = newSem;
    }

    public static void printSettings(boolean footer) {
        if (!footer)
            Config.logMessage(LocalDateTime.now()+" : Starting analysis. ", Config.LOG_LEVEL_SUMMARY);
        else {
            Config.logMessage(LocalDateTime.now()+" : Analysis completed.", Config.LOG_LEVEL_SUMMARY);
            Config.logMessage("Summary", Config.LOG_LEVEL_SUMMARY);
        }

        if (Config.inputFileName != null)
            Config.logMessage("Input log file                            : "+Config.inputFileName, Config.LOG_LEVEL_SUMMARY);
        else if (Config.connectString != null)
            Config.logMessage("Input set to MongoDB server",Config.LOG_LEVEL_SUMMARY);
        else
            Config.logMessage("Input set to StdIn.", Config.LOG_LEVEL_SUMMARY);

        if (Config.inputFileFormat == 0)
            Config.logMessage("Input file format set to                  : MongoDB", Config.LOG_LEVEL_SUMMARY);
        else if (Config.inputFileFormat == 1)
            Config.logMessage("Input file format set to                  : Atlas", Config.LOG_LEVEL_SUMMARY);
        else
            Config.logMessage("Data read directly from system.profile collection",Config.LOG_LEVEL_SUMMARY);

        if (Config.dbName != null)
            Config.logMessage("Database                                  : "+Config.dbName,Config.LOG_LEVEL_SUMMARY);

        if (Config.outputDir != null)
            Config.logMessage("Output directory                          : "+Config.outputDir, Config.LOG_LEVEL_SUMMARY);
        else
            Config.logMessage("Output set to StdOut.", Config.LOG_LEVEL_SUMMARY);
        Config.logMessage("Commands logging enabled                  : "+Config.commandsLogging, Config.LOG_LEVEL_SUMMARY);
        if (Config.traceAllDbs())
            Config.logMessage("All databases are traced.", Config.LOG_LEVEL_SUMMARY);
        else if (Config.traceInclDbs())
            Config.logMessage("List of traced databases                  : "+Config.includeDbs, Config.LOG_LEVEL_SUMMARY);
        else if (Config.traceExclDbs())
            Config.logMessage("List of databases, which are not traced   : "+Config.excludeDbs, Config.LOG_LEVEL_SUMMARY);
        if (Config.traceAllCmds())
            Config.logMessage("All commands are traced.", Config.LOG_LEVEL_SUMMARY);
        else if (Config.traceInclCmds())
            Config.logMessage("List of traced commands                   : "+Config.includeCmds, Config.LOG_LEVEL_SUMMARY);
        else if (Config.traceExclCmds())
            Config.logMessage("List of commands, which are not traced    : "+Config.excludeCmds, Config.LOG_LEVEL_SUMMARY);
        switch (Config.executionTracing) {
            case 0: Config.logMessage("Execution plan tracing disabled.", Config.LOG_LEVEL_SUMMARY);
                    break;
            case 1: Config.logMessage("Execution plan tracing level              : QueryPlanner", Config.LOG_LEVEL_SUMMARY);
                    break;
            case 2: Config.logMessage("Execution plan tracing level              : ExecutionStats", Config.LOG_LEVEL_SUMMARY);
                    break;
            case 3: Config.logMessage("Execution plan tracing level              : AllPlansExecution", Config.LOG_LEVEL_SUMMARY);
                    break;
        }
        if (footer) {
            Config.logMessage("Number of entries interpreted as traced commands : "+numOfCommands, Config.LOG_LEVEL_SUMMARY);
            Config.logMessage("Number of all entries                            : "+numOfAllEntries, Config.LOG_LEVEL_SUMMARY);
        }
    }

    public synchronized static void shutdown() {
        try {
            while(sem==1);
            setSem(1);
            inputFile.close();
            for (Map.Entry<String, PrintStream> e : outputFiles.entrySet())
                e.getValue().close();
            printSettings(true);
            Config.logFile.close();
            System.exit(0);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(0);
        }
    }

    public static void generateCommand(String dbName, JsonObject commandObject) throws Exception {
        PrintStream ps;

        commandObject.remove("lsid");
        numOfCommands++;
        Config.logMessage("Command #"+numOfCommands+" : "+commandObject, Config.LOG_LEVEL_ALL);

        if (Config.outputDir != null && !outputFiles.containsKey(dbName) ) {
            if (Config.outputMode == 0) {
                ps = new PrintStream(new FileOutputStream(Config.outputDir + File.separator + dbName + ".js"), true);
                ps.println("use " + dbName);
            } else
                ps = new PrintStream(new FileOutputStream(Config.outputDir + File.separator + dbName + ".json"), true);
            outputFiles.put(dbName,ps);
        } else if (Config.outputDir != null )
            ps = outputFiles.get(dbName);
        else {
            ps = System.out;
            if (!oldDbName.equals(dbName)) {
                ps.println("use " + dbName);
                oldDbName = dbName;
            }
        }

        if (Config.outputMode == 0) {
            if (Config.commandsLogging && Config.executionTracing == 0)
                ps.println("console.log('Executing command : " + commandObject + "')");
            else if (Config.commandsLogging && Config.executionTracing != 0)
                ps.println("console.log('Generating execution plan for : " + commandObject + "')");

            switch (Config.executionTracing) {
                case 0:
                    ps.println("db.runCommand(" + commandObject + ")");
                    break;
                case 1:
                    ps.println("try { db.runCommand({explain : " + commandObject + ", verbosity : 'queryPlanner'}); } catch (e) {console.error(\"Execution plan generation does not support this statement. Details: https://www.mongodb.com/docs/manual/reference/command/explain/\")}");
                    break;
                case 2:
                    ps.println("try { db.runCommand({explain : " + commandObject + ", verbosity : 'executionStats'}); } catch (e) {console.error(\"Execution plan generation does not support this statement. Details: https://www.mongodb.com/docs/manual/reference/command/explain/\")}");
                    break;
                case 3:
                    ps.println("try { db.runCommand({explain : " + commandObject + ", verbosity : 'allPlansExecution'}); } catch (e) {console.error(\"Execution plan generation does not support this statement. Details: https://www.mongodb.com/docs/manual/reference/command/explain/\")}");
            }

            if (Config.outputDir != null)
                ps.println("console.log('\\n\\n\\n')");
        }
        else {
            switch (Config.executionTracing) {
                case 0:
                    ps.println(commandObject);
                    break;
                case 1:
                    ps.println("{explain : " + commandObject + ", verbosity : 'queryPlanner'}");
                    break;
                case 2:
                    ps.println("{explain : " + commandObject + ", verbosity : 'executionStats'}");
                    break;
                case 3:
                    ps.println("db.runCommand({explain : " + commandObject + ", verbosity : 'allPlansExecution'}");
            }
        }
    }

    public static void initialize() throws Exception {
        Config.readConfiguration(Config.EXTRACT);
        if (Config.inputFileName != null)
            inputFile = new BufferedReader((new FileReader(Config.inputFileName)));
        else
            inputFile = new BufferedReader(new InputStreamReader(System.in));
        printSettings(false);
    }

    public static void extractLog() throws Exception {
        String line;
        while ((line = inputFile.readLine()) != null) {
            while(sem==1);
            setSem(1);
            numOfAllEntries++;
            JsonObject logEntry;
            Gson gson = new Gson();
            logEntry = gson.fromJson(line, JsonObject.class);
            if (logEntry != null &&
                    logEntry.getAsJsonPrimitive("c").getAsString().equals("COMMAND") &&
                    logEntry.has("attr")) {
                JsonObject entryAttr = logEntry.getAsJsonObject("attr");
                if (entryAttr.has("command") && entryAttr.get("command").isJsonObject()) {
                    JsonObject commandObject = entryAttr.getAsJsonObject("command");
                    dbName = commandObject.getAsJsonPrimitive("$db").getAsString();
                    if ((Config.traceDatabase(dbName) &&
                            Config.traceCommand(commandObject)) &&
                            ((commandObject.has("documents") &&
                                    commandObject.get("documents").isJsonArray())||
                                    (!commandObject.has("documents"))))
                        generateCommand(dbName,commandObject);
                }
            }
            setSem(0);
        }
    }

    public static void extractProfileDump() throws Exception {
        JsonObject  command;
        String dbName = "";

        JsonParser parser = new JsonParser();
        JsonElement el    = parser.parse(inputFile);
        JsonArray   ar    = el.getAsJsonArray();


        for (int i=0; i<ar.size(); i++) {
            numOfAllEntries++;
            command = ar.get(i).getAsJsonObject().get("command").getAsJsonObject();
            command.remove("$clusterTime");
            command.remove("lsid");
            dbName = command.get("$db").getAsString();
            generateCommand(dbName,command);
        }
    }

    public static void extractProfileDirectly() throws Exception {
        MongoClient client;
        MongoDatabase db;
        String commandStr, dbName;
        JsonObject command;

        Config.logMessage("Connecting to the database",Config.LOG_LEVEL_SUMMARY);
        MongoCollection<Document> profileCollection;


        client = MongoClients.create(Config.connectString);
        db     = client.getDatabase(Config.dbName);
        Config.logMessage("Connected to the database",Config.LOG_LEVEL_SUMMARY);

        profileCollection = db.getCollection("system.profile");
        MongoCursor<Document> collectionCursor = profileCollection.
                                                    find().
                                                    iterator();

        while (collectionCursor.hasNext()) {
            numOfAllEntries++;
            commandStr = collectionCursor.next().toJson();
            command = JsonParser.parseString(commandStr).
                    getAsJsonObject().
                    get("command").
                    getAsJsonObject();
            command.remove("$clusterTime");
            command.remove("lsid");
            dbName = command.get("$db").getAsString();
            generateCommand(Config.dbName,command);
        }
        client.close();
    }

    public static void main(String[] args) {
        String line;

        try {
            initialize();
            if (Config.inputFileName != null)
                inputFile = new BufferedReader((new FileReader(Config.inputFileName)));
            else
                inputFile = new BufferedReader(new InputStreamReader(System.in));
            switch (Config.inputFileFormat) {
                case 0: extractLog();
                        break;
                case 1: extractProfileDump();
                        break;
                case 2: extractProfileDirectly();
            }
            shutdown();
        } catch (Exception e)
        {e.printStackTrace();}
    }
}