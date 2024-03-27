// See https://aka.ms/new-console-template for more information
﻿using System.Text;
using Oracle.ManagedDataAccess.Client;

internal class Program
{

    public static OracleConnection createDBConnection(string dbUsername,
                                                      string dbPassword,
                                                      string dbURL)
    {
        Console.WriteLine("\nConnecting to the database:");
        Console.WriteLine("Database URL : "+dbURL);
        Console.WriteLine("Database Username : "+dbUsername);
        OracleConnection dbConnection = new OracleConnection("User Id="+dbUsername+";" +
                                            "Password="+dbPassword+";" +
                                            "Data Source="+dbURL);
        dbConnection.Open();
        Console.WriteLine("\nConnected");       
        Console.WriteLine("---------------");
        return dbConnection;
    }

    public static void basicJDBCTest(OracleConnection dbConnection)
    {
        Console.WriteLine("\nExecuting a SELECT statement");
        OracleCommand sqlCmd = dbConnection.CreateCommand();
        sqlCmd.CommandText = "SELECT LAST_NAME, FIRST_NAME "
                           + "FROM EMPLOYEES "
                           + "ORDER BY LAST_NAME";
        OracleDataReader sqlReader = sqlCmd.ExecuteReader();
        Console.WriteLine("\nQuery executed. Printing out results");
        while (sqlReader.Read()) 
        {
	        // result set processing, example
            Console.WriteLine(sqlReader.GetString(0)+" "+sqlReader.GetString(1));
        }
        Console.WriteLine("\nResults printed out. Executing INSERT statements in a tranaction context");
        OracleTransaction sqlTxn = dbConnection.BeginTransaction();
        sqlCmd.CommandText = "INSERT INTO EMPLOYEES_COPY "
                           + "SELECT * FROM EMPLOYEES "
                           + "WHERE DEPARTMENT_ID = 20";
        sqlCmd.ExecuteNonQuery();
        sqlCmd.CommandText = "INSERT INTO DEPARTMENTS_COPY "
                           + "SELECT * FROM DEPARTMENTS "
                           + "WHERE DEPARTMENT_ID = 20";
        sqlCmd.ExecuteNonQuery();
        
        Console.WriteLine("\nDML statement executed. Commiting transaction");
        sqlTxn.Commit();
        Console.WriteLine("\nTransaction commited.");
        Console.WriteLine("----------------------------");
    }
    
    public static void basicAQTest(OracleConnection dbConnection,
                                    string Message)
    {
        Console.WriteLine("\nStarting to demonstrate AQ/TEQ feature of Oracle Database");
        OracleTransaction sqlTxn = dbConnection.BeginTransaction();
        OracleCommand enqueueSampleMessage = dbConnection.CreateCommand();
        enqueueSampleMessage.CommandText = "sample_enqueue";
        enqueueSampleMessage.CommandType = System.Data.CommandType.StoredProcedure;

        OracleCommand dequeueSampleMessage = dbConnection.CreateCommand();
        dequeueSampleMessage.CommandText = "sample_dequeue";
        dequeueSampleMessage.CommandType = System.Data.CommandType.StoredProcedure;
  
        OracleParameter inputMessage = new OracleParameter("p_message", OracleDbType.Varchar2, 2000);
        inputMessage.Direction = System.Data.ParameterDirection.Input;
        inputMessage.Value = Message;
        
        OracleParameter outputMessage = new OracleParameter("p_message", OracleDbType.Varchar2, 2000);
        outputMessage.Direction = System.Data.ParameterDirection.Output;


        enqueueSampleMessage.Parameters.Add(inputMessage);

        dequeueSampleMessage.Parameters.Add(outputMessage);

        enqueueSampleMessage.ExecuteNonQuery();
        dequeueSampleMessage.ExecuteNonQuery();

        Console.WriteLine(outputMessage.Value);

        sqlTxn.Commit();

        Console.WriteLine("Enqueueing/Dequeueing sample message completed succesfully.");
    }

    public static void closeDBConnection (OracleConnection dbConnection) 
    {
        Console.WriteLine("\nClosing DB connection.");
        dbConnection.Close();
        Console.WriteLine("Connection closed.");
        Console.WriteLine("----------------------------");
    }

    private static void nativeAQTest(OracleConnection dbConnection)
    {
        OracleTransaction txn = dbConnection.BeginTransaction();
        OracleAQQueue sample_message_queue = new OracleAQQueue("sample_message_queue",dbConnection);
        sample_message_queue.MessageType = OracleAQMessageType.Raw;
        OracleAQMessage msgIn = new OracleAQMessage();
        msgIn.Payload = Encoding.UTF8.GetBytes("Another test payload");
        sample_message_queue.Enqueue(msgIn);
        Console.WriteLine("A message has been put into the test queue");
        txn.Commit();

        txn = dbConnection.BeginTransaction();
        OracleAQMessage msgOut = sample_message_queue.Dequeue();
        txn.Commit();
        Console.WriteLine(Encoding.UTF8.GetString(msgOut.Payload as byte[]));
    }
    private static void Main(string[] args)
    {
        try
        {
            string dbUrl, dbUsername, dbPassword;

            Console.Write("Please, provide database connection string : ");
            dbUrl = Console.ReadLine();

            Console.Write("Username : ");
            dbUsername = Console.ReadLine();

            Console.Write("Password : ");
            dbPassword = Console.ReadLine();


            OracleConnection dbConnection = createDBConnection(dbUsername,
                                                               dbPassword,
                                                               dbUrl); 
            
            basicJDBCTest(dbConnection);

            basicAQTest(dbConnection,"Test Message 01");

            nativeAQTest(dbConnection);
            
            closeDBConnection(dbConnection);
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
        }
    }
}