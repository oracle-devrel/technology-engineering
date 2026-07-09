package com.oracle;

import com.google.gson.Gson;
import jakarta.json.JsonObject;

import java.io.FileOutputStream;
import java.io.PrintStream;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Config {
    public static final int MODE_IMPORT = 1;
    public static final int MODE_EXPORT = 2;
    public static final int IMPORT_MODE_APPEND   = 1;
    public static final int IMPORT_MODE_REPLACE  = 2;
    public static final int IMPORT_MODE_CREATE   = 3;
    public static final int IMPORT_MODE_RECREATE = 4;

    public static String Url;
    public static String Username;
    public static String Password;
    public static String inputFileName;
    public static String collectionName;
    public static int    importMode;
    public static String keyField = "";

    public static void readImportConfiguration(com.google.gson.JsonObject configObject) throws Exception {


        if (configObject.has("DB_URL"))
            Url = configObject.getAsJsonPrimitive("DB_URL").getAsString();
        else
            throw new Exception ("DB_URL parameter is not set.");

        if (configObject.has("DB_USERNAME"))
            Username = configObject.getAsJsonPrimitive("DB_USERNAME").getAsString();
        else
            throw new Exception ("DB_USERNAME parameter is not set.");

        if (configObject.has("DB_PASSWORD"))
            Password = configObject.getAsJsonPrimitive("DB_PASSWORD").getAsString();
        else
            throw new Exception ("DB_PASSWORD parameter is not set.");

        if (configObject.has("DB_COLLECTION"))
            collectionName = configObject.getAsJsonPrimitive("DB_COLLECTION").getAsString();
        else
            throw new Exception ("DB_COLLECTION parameter is not set.");

        if (configObject.has("INPUT_FILE"))
            inputFileName = configObject.getAsJsonPrimitive("INPUT_FILE").getAsString();
        else
            throw new Exception ("INPUT_FILE parameter is not set.");

        if (configObject.has("IMPORT_MODE")) {
            if (configObject.getAsJsonPrimitive("IMPORT_MODE").getAsString().equals("APPEND"))
               importMode = IMPORT_MODE_APPEND;
            else if (configObject.getAsJsonPrimitive("IMPORT_MODE").getAsString().equals("REPLACE"))
                importMode = IMPORT_MODE_REPLACE;
            else if (configObject.getAsJsonPrimitive("IMPORT_MODE").getAsString().equals("CREATE"))
                importMode = IMPORT_MODE_CREATE;
            else
                throw new Exception("Invalid value of IMPORT_MODE parameter");
        }
        else
            throw new Exception ("IMPORT_MODE parameter is not set.");
        if (configObject.has("KEY_FIELD"))
            keyField = configObject.getAsJsonPrimitive("KEY_FIELD").getAsString();

        System.out.println("Configuration read.");
        System.out.println("DB_URL        : " + Url);
        System.out.println("DB_USERNAME   : " + Username);
        System.out.println("IMPORT_MODE   : " + configObject.getAsJsonPrimitive("IMPORT_MODE").getAsString() );
        System.out.println("DB_COLLECTION : " + collectionName);
        System.out.println("INPUT_FILE    : " + inputFileName);
        if (!keyField.equals(""))
            System.out.println("KEY_FIELD     : " + keyField);
        else
            System.out.println("KEY_FIELD     : not set, _id will be generated automaticaly" );
    }

    public static void readExportConfiguration(com.google.gson.JsonObject configObject) throws Exception {

    }

    public static void readConfiguration(int mode) throws Exception {
        String cfgFileName;
        Reader reader;
        com.google.gson.JsonObject configObject;

        if (mode == MODE_IMPORT)
            cfgFileName = System.getenv("SODA_IMP_CFG_FILE");
        else if (mode == MODE_EXPORT)
            cfgFileName = System.getenv("SODA_EXP_CFG_MDOE");
        else
            throw new Exception ("Invalid mode.");

        if (cfgFileName == null || cfgFileName.equals("") )
            throw new Exception("Config file name not provided. Please set appropriate environment variable.");

        reader = Files.newBufferedReader(Paths.get(cfgFileName));
        configObject = (new Gson()).fromJson(reader, com.google.gson.JsonObject.class);

        if (mode == MODE_IMPORT)
            readImportConfiguration(configObject);
        else
            readExportConfiguration(configObject);
    }
}
