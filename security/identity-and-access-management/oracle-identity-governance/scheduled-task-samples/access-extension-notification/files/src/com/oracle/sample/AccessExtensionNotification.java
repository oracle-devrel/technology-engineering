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

package com.oracle.sample;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.mail.Message;
import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeMessage;
import javax.xml.bind.DatatypeConverter;

import oracle.iam.identity.usermgmt.api.UserManager;
import oracle.iam.identity.usermgmt.api.UserManagerConstants;
import oracle.iam.identity.usermgmt.vo.User;
import oracle.iam.platform.Platform;
import oracle.iam.platform.entitymgr.vo.SearchCriteria;
import oracle.iam.provisioning.api.ProvisioningConstants;
import oracle.iam.provisioning.api.ProvisioningService;
import oracle.iam.provisioning.vo.Account;
import oracle.iam.provisioning.vo.EntitlementInstance;
import oracle.iam.scheduler.exception.SchedulerException;
import oracle.iam.scheduler.vo.TaskSupport;
import oracle.iam.requestactions.vo.RequestactionsConstants;

/**
 * Sample scheduled task implementation that sends notification emails to users
 * prior to user account/entitlement expiration or access termination.
 * 
 * It uses JavaMail APIs and direct database queries and does not need any
 * custom notification handlers in order to function.
 * 
 * @author mgere-oracle
 * 
 */
public class AccessExtensionNotification extends TaskSupport {

	private static final Logger logger = Logger.getLogger(AccessExtensionNotification.class.getName());

	private static final String EXTENSION_COUNT_QUERY = "SELECT COUNT(*) FROM EXTEND_ACCESS WHERE EXT_USR_KEY = ? AND EXT_ACCESS_ID = ? AND EXT_INSTANCE_TYPE = ?";
	private static final String EXTENSION_INSERT_QUERY = "INSERT INTO EXTEND_ACCESS VALUES (?, ?, ?, ?, ?, ?, ?)";
	private static final String TEMPLATE_SELECT_QUERY = "SELECT NOTIFICATIONTEMPLATE.ID, LONGMESSAGE, SUBJECT "
			+ "FROM LOCALTEMPLATE, NOTIFICATIONTEMPLATE WHERE LOCALTEMPLATE.TEMPLATEID = NOTIFICATIONTEMPLATE.ID AND TEMPLATENAME = ?";

	private static final String FROM_EMAIL_ADDRESS = "donotreply@example.com";

	private Date currentDate;
	private Integer daysBeforeExpiration;
	private Integer extensionDays;
	private String extensionLinkText;
	private String extensionWSBaseEndpoint;

	private StringBuilder extensionItemsText;

