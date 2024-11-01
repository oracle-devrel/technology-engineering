package pg.oracle;

/* property graph demo
   this code demonstrates:
   1. integration of Property Graph with SQL in Oracle Database 23c
   2. Java API for Property Graph Server
   It uses demonstration tables described in the following LiveLabs Workshop:
   "Analyze, Query, and Visualize Property Graphs with Oracle Database"
   https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=686&p210_wec=&session=108772142407826
   Requirements:
   1. Oracle Database 23c
   2. Database user account ( <username> ) with the privileges described in the mentioned LiveLabs Workshop
   3. Tables used in this workshop created in the mentioned schema
   4. Oracle Property Graph Server installation using user account
 */


import java.sql.*;
import oracle.jdbc.pool.OracleDataSource;
import oracle.pg.rdbms.GraphServer;
import oracle.pgx.api.*;

public class Main {
    private static String dbHost    = "<database_hostname_or_op>";
    private static String pgxHost   = "<graph_server_hostname_or_ip>";
    private static int dbPort       = <listener_port_number_ususally_1521>;
    private static int pgxPort      = <graph_server_port_number_usually_7007>;
    private static String dbService = "<database_service_name>";
    private static String username  = "<username>";
    private static String password  = "<password>";
    private static String pgName = "CUSTOMER_GRAPH";
    public static void SQLPGDemo() {
        try {
            OracleDataSource ds = new OracleDataSource();
            ds.setDriverType("thin");
            ds.setServerName(dbHost);
            ds.setServiceName(dbService);
            ds.setPortNumber(dbPort);
            ds.setUser(username);
            ds.setPassword(password);
            Connection con = ds.getConnection();
            System.out.println("Connected to the database");
            System.out.println("(Re)creating property graph "+pgName);
            Statement stmt = con.createStatement();
            stmt.execute("CREATE OR REPLACE PROPERTY GRAPH "+pgName+" VERTEX TABLES (\n" +
                    "    customer\n" +
                    "  , account\n" +
                    "  , merchant\n" +
                    "  )\n" +
                    "  EDGE TABLES (\n" +
                    "    account as account_edge\n" +
                    "      SOURCE KEY(id) REFERENCES account (id)\n" +
                    "      DESTINATION KEY(customer_id) REFERENCES customer (id)\n" +
                    "      LABEL owned_by PROPERTIES (id)\n" +
                    "  , parent_of as parent_of_edge \n" +
                    "      SOURCE KEY(customer_id_parent) REFERENCES customer (id)\n" +
                    "      DESTINATION KEY(customer_id_child) REFERENCES customer (id)\n" +
                    "  , purchased as puchased_edge \n" +
                    "      SOURCE KEY(account_id) REFERENCES account (id)\n" +
                    "      DESTINATION KEY(merchant_id) REFERENCES merchant (id)\n" +
                    "  , transfer as transfer_edge \n" +
                    "      SOURCE KEY(account_id_from) REFERENCES account (id)\n" +
                    "      DESTINATION KEY(account_id_to) REFERENCES account (id)\n" +
                    "  ) ");
            System.out.println("Graph (re)created succesfully.");
            ResultSet rset = stmt.executeQuery("SELECT account_no\n" +
                    "FROM GRAPH_TABLE ( CUSTOMER_GRAPH MATCH (v1)-[transfer_edge]->{1,2}(v1)\n" +
                    "columns (v1.account_no as account_no))");
            while (rset.next()) {
                System.out.println(rset.getString(1));
            }
            con.close();
        }
        catch (Exception e) {e.printStackTrace();}
    }

    public static void PGXDemo() {
        try {
            ServerInstance si = GraphServer.getInstance("https://"+pgxHost+":"+pgxPort,username,password.toCharArray());
            PgxSession ses = si.createSession("my-session");
            System.out.println("Connected to graph server");
            PgxGraph graph = ses.readGraphByName(username.toUpperCase(), pgName, GraphSource.PG_SQL);
            System.out.println("Graph loaded into Property Graph Server");
            PgqlResultSet rset = graph.queryPgql("SELECT a1.account_no    AS a1_account\n" +
                                "    , t1.transfer_date AS t1_date\n" +
                                "     , t1.amount        AS t1_amount\n" +
                                "     , a2.account_no    AS a2_account\n" +
                                "     , t2.transfer_date AS t2_date\n" +
                                "     , t2.amount        AS t2_amount\n" +
                                "FROM MATCH (a1)-[t1:transfer_edge]->(a2)-[t2:transfer_edge]->(a1)\n" +
                                "WHERE t1.transfer_date < t2.transfer_date");
            while (rset.next()) {
                System.out.println(rset.getString(1));
            }
        }
        catch (Exception e) {e.printStackTrace();}
    }
    public static void main(String[] args) {
        SQLPGDemo();
        PGXDemo();
    }
}
