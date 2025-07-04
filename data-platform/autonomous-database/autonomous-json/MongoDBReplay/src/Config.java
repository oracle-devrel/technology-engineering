package utils.dbutils;

import com.google.gson.*;

import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Config {
    public static final int EXTRACT=1;
    public static final int APPLY=2;

    public static final int LOG_LEVEL_SUMMARY = 0;
    public static final int LOG_LEVEL_ERRORS  = 1;
    public static final int LOG_LEVEL_ALL     = 2;

    public static int runningMode;
    public static String configDir;
    public static String inputFileName;
    public static String configFileName;
    public static PrintStream logFile;
    public static String logFileName;
    public static int logLevel = 0;
    public static String shutdownFileName;
    public static String outputDir;
    public static JsonArray includeDbs;
    public static JsonArray excludeDbs;
    public static JsonArray includeCmds;
    public static JsonArray excludeCmds;
    public static boolean commandsLogging;
    public static String connectString;
    public static String dbName;
    public static int outputMode = 0; // 0 - mongosh script, default
                                      // 1 - json
    public static int inputFileFormat = 0; // 0 - Momngod log
                                           // 1 - db.system.profile collection dump
                                           // 2 - db.system.profile direct reads

    public static int executionTracing = 0; // 0 - not tracing
                                            // 1 - query planner
                                            // 2 - execution stats
                                            // 3 - allPlansExecution
    public static ManagingThread t = new ManagingThread();
    private static Reader reader;
    private static JsonObject configObject;

    public static boolean traceAllDbs() {
        return (includeDbs == null && excludeDbs == null);
    }

    public static boolean traceInclDbs() {
        return (includeDbs != null);
    }

    public static boolean traceExclDbs() {
        return (excludeDbs != null);
    }

    public static boolean traceInclCmds() {
        return (includeCmds != null);
    }

    public static boolean traceExclCmds() {
        return (excludeCmds != null);
    }

    public static boolean traceAllCmds() {
        return (includeCmds == null && excludeCmds == null);
    }

    public static boolean traceDatabase(String dbName) {
        boolean contains = false;
        if ( includeDbs == null && excludeDbs == null )
            contains = true;
        else if ( excludeDbs == null )
            contains = includeDbs.contains(new JsonParser().parse(dbName));
        else contains = !excludeDbs.contains(new JsonParser().parse(dbName));
        return contains;
    }

    public static boolean traceCommand(JsonObject command) {
        boolean contains = false;
        int i = 0;
        if (includeCmds == null && excludeCmds == null)
            contains = true;
        else if (excludeCmds == null)
                while (!contains && i < includeCmds.asList().toArray().length) {
                    if (command.has(includeCmds.asList().get(i).getAsString()))
                        contains = true;
                    i++;
                }
        else if (includeCmds == null) {
            contains = true;
            while (contains && i < excludeCmds.asList().toArray().length) {
                if (command.has(excludeCmds.asList().get(i).getAsString()))
                    contains = false;
                i++;
            }
        }
        return contains;
    }

    public static void readExtractConfiguration() {
        try {

            if (configObject.has("INPUT_FILE"))
                inputFileName = configObject.getAsJsonPrimitive("INPUT_FILE").getAsString();
            else
                t.start();

            if (configObject.has("OUTPUT_DIR"))
                outputDir = configObject.getAsJsonPrimitive("OUTPUT_DIR").getAsString();

            if (configObject.has("INCLUDE_COMMANDS") &&
                    configObject.has("EXCLUDE_COMMANDS"))
                throw new Exception("You cannot set INCLUDE_COMMANDS and EXCLUDE_COMMANDS at the same time. Please, review the available documentation.");

            if (configObject.has("INCLUDE_DATABASES"))
                includeDbs = configObject.getAsJsonArray("INCLUDE_DATABASES");

            if (configObject.has("EXCLUDE_DATABASES"))
                excludeDbs = configObject.getAsJsonArray("EXCLUDE_DATABASES");

            if (configObject.has("INCLUDE_COMMANDS"))
                includeCmds = configObject.getAsJsonArray("INCLUDE_COMMANDS");

            if (configObject.has("EXCLUDE_COMMANDS"))
                excludeCmds = configObject.getAsJsonArray("EXCLUDE_COMMANDS");

            if (configObject.has("COMMANDS_LOGGING"))
                commandsLogging = configObject.getAsJsonPrimitive("COMMANDS_LOGGING").getAsBoolean();
            else
                commandsLogging = true;

            if (configObject.has("EXECUTION_PLAN_TRACING"))
                executionTracing = configObject.getAsJsonPrimitive("EXECUTION_PLAN_TRACING").getAsInt();

            if (configObject.has("INPUT_FILE_FORMAT")) {
                if ( configObject.getAsJsonPrimitive("INPUT_FILE_FORMAT").getAsString().equals("MONGO_LOG"))
                        inputFileFormat = 0;
                else if ( configObject.getAsJsonPrimitive("INPUT_FILE_FORMAT").getAsString().equals("MONGO_PROFILE"))
                        inputFileFormat = 1;
                else throw new Exception("INPUT_FILE_FORMAT can be set to MONGO_LOG or MONGO_PROFILE");
            }
            else inputFileFormat = 0;

            if (configObject.has("INPUT_CONNECT_STRING")) {
                if (configObject.has("INPUT_FILE_FORMAT") || configObject.has("INPUT_FILE"))
                    throw new Exception("If INPUT_CONNECT_STRING is set then INPUT_FILE and INPUT_FILE_FORMAT cannot be set");

                if (configObject.has("DB_NAME"))
                    dbName = configObject.getAsJsonPrimitive("DB_NAME").getAsString();
                else throw new Exception("DB_NAME parameter is mandatory when INPUT_CONNECT_STRING is set.");

                connectString = configObject.get("INPUT_CONNECT_STRING").getAsString();
                inputFileFormat = 2;
            }

            if (configObject.has("OUTPUT_MODE")) {
                if ( configObject.getAsJsonPrimitive("OUTPUT_MODE").getAsString().equals("SCRIPT"))
                    outputMode = 0;
                else if (configObject.getAsJsonPrimitive("OUTPUT_MODE").getAsString().equals("JSON"))
                    outputMode = 1;
                else throw new Exception("OUTPUT_MODE can be set to SCRIPT or JSON values only");
            }
            else
                outputMode = 0;



        } catch (Exception e) {
            e.printStackTrace();
            System.exit(0);
        }
    }

    public static void readApplyConfiguration() {
        try {
            if (configObject.has("CONNECT_STRING"))
                connectString = configObject.getAsJsonPrimitive("CONNECT_STRING").getAsString();
            else throw new Exception("CONNECT_STRING parameter is mandatory.");


            if (configObject.has("DB_NAME"))
                dbName = configObject.getAsJsonPrimitive("DB_NAME").getAsString();
            else throw new Exception("DB_NAME parameter is mandatory.");

            if (configObject.has("INPUT_FILE"))
                inputFileName = configObject.getAsJsonPrimitive("INPUT_FILE").getAsString();
            else
                t.start();
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(0);
        }
    }

    public static void readConfiguration(int mode) {
        try {
            runningMode = mode;
            configDir = System.getenv("MR_CONFIG_DIR");
            if (configDir == null || configDir.length() == 0)
                throw new Exception("MR_CONFIG_DIR environment variable is mandatory. Please review the available documentation.");

            if (mode == EXTRACT) {
                configFileName = configDir + File.separator + "mdbecfg.json";
                shutdownFileName = configDir + File.separator + "mdbes.label";
            }
            else {
                configFileName = configDir + File.separator + "mdbacfg.json";
                shutdownFileName = configDir + File.separator + "mdbas.label";
            }

            reader = Files.newBufferedReader(Paths.get(configFileName));
            configObject = (new Gson()).fromJson(reader, JsonObject.class);

            if (configObject.has("LOG_FILE")) {
                logFileName = configObject.getAsJsonPrimitive("LOG_FILE").getAsString();
                logFile = new PrintStream(new FileOutputStream(Config.logFileName), true);
            }
            else
                logFile = System.err;

            if (configObject.has("LOG_LEVEL"))
                logLevel = configObject.getAsJsonPrimitive("LOG_LEVEL").getAsInt();

            if (mode == EXTRACT)
                readExtractConfiguration();
            else
                readApplyConfiguration();

            reader.close();
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(0);
        }
    }

    public static void logMessage(String message, int level) {
        if (level <= logLevel)
            logFile.println(message);
    }
}