	@Override
	public void execute(HashMap arg0) throws Exception {
		logger.log(Level.INFO, "The scheduled task run has started.");

		if (arg0 == null) {
			// arg0 will never be null if a valid scheduled task definition file is used
			throw new SchedulerException("Scheduled task definition is incorrect. Aborting run.");
		}

		// retrieve parameters from the scheduled task
		daysBeforeExpiration = Integer.parseInt((String) arg0.get("Days Before Expiration"));
		extensionDays = Integer.parseInt((String) arg0.get("Extension Days"));
		extensionLinkText = (String) arg0.get("Extension Link Text");
		extensionWSBaseEndpoint = (String) arg0.get("REST WS Endpoint URL");

		UserManager userManager = Platform.getService(UserManager.class);
		ProvisioningService provisioningService = Platform.getService(ProvisioningService.class);

		currentDate = Calendar.getInstance().getTime();
		logger.log(Level.FINE, "Current date: {0}", currentDate);

		// construct a criteria for all active and disabled users in the system
		SearchCriteria userSearchCriteriaActive = new SearchCriteria(UserManagerConstants.AttributeName.STATUS.getId(),
				UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId(), SearchCriteria.Operator.EQUAL);
		SearchCriteria userSearchCriteriaDisabled = new SearchCriteria(
				UserManagerConstants.AttributeName.STATUS.getId(),
				UserManagerConstants.AttributeValues.USER_STATUS_DISABLED.getId(), SearchCriteria.Operator.EQUAL);
		SearchCriteria userSearchCriteria = new SearchCriteria(userSearchCriteriaActive, userSearchCriteriaDisabled,
				SearchCriteria.Operator.OR);
		Set<String> retAttrs = new HashSet<>();

		List<User> returnedUserList = userManager.search(userSearchCriteria, retAttrs, null);

		for (User currentUser : returnedUserList) {
			try {
				String userLogin = currentUser.getLogin();
				logger.log(Level.INFO, "Processing user: {0}", userLogin);
				String userKey = currentUser.getId();
				logger.log(Level.FINE, "User key: {0}", userKey);

				Boolean sendEmail = false;

				String terminationEmailAddress = null;
				String emailSubject = null;
				String emailBody = null;
				HashMap<String, String> templateParams = null;
				extensionItemsText = new StringBuilder();

				// construct a criteria for all provisioned and enabled user accounts
				SearchCriteria accountSearchCriteriaProvisioned = new SearchCriteria(
						ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(),
						RequestactionsConstants.OBJECT_STATUS_PROVISIONED, SearchCriteria.Operator.EQUAL);
				SearchCriteria accountSearchCriteriaEnabled = new SearchCriteria(
						ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(),
						RequestactionsConstants.OBJECT_STATUS_ENABLED, SearchCriteria.Operator.EQUAL);
				SearchCriteria accountSearchCriteria = new SearchCriteria(accountSearchCriteriaProvisioned,
						accountSearchCriteriaEnabled, SearchCriteria.Operator.OR);

				List<Account> userAccounts = provisioningService.getAccountsProvisionedToUser(userKey,
						accountSearchCriteria, null, true);
				logger.log(Level.FINE, "Found {0} accounts for the user.", userAccounts.size());
				sendEmail = processAccounts(userKey, userAccounts);

				if (Boolean.TRUE.equals(sendEmail)) {
					// retrieve email parameters from the scheduled task
					String emailTemplateName = (String) arg0.get("Email Template Name");
					String smtpServerHost = (String) arg0.get("SMTP Mail Server Hostname");
					Boolean smtpServerTLS = (Boolean) arg0.get("SMTP Mail Server TLS");
					String smtpServerPort = (String) arg0.get("SMTP Mail Server Port");

					// setup the SMTP mailing server parameters
					Properties props = new Properties();
					props.put("mail.smtp.host", smtpServerHost);
					props.put("mail.transport.protocol", "smtp");
					props.put("mail.smtp.starttls.enable", smtpServerTLS.toString()); // "true" or "false"
					props.put("mail.smtp.port", smtpServerPort);
					Session session = Session.getDefaultInstance(props);

					logger.log(Level.INFO, "Constructing notification email...");

					templateParams = new HashMap<>();
					templateParams.put("$display_name", currentUser.getDisplayName());
					templateParams.put("$days", daysBeforeExpiration.toString());
					templateParams.put("$expiring_items", extensionItemsText.toString());
					HashMap<String, String> subjectAndBody = dynamicTemplateFill(templateParams, emailTemplateName);
					emailSubject = subjectAndBody.get("subject");
					logger.log(Level.FINE, "Filled in email subject: {0}", emailSubject);
					emailBody = subjectAndBody.get("body");
					logger.log(Level.FINE, "Filled in email body: {0}", emailBody);

					terminationEmailAddress = currentUser.getEmail();

					if (terminationEmailAddress == null
							|| (terminationEmailAddress != null && terminationEmailAddress.equals(""))) {
						throw new MessagingException("The user doesn't have valid email address.");
					}

					logger.log(Level.FINE, "Send to email address: {0}", terminationEmailAddress);

					logger.log(Level.INFO, "Sending notification email...");

					InternetAddress fromAddress = new InternetAddress(FROM_EMAIL_ADDRESS);
					InternetAddress toAddress = new InternetAddress(terminationEmailAddress);

					Message message = new MimeMessage(session);
					message.setFrom(fromAddress);
					message.setRecipient(Message.RecipientType.TO, toAddress);
					message.setSubject(emailSubject);
					message.setContent(emailBody, "text/html; charset=utf-8");
					message.saveChanges();
					Transport.send(message);

					logger.log(Level.INFO, "Notification email was sent successfully.");
				}
			} catch (MessagingException e) {
				logger.log(Level.WARNING, "Sending the email failed with: ", e);
			} catch (Exception e) {
				logger.log(Level.WARNING, "User processing failed with: ", e);
			}
		}

		logger.log(Level.INFO, "The scheduled task run has finished.");
	}

