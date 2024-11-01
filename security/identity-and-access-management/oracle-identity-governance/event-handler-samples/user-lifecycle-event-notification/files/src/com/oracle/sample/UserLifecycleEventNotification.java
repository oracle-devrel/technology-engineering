/*******************************************************************************
 * Copyright (c) 2024 Oracle and/or its affiliates. All rights reserved. DO NOT
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

import java.io.Serializable;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.thortech.xl.dataaccess.tcDataProvider;
import com.thortech.xl.dataobj.util.XLDatabase;
import com.thortech.xl.dataobj.util.tcEmailNotificationUtil;

import Thor.API.tcResultSet;
import Thor.API.Exceptions.tcAPIException;
import Thor.API.Exceptions.tcColumnNotFoundException;
import Thor.API.Exceptions.tcInvalidLookupException;
import Thor.API.Operations.tcLookupOperationsIntf;
import oracle.iam.identity.exception.UserSearchException;
import oracle.iam.identity.usermgmt.api.UserManager;
import oracle.iam.identity.usermgmt.api.UserManagerConstants;
import oracle.iam.identity.usermgmt.vo.User;
import oracle.iam.platform.Platform;
import oracle.iam.platform.authz.exception.AccessDeniedException;
import oracle.iam.platform.context.ContextAware;
import oracle.iam.platform.entitymgr.vo.SearchCriteria;
import oracle.iam.platform.kernel.OrchestrationEngine;
import oracle.iam.platform.kernel.spi.PostProcessHandler;
import oracle.iam.platform.kernel.vo.AbstractGenericOrchestration;
import oracle.iam.platform.kernel.vo.BulkEventResult;
import oracle.iam.platform.kernel.vo.BulkOrchestration;
import oracle.iam.platform.kernel.vo.EventResult;
import oracle.iam.platform.kernel.vo.Orchestration;

public class UserLifecycleEventNotification implements PostProcessHandler {
	private static final Logger logger = Logger.getLogger(UserLifecycleEventNotification.class.getName());

	private static final String ORCHESTRATION_CREATE_EVENT = "CREATE";

	private static final String LOOKUP_NAME = "Lookup.Sample.LifecycleNotification";
	private static final String LOOKUP_RECIPIENT_EMAILS = "Recipient Emails";
	private static final String LOOKUP_RECIPIENT_SELF = "Self Recipient";
	private static final String LOOKUP_USER_STATE = "User State";
	private static final String LOOKUP_TEMPLATE_NAME = "Template Name";

	private static final String LOOKUP_FIELD_CODE = "Lookup Definition.Lookup Code Information.Code Key";
	private static final String LOOKUP_FIELD_DECODE = "Lookup Definition.Lookup Code Information.Decode";

	private static final String TEMPLATE_SELECT_QUERY = "SELECT NOTIFICATIONTEMPLATE.ID, LONGMESSAGE, SUBJECT "
			+ "FROM LOCALTEMPLATE, NOTIFICATIONTEMPLATE WHERE LOCALTEMPLATE.TEMPLATEID = NOTIFICATIONTEMPLATE.ID AND TEMPLATENAME = ?";

	private static final String FROM_EMAIL_ADDRESS = "donotreply@example.com";

	@Override
	public EventResult execute(long arg0, long arg1, Orchestration arg2) {
		logger.log(Level.INFO, "Event handler execution has started.");

		EventResult eventNotificationResult = new EventResult();

		if (arg2 == null) {
			// arg2 will never be null if execute is called from an OIM event handler
			logger.log(Level.SEVERE, "Invalid orchestration payload.");
			eventNotificationResult.setFailureReason(new EventHandlerException("Invalid orchestration payload."));
		}

		else {
			try {
				HashMap<String, String> lookupValueMap = getLookupValues(LOOKUP_NAME);

				UserManager userManager = Platform.getService(UserManager.class);
				User currentUser = null;

				String operation = arg2.getOperation();
				logger.log(Level.INFO, "Orchestration event: {0}", operation);

				// in the case of CREATE events, the user display name will be included
				// in the event handler parameters (arg2)
				HashMap<String, Serializable> contextParams = arg2.getParameters();
				String userDisplayName = getParamaterValue(contextParams,
						UserManagerConstants.AttributeName.DISPLAYNAME.getId());

				// for other event types we will need to manually retrieve the user display name
				if (userDisplayName == null) {
					String userKey = getUserKey(arg0, arg2);
					logger.log(Level.FINE, "User Key: {0}", userKey);

					Set<String> retAttrs = new HashSet<>();
					SearchCriteria searchCriteria = new SearchCriteria(
							UserManagerConstants.AttributeName.USER_KEY.getId(), userKey,
							SearchCriteria.Operator.EQUAL);

					try {
						currentUser = userManager.search(searchCriteria, retAttrs, null).get(0);
					} catch (UserSearchException | AccessDeniedException | IndexOutOfBoundsException e) {
						logger.log(Level.SEVERE, "Unable to retrieve user data.");
						throw e;
					}

					userDisplayName = currentUser.getDisplayName();
				}

				logger.log(Level.INFO, "User DisplayName: {0}", userDisplayName);

				HashMap<String, String> templateParams = new HashMap<>();
				templateParams.put("$display_name", userDisplayName);
				String userState = lookupValueMap.get(LOOKUP_USER_STATE);
				templateParams.put("$user_state", userState);
				HashMap<String, String> subjectAndBody = dynamicTemplateFill(templateParams,
						lookupValueMap.get(LOOKUP_TEMPLATE_NAME));

				tcDataProvider dbProvider = XLDatabase.getInstance().getDataBase();
				tcEmailNotificationUtil emailNotificationUtil = new tcEmailNotificationUtil(dbProvider);
				emailNotificationUtil.setFromAddress(FROM_EMAIL_ADDRESS);

				String emailSubject = subjectAndBody.get("subject");
				logger.log(Level.INFO, "Filled in email subject is: {0}", emailSubject);
				String emailBody = subjectAndBody.get("body");
				logger.log(Level.INFO, "Filled in email body is: {0}", emailBody);

				emailNotificationUtil.setSubject(emailSubject);
				emailNotificationUtil.setBody(emailBody);

				logger.log(Level.INFO, "Sending notifications.");
				try {
					String[] recepientEmails = lookupValueMap.get(LOOKUP_RECIPIENT_EMAILS).split(",");

					// notify the user if the option is enabled in the configuration lookup
					if (currentUser != null && lookupValueMap.get(LOOKUP_RECIPIENT_SELF).equalsIgnoreCase("TRUE")) {
						String userEmail = currentUser.getEmail();
						logger.log(Level.INFO, "Sending email to user: {0}", userEmail);
						emailNotificationUtil.sendEmail(userEmail);
					}

					for (String recepientEmail : recepientEmails) {
						logger.log(Level.INFO, "Sending email to: {0}", recepientEmail);
						emailNotificationUtil.sendEmail(recepientEmail);
					}
				} catch (Exception e) {
					logger.log(Level.SEVERE, "Email dispatch has failed.");
					throw e;
				}
				logger.log(Level.INFO, "Notifications have been sent successfully");

			} catch (Exception e) {
				logger.log(Level.SEVERE, "User lifecycle notification has failed with: ", e);
				eventNotificationResult.setFailureReason(e);
			}
		}

		logger.log(Level.INFO, "Event handler execution has stopped");
		return eventNotificationResult;
	}

	/**
	 * Generic method used to retrieve lookup values based on a lookup name and
	 * return a HashMap of the code and decode values.
	 * 
	 * @param LookupName
	 * @return
	 */
	private HashMap<String, String> getLookupValues(String lookupName) {
		logger.log(Level.FINE, "Retrieving lookup values from: {0}", lookupName);

		HashMap<String, String> lookupHashValues = new HashMap<>();
		tcLookupOperationsIntf lookupIntf = Platform.getService(tcLookupOperationsIntf.class);

		try {
			tcResultSet lookupValues = lookupIntf.getLookupValues(lookupName);

			int rowCount = lookupValues.getTotalRowCount();

			if (rowCount > 0) {
				String lookupCodeValue;
				String lookupDecodeValue;

				for (int row = 0; row < rowCount; row++) {
					lookupValues.goToRow(row);
					lookupCodeValue = lookupValues.getStringValue(LOOKUP_FIELD_CODE);
					lookupDecodeValue = lookupValues.getStringValue(LOOKUP_FIELD_DECODE);
					lookupHashValues.put(lookupCodeValue, lookupDecodeValue);
					logger.log(Level.FINE, "Parsed {0}: {1}", new Object[] { lookupCodeValue, lookupDecodeValue });
				}
			}
		} catch (tcAPIException | tcInvalidLookupException | tcColumnNotFoundException e) {
			logger.log(Level.SEVERE, "Unable to retrive lookup values.");
		}

		logger.log(Level.FINE, "Return hashmap size is: {0}", lookupHashValues.size());
		return lookupHashValues;
	}

	/**
	 * Method used to dynamically replace the placeholders specified in the email
	 * template with actual values.
	 * 
	 * @param attrMap
	 * @param templateName
	 * @return
	 * @throws SQLException
	 * @throws EventHandlerException
	 */
	private HashMap<String, String> dynamicTemplateFill(HashMap<String, String> attrMap, String templateName)
			throws SQLException, EventHandlerException {
		if (templateName == null || templateName.equals("")) {
			throw new EventHandlerException("templateName must be specified.");
		}
		if (attrMap == null || attrMap.size() == 0) {
			throw new EventHandlerException("attrMap must contain at least one item.");
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
			throw new EventHandlerException("Email template fill has failed.");
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

	/**
	 * Retrieve ContextAware values of parameters from an event handler
	 * orchestration event, based on a desired key.
	 * 
	 * @param parameters
	 * @param key
	 * @return
	 */
	private String getParamaterValue(HashMap<String, Serializable> parameters, String key) {
		if (parameters.containsKey(key)) {
			return (parameters.get(key) instanceof ContextAware)
					? (String) ((ContextAware) parameters.get(key)).getObjectValue()
					: (String) parameters.get(key);
		} else {
			return null;
		}
	}

	/**
	 * Return the affected user key from an orchestration event.
	 * 
	 * @param processID
	 * @param orchestration
	 * @return
	 */
	private String getUserKey(long processID, Orchestration orchestration) {
		String userKey;

		if (!orchestration.getOperation().equals(ORCHESTRATION_CREATE_EVENT)) {
			userKey = orchestration.getTarget().getEntityId();
		} else {
			OrchestrationEngine orchEngine = Platform.getService(OrchestrationEngine.class);
			userKey = (String) orchEngine.getActionResult(processID);
		}

		return userKey;
	}

	@Override
	public void initialize(HashMap<String, String> arg0) {
	}

	@Override
	public void compensate(long arg0, long arg1, AbstractGenericOrchestration arg2) {
	}

	@Override
	public boolean cancel(long arg0, long arg1, AbstractGenericOrchestration arg2) {
		return false;
	}

	@Override
	public BulkEventResult execute(long arg0, long arg1, BulkOrchestration arg2) {
		BulkEventResult bulkEventNotificationResult = new BulkEventResult();

		logger.log(Level.WARNING, "The event handler does not send notifications for bulk events.");

		return bulkEventNotificationResult;
	}
}