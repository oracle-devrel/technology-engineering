package com.oracle;

import com.google.gson.JsonParser;
import oracle.jdbc.datasource.impl.OracleDataSource;
import oracle.soda.OracleCollection;
import oracle.soda.OracleDatabase;
import oracle.soda.OracleDatabaseAdmin;
import oracle.soda.OracleDocument;
import oracle.soda.rdbms.OracleRDBMSClient;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.io.filefilter.WildcardFileFilter;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileFilter;
import java.io.FileReader;
import java.math.BigDecimal;
import java.util.List;

public class SODAImport {

    private static BufferedReader      inputFile;
    private static OracleDatabase      sodaDb;
    private static OracleDatabaseAdmin sodaDbAdmin;
    private static OracleCollection    sodaCollection;

    private static int numOfDocuments = 0;

    public static File[] getFiles(String path) {
        String fname = FilenameUtils.getBaseName(path);
        String fext  = FilenameUtils.getExtension(path);
        String fdir  = FilenameUtils.getFullPathNoEndSeparator(path);
        fname = fname + "." + fext;
        FileFilter filter = new WildcardFileFilter(fname);
        File[] files = (new File(fdir)).listFiles(filter);
        return files;
    }

    public static void initializeImport() throws Exception {
        boolean collectionExists = false;

        inputFile  = new BufferedReader((new FileReader(Config.inputFileName)));
        OracleDataSource ods = new OracleDataSource();
        ods.setURL(Config.Url);
        ods.setUser(Config.Username);
        ods.setPassword(Config.Password);
        OracleRDBMSClient client = new OracleRDBMSClient();
        sodaDb = client.getDatabase(ods.getConnection());
        sodaDbAdmin = sodaDb.admin();
        List<String> collections = sodaDbAdmin.getCollectionNames();
        for (String name: collections)
            if (name.equals(Config.collectionName))
                collectionExists = true;
        if (collectionExists) {
            sodaCollection = sodaDb.openCollection(Config.collectionName);
            if (Config.importMode == Config.IMPORT_MODE_REPLACE)
                sodaCollection.find().remove();
            else if (Config.importMode == Config.IMPORT_MODE_RECREATE) {
                sodaCollection.admin().drop();
                sodaCollection = sodaDbAdmin.createCollection(Config.collectionName);
            }
        }
        else if (Config.importMode == Config.IMPORT_MODE_CREATE ||
                 Config.importMode == Config.IMPORT_MODE_RECREATE )
            sodaCollection = sodaDbAdmin.createCollection(Config.collectionName);
        else
            throw new Exception("Collection "+Config.collectionName+" does not exists. To create it automatically set IMPORT_MODE parameter to CREATE.");
        System.out.println("Import initialized successfully.");
    }

    public static void importData() throws Exception {
        String line;
        String keyValue;
        com.google.gson.JsonObject gdoc;
        OracleDocument odoc;
        System.out.println("Starting importing json data.");
        while ((line = inputFile.readLine()) != null) {
            numOfDocuments++;
            gdoc = JsonParser.parseString(line).getAsJsonObject();
            if (!Config.keyField.isEmpty() && gdoc.has(Config.keyField)) {
                try {
                    int ikeyValue = gdoc.get(Config.keyField).getAsInt();
                    keyValue = Integer.toString(ikeyValue);
                }
                catch (Exception e) {
                    keyValue = gdoc.get(Config.keyField).getAsString();
                }
                gdoc.addProperty("_id", keyValue);
            }
            odoc = sodaDb.createDocumentFromString(gdoc.toString());
            sodaCollection.insert(odoc);
            System.out.print("#");
        }
        System.out.println("");
        System.out.println("Import process completed.");
        System.out.println("Number of documents imported : "+numOfDocuments);
    }

    public static void finalizeImport() throws Exception {
        inputFile.close();
        sodaDbAdmin.getConnection().close();
        System.out.println("Import process stopped succesfully.");
    }
    public static void main(String[] args) {
        try {
            Config.readConfiguration(Config.MODE_IMPORT);
            initializeImport();
            importData();
            finalizeImport();
        }
        catch (Exception e) {e.printStackTrace();}
    }
}