	private Boolean processAccounts(String userKey, List<Account> userApplications) throws SQLException, SchedulerException {
		if (userKey == null || userKey.equals("")) {
			throw new SchedulerException("userKey must be specified.");
		}
		if (userApplications == null) {
			throw new SchedulerException("userApplications can not be null.");
		}
		
		Boolean sendEmailAccounts = false;
		Boolean sendEmailEntitlements = false;

		Connection dbConnection = null;
		PreparedStatement preparedStatement = null;
		ResultSet resultSet = null;

		for (Account currentAccount : userApplications) {
			try {
				String currentAccountId = currentAccount.getAccountID();
				logger.log(Level.INFO, "Processing Account ID: {0}", currentAccountId);
				String currentAccountAppInstID = String
						.valueOf(currentAccount.getAppInstance().getApplicationInstanceKey());
				logger.log(Level.FINE, "Account Application Instance ID: {0}", currentAccountAppInstID);
				String currentAccountAppInstName = currentAccount.getAppInstance().getDisplayName();
				logger.log(Level.FINE, "Account Application Instance name: {0}", currentAccountAppInstName);

				Date currentAccountExpirationDate = currentAccount.getValidToDate();
				logger.log(Level.FINE, "Account valid up to: {0}", currentAccountExpirationDate);

				// process user accounts
				if (currentAccountExpirationDate != null) {
					// calculate the difference in days between the expiration and current date
					Long dayDiff = TimeUnit.DAYS.convert(currentAccountExpirationDate.getTime() - currentDate.getTime(),
							TimeUnit.MILLISECONDS);
					logger.log(Level.FINE, "Time diff is: {0}", dayDiff);

					// the email will be sent on the x-th day prior to expiration (diff will be x-1)
					if (dayDiff >= 0 && dayDiff + 1 == daysBeforeExpiration) {
						logger.log(Level.INFO, "The account is in the expiration notification window.");

						// check for an existing token for the same access rights
						dbConnection = Platform.getOperationalDS().getConnection();
						preparedStatement = dbConnection.prepareStatement(EXTENSION_COUNT_QUERY);
						preparedStatement.setInt(1, Integer.parseInt(userKey));
						preparedStatement.setInt(2, Integer.parseInt(currentAccountId));
						preparedStatement.setString(3, "Application Instance");
						resultSet = preparedStatement.executeQuery();

						Integer existingEntryCount = 0;
						while (resultSet.next()) {
							existingEntryCount = resultSet.getInt(1);
							logger.log(Level.FINE, "Existing entry count: {0}", existingEntryCount);
						}

						resultSet.close();
						preparedStatement.close();
						dbConnection.close();

						if (existingEntryCount != 0) {
							logger.log(Level.WARNING, "Access extension details are already saved.");
						} else {
							sendEmailAccounts = true;

							String uniqueIdentifier = UUID.randomUUID().toString();
							logger.log(Level.FINE, "Random UUID: {0}", uniqueIdentifier);
							String htmlIdentifier = DatatypeConverter.printBase64Binary(uniqueIdentifier.getBytes());
							logger.log(Level.FINE, "HTML identifier: {0}", htmlIdentifier);

							extensionItemsText.append("<b>" + currentAccountAppInstName + "</b> - <a href=\""
									+ extensionWSBaseEndpoint + "/v1/extend/" + userKey + "/" + htmlIdentifier + "\">"
									+ extensionLinkText + "</a><br>");

							Calendar c = Calendar.getInstance();
							c.setTime(currentAccountExpirationDate);
							c.add(Calendar.DATE, extensionDays);
							Date newExpiryDate = c.getTime();
							logger.log(Level.FINE, "New expiry date is: {0}", newExpiryDate);

							logger.log(Level.FINE, "Preparing to save account access extention details...");
							dbConnection = Platform.getOperationalDS().getConnection();
							preparedStatement = dbConnection.prepareStatement(EXTENSION_INSERT_QUERY);
							// save the application extension details in the DB
							preparedStatement.setString(1, htmlIdentifier);
							preparedStatement.setInt(2, Integer.parseInt(userKey));
							preparedStatement.setInt(3, Integer.parseInt(currentAccountId));
							preparedStatement.setInt(4, Integer.parseInt(currentAccountAppInstID));
							preparedStatement.setString(5, "Application Instance");
							preparedStatement.setString(6, currentAccountAppInstName);
							java.sql.Date sqlDate = new java.sql.Date(newExpiryDate.getTime());
							preparedStatement.setDate(7, sqlDate);
							preparedStatement.execute();
							logger.log(Level.FINE, "Account access extension details saved.");

							preparedStatement.close();
							dbConnection.close();
						}
					}

					sendEmailEntitlements = processEntitlements(userKey, currentAccount);
				} else {
					logger.log(Level.FINE, "Processed item does not have a valid end date. Skipping.");
				}
			} catch (Exception e) {
				logger.log(Level.WARNING, "Account processing failed with: ", e);
			} finally {
				if (resultSet != null && !resultSet.isClosed()) {
					resultSet.close();
				}
				if (preparedStatement != null && !preparedStatement.isClosed()) {
					preparedStatement.close();
				}
				if (dbConnection != null && !dbConnection.isClosed()) {
					dbConnection.close();
				}
			}
		}

		return (sendEmailAccounts || sendEmailEntitlements);
	}

