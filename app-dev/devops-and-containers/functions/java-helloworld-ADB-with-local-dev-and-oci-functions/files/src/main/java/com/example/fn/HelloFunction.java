/*
Copyright (c) 2025 Oracle and/or its affiliates.

The Universal Permissive License (UPL), Version 1.0

Subject to the condition set forth below, permission is hereby granted to any
person obtaining a copy of this software, associated documentation and/or data
(collectively the "Software"), free of charge and under any and all copyright
rights in the Software, and any and all patent rights owned or freely
licensable by each licensor hereunder covering either (i) the unmodified
Software as contributed to or provided by such licensor, or (ii) the Larger
Works (as defined below), to deal in both

(a) the Software, and
(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
one is included with the Software (each a "Larger Work" to which the Software
is contributed by such licensors),

without restriction, including without limitation the rights to copy, create
derivative works of, display, perform, and distribute the Software and make,
use, sell, offer for sale, import, export, have made, and have sold the
Software and the Larger Work(s), and to sublicense the foregoing rights on
either these or other terms.

This license is subject to the following condition:
The above copyright notice and either this complete permission notice or at
a minimum a reference to the UPL must be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

package com.example.fn;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Properties;
import oracle.jdbc.OracleConnection;
import oracle.ucp.jdbc.PoolDataSource;
import oracle.ucp.jdbc.PoolDataSourceFactory;

public class HelloFunction {

    private PoolDataSource pds;
    // JDBC CONNECTION DETAILS
    private String DB_USER;
    private String DB_PASSWORD;
    private String DB_URL;
    
    @FnConfiguration
    public void setUp(RuntimeContext ctx) throws Exception {

        // JDBC CONNECTION DETAILS - try reading from Application and Function level config
        DB_USER = ctx.getConfigurationByKey("DB_USER").orElse(System.getenv().getOrDefault("DB_USER", ""));
        DB_PASSWORD = ctx.getConfigurationByKey("DB_PASSWORD").orElse(System.getenv().getOrDefault("DB_PASSWORD", ""));
        DB_URL = "jdbc:oracle:thin:@" + ctx.getConfigurationByKey("DB_URL").orElse(System.getenv().getOrDefault("DB_URL", ""));

        try {
            Properties props = new Properties();
            props.put(OracleConnection.CONNECTION_PROPERTY_FAN_ENABLED, "false");
            pds = PoolDataSourceFactory.getPoolDataSource();
            pds.setConnectionFactoryClassName("oracle.jdbc.pool.OracleDataSource");
            pds.setURL(DB_URL);
            pds.setUser(DB_USER);
            pds.setPassword(DB_PASSWORD);
            pds.setConnectionPoolName("JDBC_UCP_POOL");
            pds.setConnectionProperties(props);
        } catch (Exception e)
        {
            System.out.println(e.getMessage());
        }
    }

    public String handleRequest() {
        String retval = "";
        try {
            OracleConnection connection = (OracleConnection) pds.getConnection();
            PreparedStatement userQuery = connection.prepareStatement("SELECT SYSDATE");
            ResultSet rs = userQuery.executeQuery();
            if(rs.next()) {
                retval = rs.getString("SYSDATE");
            }
            connection.close();
        } catch (Exception e)
        {
            e.printStackTrace();
            retval = e.getMessage();
        }
        return retval;
    }

}