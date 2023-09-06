/*******************************************************************************
 * Copyright (c) 2023 Oracle and/or its affiliates. All rights reserved. DO NOT
 * ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
 *
 * The Universal Permissive License (UPL), Version 1.0
 *
 * Subject to the condition set forth below, permission is hereby granted to any
 * person obtaining a copy of this software, associated documentation and/or
 * data (collectively the "Software"), free of charge and under any and all
 * copyright rights in the Software, and any and all patent rights owned or
 * freely licensable by each licensor hereunder covering either (i) the
 * unmodified Software as contributed to or provided by such licensor, or (ii)
 * the Larger Works (as defined below), to deal in both
 *
 * (a) the Software, and
 *
 * (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
 * one is included with the Software each a "Larger Work" to which the Software
 * is contributed by such licensors),
 *
 * without restriction, including without limitation the rights to copy, create
 * derivative works of, display, perform, and distribute the Software and make,
 * use, sell, offer for sale, import, export, have made, and have sold the
 * Software and the Larger Work(s), and to sublicense the foregoing rights on
 * either these or other terms.
 *
 * This license is subject to the following condition:
 *
 * The above copyright notice and either this complete permission notice or at a
 * minimum a reference to the UPL must be included in all copies or substantial
 * portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *******************************************************************************/

package com.oracle.samplews;

import java.nio.file.Paths;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;
import java.util.Properties;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.security.auth.login.LoginException;
import javax.sql.DataSource;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

import oracle.iam.platform.OIMClient;
import oracle.iam.platform.entitymgr.vo.SearchCriteria;
import oracle.iam.provisioning.api.ProvisioningConstants;
import oracle.iam.provisioning.api.ProvisioningService;
import oracle.iam.provisioning.vo.Account;
import oracle.iam.provisioning.vo.EntitlementInstance;

/**
 * Sample RESTful web service implementation that extends a user's access
 * following a REST call with the correct access extension UUID.
 * 
 * Must be used in conjunction with the AccessTerminationNotification scheduled
 * task, which will generate the required database entries for server-side
 * validation and send access extension links via email.
 * 
 * @author mgere-oracle
 *
 */
@Path("/v1")
public class ExtendAccessWSv1 {
	private static final Logger logger = Logger.getLogger(ExtendAccessWSv1.class.getName());

	private static final String EXTENSION_SELECT_QUERY = "SELECT EXT_INSTANCE_TYPE, EXT_ACCESS_ID, EXT_INSTANCE_NAME, EXT_ACCESS_END_DATE FROM EXTEND_ACCESS WHERE EXT_UUID = ? AND EXT_USR_KEY = ?";
	private static final String EXTENSION_DELETE_QUERY = "DELETE FROM EXTEND_ACCESS WHERE EXT_UUID = ?";

	private OIMClient oimClient;

	/**
	 * Connect to the remote/local OIM node using an OIMClient object
	 * 
	 * @throws IOException
	 * @throws LoginException
	 */
	private void initOIMClient() throws IOException, LoginException {
		logger.log(Level.FINE, "Initializing OIM Client...");

		Properties prop = new Properties();
		InputStream configurationsFileInput = null;

		String wlDomainDirectory = System.getProperty("domain.home");

		if (wlDomainDirectory == null || wlDomainDirectory.equals("")) {
			throw new LoginException("Domain Home is not defined. Please deploy the service on a WebLogic server.");
		}

		configurationsFileInput = new FileInputStream(
				Paths.get(wlDomainDirectory, "config", "extendaccessws.properties").toString());
		prop.load(configurationsFileInput);

		try {
			configurationsFileInput.close();
		} catch (IOException e) {
			logger.log(Level.WARNING, "Unable to close properties file.");
		}

		String wsOIGNodeURL = prop.getProperty("wsOIGNodeURL");
		logger.log(Level.FINE, "wsOIGNodeURL: {0}", wsOIGNodeURL);
		String wsOIGUser = prop.getProperty("wsOIGUser");
		logger.log(Level.FINE, "wsOIGUser: {0}", wsOIGUser);
		String wsOIGPassword = prop.getProperty("wsOIGPassword");

		if (wsOIGNodeURL == null || wsOIGUser == null || wsOIGPassword == null) {
			throw new LoginException("Invalid configuration file structure.");
		}

		Hashtable<String, String> env = new Hashtable<>();
		env.put(OIMClient.JAVA_NAMING_FACTORY_INITIAL, "weblogic.jndi.WLInitialContextFactory");
		env.put(OIMClient.JAVA_NAMING_PROVIDER_URL, wsOIGNodeURL);
		oimClient = new OIMClient(env);
		oimClient.login(wsOIGUser, wsOIGPassword.toCharArray());

		logger.log(Level.FINE, "OIM Client initialization complete.");
	}