	private Boolean processEntitlements(String userKey, Account currentAccount) throws SQLException, SchedulerException {
		if (userKey == null || userKey.equals("")) {
			throw new SchedulerException("userKey must be specified.");
		}
		if (currentAccount == null) {
			throw new SchedulerException("currentAccount can not be null.");
		}
		
		Boolean sendEmailEntitlements = false;

		Connection dbConnection = null;
		PreparedStatement preparedStatement = null;
		ResultSet resultSet = null;

		List<EntitlementInstance> linkedEntitlements = currentAccount.getEntitlementGrants();

		for (EntitlementInstance currentEntitlementInstance : linkedEntitlements) {
			try {
				String currentEntitlementInstanceKey = String
						.valueOf(currentEntitlementInstance.getEntitlementInstanceKey());
				logger.log(Level.INFO, "Processing Entitlement Instance: {0}", currentEntitlementInstanceKey);
				String currentEntitlementKey = String
						.valueOf(currentEntitlementInstance.getEntitlement().getEntitlementKey());
				logger.log(Level.FINE, "Entitlement Key: {0}", currentEntitlementKey);
				String currentEntitlementName = currentEntitlementInstance.getEntitlement().getDisplayName();
				logger.log(Level.FINE, "Entitlement Display Name: {0}", currentEntitlementName);

				Date currentEntitlementExpirationDate = currentEntitlementInstance.getValidToDate();
				logger.log(Level.FINE, "Entitlement Instance valid up to: {0}", currentEntitlementExpirationDate);

				// process entitlements
				if (currentEntitlementExpirationDate != null) {
					// calculate the difference in days between the expiration and current date
					Long dayDiff = TimeUnit.DAYS.convert(
							currentEntitlementExpirationDate.getTime() - currentDate.getTime(), TimeUnit.MILLISECONDS);
					logger.log(Level.FINE, "Time diff is: {0}", dayDiff);

					// the email will be sent on the x-th day prior to expiration (diff will be x-1)
					if (dayDiff >= 0 && dayDiff + 1 == daysBeforeExpiration) {
						logger.log(Level.INFO, "The entitlement is in the expiration notification window.");

						// check for an existing token for the same access rights
						dbConnection = Platform.getOperationalDS().getConnection();
						preparedStatement = dbConnection.prepareStatement(EXTENSION_COUNT_QUERY);
						preparedStatement.setInt(1, Integer.parseInt(userKey));
						preparedStatement.setInt(2, Integer.parseInt(currentEntitlementInstanceKey));
						preparedStatement.setString(3, "Entitlement");
						resultSet = preparedStatement.executeQuery();

						Integer existingEntryCount = 0;
						while (resultSet.next()) {
							existingEntryCount = resultSet.getInt(1);
							logger.log(Level.FINE, "Existing entry count: {0}", existingEntryCount);
						}

						resultSet.close();
						preparedStatement.close();
						dbConnection.close();

						if (existingEntryCount != 0) {
							logger.log(Level.WARNING, "Access extension details are already saved.");
						} else {
							sendEmailEntitlements = true;

							String uniqueIdentifier = UUID.randomUUID().toString();
							logger.log(Level.FINE, "Random UUID: {0}", uniqueIdentifier);
							String htmlIdentifier = DatatypeConverter.printBase64Binary(uniqueIdentifier.getBytes());
							logger.log(Level.FINE, "HTML identifier: {0}", htmlIdentifier);

							extensionItemsText.append("<i>" + currentEntitlementName + "</i> - <a href=\""
									+ extensionWSBaseEndpoint + "/v1/extend/" + userKey + "/" + htmlIdentifier + "\">"
									+ extensionLinkText + "</a><br>");

							Calendar c = Calendar.getInstance();
							c.setTime(currentEntitlementExpirationDate);
							c.add(Calendar.DATE, extensionDays);
							Date newExpiryDate = c.getTime();
							logger.log(Level.FINE, "New expiry date is: {0}", newExpiryDate);

							// save the entitlement extension details in the DB
							logger.log(Level.FINE, "Preparing to save entitlement access extention details...");
							dbConnection = Platform.getOperationalDS().getConnection();
							preparedStatement = dbConnection.prepareStatement(EXTENSION_INSERT_QUERY);
							preparedStatement.setString(1, htmlIdentifier);
							preparedStatement.setInt(2, Integer.parseInt(userKey));
							preparedStatement.setInt(3, Integer.parseInt(currentEntitlementInstanceKey));
							preparedStatement.setInt(4, Integer.parseInt(currentEntitlementKey));
							preparedStatement.setString(5, "Entitlement");
							preparedStatement.setString(6, currentEntitlementName);
							java.sql.Date sqlDate = new java.sql.Date(newExpiryDate.getTime());
							preparedStatement.setDate(7, sqlDate);
							preparedStatement.execute();
							logger.log(Level.FINE, "Entitlement access extension details saved.");

							preparedStatement.close();
							dbConnection.close();
						}
					}
				} else {
					logger.log(Level.FINE, "Processed item does not have a valid end date. Skipping.");
				}
			} catch (Exception e) {
				logger.log(Level.WARNING, "Entitlement processing failed with: ", e);
			} finally {
				if (resultSet != null && !resultSet.isClosed()) {
					resultSet.close();
				}
				if (preparedStatement != null && !preparedStatement.isClosed()) {
					preparedStatement.close();
				}
				if (dbConnection != null && !dbConnection.isClosed()) {
					dbConnection.close();
				}
			}
		}

		return sendEmailEntitlements;
	}

