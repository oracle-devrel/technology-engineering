package utils.dbutils;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;

public class ManagingThread extends Thread {
    public void run() {
        PrintStream ps1;
        try {
            while (true) {
                Thread.sleep(1000);
                if (Files.exists(Paths.get(Config.shutdownFileName))) {
                    Files.delete(Paths.get(Config.shutdownFileName));
                    if (Config.runningMode == Config.EXTRACT)
                        Extractor.shutdown();
                    else
                        Applier.shutdown();
                }
            }
        }
        catch (Exception e) {}
    }
}