	/**
	 * Initiate a DB connection. Note that the web service needs to be deployed on a
	 * WebLogic node which also has access to the jdbc/operationsDB datasource, also
	 * known as oimOperationsDB. This datasource is typically deployed only on the
	 * OIM and SOA nodes of a WebLogic cluster.
	 * 
	 * @return
	 * @throws IOException
	 * @throws SQLException
	 * @throws NamingException
	 */
	private Connection getDBConnection() throws IOException, SQLException, NamingException, LoginException {
		logger.log(Level.FINE, "Initializing DB Datasource connection...");

		Properties prop = new Properties();
		InputStream configurationsFileInput = null;

		String wlDomainDirectory = System.getProperty("domain.home");

		if (wlDomainDirectory == null || wlDomainDirectory.equals("")) {
			throw new LoginException("Domain Home is not defined. Please deploy the service on a WebLogic server.");
		}

		configurationsFileInput = new FileInputStream(
				Paths.get(wlDomainDirectory, "config", "extendaccessws.properties").toString());
		prop.load(configurationsFileInput);

		try {
			configurationsFileInput.close();
		} catch (IOException e) {
			logger.log(Level.WARNING, "Unable to close properties file.");
		}

		String wsExtendAccessNodeURL = prop.getProperty("wsExtendAccessNodeURL");
		logger.log(Level.FINE, "wsExtendAccessNodeURL: {0}", wsExtendAccessNodeURL);

		if (wsExtendAccessNodeURL == null) {
			throw new LoginException("Invalid configuration file structure.");
		}

		Hashtable<Object, String> env = new Hashtable<>();
		env.put(OIMClient.JAVA_NAMING_FACTORY_INITIAL, "weblogic.jndi.WLInitialContextFactory");
		env.put(OIMClient.JAVA_NAMING_PROVIDER_URL, wsExtendAccessNodeURL);
		Context ctx = new InitialContext(env);
		DataSource ds = (DataSource) ctx.lookup("jdbc/operationsDB");
		Connection connection = ds.getConnection();

		logger.log(Level.FINE, "DB Datasource connection initialization complete.");
		return connection;
	}