	/**
	 * Method used to dynamically replace the placeholders specified in the email
	 * template with actual values
	 * 
	 * @param attrMap
	 * @param templateName
	 * @return
	 * @throws SQLException
	 * @throws Exception
	 */
	private HashMap<String, String> dynamicTemplateFill(HashMap<String, String> attrMap, String templateName)
			throws SQLException, SchedulerException {
		if (templateName == null || templateName.equals("")) {
			throw new SchedulerException("templateName must be specified.");
		}
		if (attrMap == null || attrMap.size() == 0) {
			throw new SchedulerException("attrMap must contain at least one item.");
		}
		
		HashMap<String, String> templateMap = new HashMap<>();

		Connection oimConn = null;
		PreparedStatement templatePS = null;
		ResultSet templateRS = null;

		String currentTemplateID = null;
		String body = null;
		String subject = null;

		try {
			oimConn = Platform.getOperationalDS().getConnection();
			templatePS = oimConn.prepareStatement(TEMPLATE_SELECT_QUERY);
			templatePS.setString(1, templateName);
			logger.log(Level.FINE, "Fetching existing template...");
			templateRS = templatePS.executeQuery();

			// should not find more than one entry, as the template name is unique
			while (templateRS.next()) {
				currentTemplateID = templateRS.getString(1);
				body = templateRS.getString(2);
				subject = templateRS.getString(3);

				templateMap.put("templateID", currentTemplateID);

				Set<String> keyMap = attrMap.keySet();

				for (String currentKeyValue : keyMap) {
					logger.log(Level.FINE, "Processing placeholder: {0}", currentKeyValue);
					String currentValue = attrMap.get(currentKeyValue);
					logger.log(Level.FINE, "Replacing with value: {0}", currentValue);

					body = body.replace(currentKeyValue, currentValue);
					subject = subject.replace(currentKeyValue, currentValue);
				}

				templateMap.put("body", body);
				templateMap.put("subject", subject);
			}
		} catch (Exception e) {
			logger.log(Level.WARNING, "Exception encountered: ", e);
			throw new SchedulerException("Email template fill has failed.");
		} finally {
			if (templateRS != null && !templateRS.isClosed()) {
				templateRS.close();
			}
			if (templatePS != null && !templatePS.isClosed()) {
				templatePS.close();
			}
			if (oimConn != null && !oimConn.isClosed()) {
				oimConn.close();
			}
		}

		return templateMap;
	}

	@Override
	public HashMap getAttributes() {
		return new HashMap<>();
	}

	@Override
	public void setAttributes() {
	}
}