	/**
	 * Extend the access for accounts and entitlements based on previously saved DB
	 * entries. The code will validate against a UUID token before access extension.
	 * 
	 * @return
	 */
	@GET
	@Path("/extend/{userId}/{eaUUID}")
	@Produces(MediaType.TEXT_PLAIN)
	public String extendAccess(@PathParam("userId") String userId, @PathParam("eaUUID") String eaUUID) {
		logger.log(Level.INFO, "Extending access for userId: {0}", userId);
		logger.log(Level.FINE, "Extension token: {0}", eaUUID);

		// default return string (in case of unexpected exceptions)
		String restOutput = "Error: Access could not be extended.";

		Connection dbConnection = null;
		PreparedStatement preparedStatement = null;
		ResultSet resultSet = null;

		try {
			// connect to OIM using the oimClient service
			if (oimClient == null) {
				initOIMClient();
			}

			ProvisioningService provisioningService = oimClient.getService(ProvisioningService.class);

			dbConnection = getDBConnection();
			preparedStatement = dbConnection.prepareStatement(EXTENSION_SELECT_QUERY);
			preparedStatement.setString(1, eaUUID);
			preparedStatement.setInt(2, Integer.parseInt(userId));
			resultSet = preparedStatement.executeQuery();

			List<HashMap<String, Object>> resultValuesList = new ArrayList<>();

			while (resultSet.next()) {
				HashMap<String, Object> currentResultValues = new HashMap<>();

				logger.log(Level.FINE, "Processing entry...");
				String resultEntityType = resultSet.getString(1);
				logger.log(Level.FINE, "Entity type: {0}", resultEntityType);
				currentResultValues.put("entityType", resultEntityType);
				String resultItemId = resultSet.getString(2);
				logger.log(Level.WARNING, "Entity ID: {0}", resultItemId);
				currentResultValues.put("itemId", resultItemId);
				String resultEntityName = resultSet.getString(3);
				logger.log(Level.WARNING, "Entity name: {0}", resultEntityName);
				currentResultValues.put("entityName", resultEntityName);
				Date resultEntityEndDate = resultSet.getDate(4);
				logger.log(Level.WARNING, "Entity end date: {0}", resultEntityEndDate);
				currentResultValues.put("entityEndDate", resultEntityEndDate);

				resultValuesList.add(currentResultValues);
			}

			resultSet.close();
			preparedStatement.close();
			dbConnection.close();

			for (HashMap<String, Object> currentResultValues : resultValuesList) {

				String entityType = (String) currentResultValues.get("entityType");
				String itemId = (String) currentResultValues.get("itemId");
				Date entityEndDate = (Date) currentResultValues.get("entityEndDate");

				SearchCriteria accountSearchCriteriaProvisioned = new SearchCriteria(
						ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(), "Provisioned",
						SearchCriteria.Operator.EQUAL);
				SearchCriteria accountSearchCriteriaEnabled = new SearchCriteria(
						ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(), "Enabled",
						SearchCriteria.Operator.EQUAL);
				SearchCriteria accountSearchCriteria = new SearchCriteria(accountSearchCriteriaProvisioned,
						accountSearchCriteriaEnabled, SearchCriteria.Operator.OR);

				List<Account> userApplications = provisioningService.getAccountsProvisionedToUser(userId,
						accountSearchCriteria, null, true);
				logger.log(Level.INFO, "Found {0} accounts for user.", userApplications.size());

				for (Account currentAccount : userApplications) {
					String currentAccountId = currentAccount.getAccountID();
					logger.log(Level.INFO, "Found Account ID: {0}", currentAccountId);

					if (entityType.equals("Application Instance") && currentAccountId.equals(itemId)) {
						logger.log(Level.FINE, "Matched account ID...");

						currentAccount.setValidToDate(entityEndDate);
						// must clear account data in order for modify to work
						// (due to partial child data)
						currentAccount.setAccountData(null);
						provisioningService.modify(currentAccount);
						logger.log(Level.FINE, "Updated user account.");

						logger.log(Level.FINE, "Removing token from the database...");

						dbConnection = getDBConnection();
						PreparedStatement deletePS = dbConnection.prepareStatement(EXTENSION_DELETE_QUERY);
						deletePS.setString(1, eaUUID);
						deletePS.execute();

						deletePS.close();
						dbConnection.close();

						logger.log(Level.INFO, "Account extension complete.");

						restOutput = "Account access has been extended. You can now close this browser window.";
					} else {
						List<EntitlementInstance> applicationEnitlementGrants = currentAccount.getEntitlementGrants();

						for (EntitlementInstance currentEntitlementInstance : applicationEnitlementGrants) {
							String currentEntitlementInstanceKey = String
									.valueOf(currentEntitlementInstance.getEntitlementInstanceKey());
							logger.log(Level.INFO, "Found Entitlement Instance Key: {0}",
									currentEntitlementInstanceKey);

							if (currentEntitlementInstanceKey.equals(itemId)) {
								logger.log(Level.FINE, "Matched entitlement instance key...");

								currentEntitlementInstance.setValidToDate(entityEndDate);
								provisioningService.updateEntitlement(currentEntitlementInstance);
								logger.log(Level.FINE, "Updated user entitlement instance.");

								logger.log(Level.FINE, "Removing token from the database...");
								dbConnection = getDBConnection();
								PreparedStatement deletePS = dbConnection.prepareStatement(EXTENSION_DELETE_QUERY);
								deletePS.setString(1, eaUUID);
								deletePS.execute();

								deletePS.close();
								dbConnection.close();

								logger.log(Level.INFO, "Entitlement extension complete.");

								restOutput = "Entitlement access has been extended. You can now close this browser window.";
							}
						}
					}
				}
			}

			if (resultValuesList.isEmpty()) {
				logger.log(Level.WARNING, "The extension token is no longer present in the DB.");
				restOutput = "Error: Invalid or expired extension token.";
			}

		} catch (Exception e) {
			logger.log(Level.SEVERE, "Severe exception encountered: ", e);
		} finally {
			try {
				if (resultSet != null && !resultSet.isClosed()) {
					resultSet.close();
				}
			} catch (SQLException e) {
				logger.log(Level.WARNING, "Error on RS termination: ", e);
			}
			try {
				if (preparedStatement != null && !preparedStatement.isClosed()) {
					preparedStatement.close();
				}
			} catch (SQLException e) {
				logger.log(Level.WARNING, "Error on PS termination: ", e);
			}
			try {
				if (dbConnection != null && !dbConnection.isClosed()) {
					dbConnection.close();
				}
			} catch (SQLException e) {
				logger.log(Level.WARNING, "Error on DB connection termination: ", e);
			}
		}

		logger.log(Level.INFO, "Token processing complete.");
		return restOutput;
	}
}
